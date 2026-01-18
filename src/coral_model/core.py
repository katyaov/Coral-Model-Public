import numpy as np
import pandas as pd
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import asdict
import random

from .parameters import CoralConstants, CoralParameters
from .dynamics import CoralDynamics
from .utils import CoralUtils

class CoralModel:
    """
    Main class for the Coral Growth/Decline logic.
    Manages state (population, cover) and executes time steps.
    """
    
    def __init__(self, params: Optional[CoralParameters] = None, constants: Optional[CoralConstants] = None):
        if params is None:
            self.params = CoralParameters()
        else:
            self.params = params
            
        if constants is None:
            self.constants = CoralConstants()
        else:
            self.constants = constants
            
        # State
        self.year = 0
        self.population: np.ndarray = np.zeros((3, self.constants.MAX_BIN_ID), dtype=int)
        
        # Derived State
        self.dhw_counter = 0
        self.available_substrate = 0.0
        self.total_cover = 0.0
        self.cover_breakdown = {}
        
        # Benthic State
        self.benthic_cover = {}
        self.rugosity = 0.0
        
        # History
        self.history_population: List[np.ndarray] = []
        self.history_cover: List[Dict[str, float]] = []
        self.history_benthic: List[Dict[str, float]] = []
        self.history_rugosity: List[float] = []
        
        # Initialization
        self.initialize()
        
    def initialize(self):
        """Set initial state based on parameters."""
        self.year = 0
        self.dhw_counter = 0
        
        # Initialize Benthic Cover
        self.benthic_cover = {
            "hard_substrate": self.params.hard_substrate_cover,
            "dead_coral": self.params.dead_coral_cover,
            "CCA": self.params.cca_cover,
            "turfing_algae": self.params.turfing_algae_cover,
            "macro_algae": self.params.macro_algae_cover,
            "rubble": self.params.rubble_cover,
            "sediment": self.params.sediment_cover
        }
        
        # Update Total Benthic
        self.benthic_cover['total'] = sum(self.benthic_cover.values())
        
        # Initialize Rugosity
        self.rugosity = self.params.initial_rugosity
        
        # Initialize Population
        # Use simple estimation from utils
        self.population = CoralUtils.estimate_initial_population(self.params, self.constants)
        
        # Calculate initial cover to sync
        self._update_derived_state()
        
        # Record initial state
        self._record_history()
        
    def _update_derived_state(self):
        """Update metrics like Total Cover and Available Substrate."""
        # Calculate Area for each type
        area_m2 = CoralUtils.population_to_area_m2(self.population, self.constants)
        total_type_area_m2 = area_m2.sum(axis=1) # (3,)
        
        reef_area = self.params.reef_area
        type_cover_pct = (total_type_area_m2 / reef_area) * 100.0
        
        self.cover_breakdown = {
            'Branching': type_cover_pct[0],
            'Foliose': type_cover_pct[1],
            'Other': type_cover_pct[2]
        }
        
        self.total_cover = sum(self.cover_breakdown.values())
        
        # Available Substrate calculation
        unavailable = (self.benthic_cover['macro_algae'] + 
                       self.benthic_cover['rubble'] + 
                       self.benthic_cover['sediment'])
        
        self.available_substrate = 100.0 - unavailable - self.total_cover
        if self.available_substrate < 0:
            self.available_substrate = 0.0
            
    def _update_benthic_dynamics(self, old_cover: Dict[str, float], is_bleaching: bool, is_cyclone: bool):
        """
        Update Benthic Cover components based on changes in Coral Cover.
        Logic ported from legacy/utils.py.
        """
        # Calculate changes
        change_branching = self.cover_breakdown['Branching'] - old_cover['Branching']
        change_foliose = self.cover_breakdown['Foliose'] - old_cover['Foliose']
        change_other = self.cover_breakdown['Other'] - old_cover['Other']
        
        bc = self.benthic_cover
        
        # Helper to simplify repeated logic
        def apply_increase(change, substrate_pool):
            """When coral increases, it consumes substrate."""
            if change <= 0: return
            
            w_hs, w_dc, w_tf = CoralUtils.split_w(
                bc['hard_substrate'], 
                bc['dead_coral'], 
                bc['turfing_algae'], 
                substrate_pool, 
                change
            )
            bc['hard_substrate'] -= w_hs
            bc['dead_coral'] -= w_dc
            bc['turfing_algae'] -= w_tf
            
        substrate_pool = bc['hard_substrate'] + bc['dead_coral'] + bc['turfing_algae']
        if substrate_pool <= 0: substrate_pool = 0.0001
        
        if is_cyclone:
            if change_branching < 0: bc['rubble'] += abs(change_branching)
            else: apply_increase(change_branching, substrate_pool)
                
            if change_foliose < 0: bc['rubble'] += abs(change_foliose)
            else: apply_increase(change_foliose, substrate_pool)
            
            if change_other < 0:
                bc['rubble'] += abs(change_other)/4
                bc['dead_coral'] += abs(change_other)/2
                bc['turfing_algae'] += abs(change_other)/4
            else: apply_increase(change_other, substrate_pool)
            
        elif is_bleaching:
            if change_branching < 0: bc['rubble'] += abs(change_branching)
            else: apply_increase(change_branching, substrate_pool)
            
            if change_foliose < 0:
                bc['dead_coral'] += abs(change_foliose)/3
                bc['turfing_algae'] += abs(change_foliose)/3
                bc['macro_algae'] += abs(change_foliose)/3
            else: apply_increase(change_foliose, substrate_pool)
            
            if change_other < 0:
                 bc['dead_coral'] += abs(change_other)/3
                 bc['turfing_algae'] += abs(change_other)/3
                 bc['macro_algae'] += abs(change_other)/3
            else: apply_increase(change_other, substrate_pool)
            
        else:
            if change_branching > 0: apply_increase(change_branching, substrate_pool)
            else: bc['dead_coral'] += abs(change_branching)
                
            if change_foliose > 0: apply_increase(change_foliose, substrate_pool)
            else: bc['dead_coral'] += abs(change_foliose)
                
            if change_other > 0: apply_increase(change_other, substrate_pool)
            else: bc['dead_coral'] += abs(change_other)
            
        # Annual Rubble -> Dead Coral Conversion (Legacy: 1/6 per year)
        rubble_loss = bc['rubble'] / self.constants.RUBBLE_EROSION_TIME_YEARS
        bc['rubble'] -= rubble_loss
        bc['dead_coral'] += rubble_loss
        
        # Verify and Normalize
        substrate_sum = (bc['hard_substrate'] + bc['dead_coral'] + bc['CCA'] + 
                        bc['turfing_algae'] + bc['macro_algae'] + 
                        bc['rubble'] + bc['sediment'])
                        
        target_substrate = 100.0 - self.total_cover
        
        if substrate_sum > 0 and abs(substrate_sum - target_substrate) > 0.001:
            multiplying_factor = target_substrate / substrate_sum
            for key in bc:
                if key != 'total' and key != 'available_substrate':
                   bc[key] *= multiplying_factor
                   
        bc['total'] = sum([v for k,v in bc.items() if k not in ['total', 'available_substrate']])
        

    def _update_rugosity(self, old_cover: Dict[str, float]):
        """
        Update Rugosity index based on coral cover change and composition.
        Logic: RI_t = RI_{t-1} + m * (Change_Total)
        where m depends on Branching / (Foliose + Other) ratio.
        """
        b_cov = self.cover_breakdown['Branching']
        f_cov = self.cover_breakdown['Foliose']
        o_cov = self.cover_breakdown['Other']
        
        denom = f_cov + o_cov
        ratio = b_cov / denom if denom > 0 else (100.0 if b_cov > 0 else 0)
        
        if ratio > 1.0:
            m = self.constants.SLOPE_MAX
        elif 0.1 < ratio <= 1.0:
            m = self.constants.SLOPE_AV
        else:
            m = self.constants.SLOPE_MIN
            
        change_total = self.total_cover - sum(old_cover.values())
        
        self.rugosity += m * change_total
        
        
    def _record_history(self):
        """Save current state to history."""
        self.history_population.append(self.population.copy())
        
        record = {'year': self.year, 'total_cover': self.total_cover}
        record.update(self.cover_breakdown)
        self.history_cover.append(record)
        
        self.history_benthic.append(self.benthic_cover.copy())
        self.history_rugosity.append(self.rugosity)
        
    def run(self):
        """Run the simulation for the configured duration."""
        years_to_run = self.params.max_year
        for _ in range(years_to_run):
            self.step()
            
    def step(self):
        """Execute one year of simulation."""
        self.year += 1
        current_abs_year = self.params.year_start + self.year
        
        old_cover = self.cover_breakdown.copy()
        
        # 1. Get Environment
        dhw = self.params.dhw_years.get(self.year, 0.0)
        cyclone_data = self.params.cyclone_years.get(self.year, [0.0, 0.0]) # [Sev, Dist]
        cyclone_sev, cyclone_dist = cyclone_data
        
        if not self.params.enable_bleaching:
            dhw = 0.0
        if not self.params.enable_cyclone:
            cyclone_sev = 0.0
            
        if dhw > 0:
            self.dhw_counter += 1
            
        # 2. Recruitment
        recruits = CoralDynamics.calculate_recruitment(
            self.params, 
            self.constants, 
            self.available_substrate, 
            dhw,
            self.cover_breakdown
        )
        
        # Add recruits to bin 0 of distinct types
        self.population[0, 0] += int(recruits[0])
        self.population[1, 0] += int(recruits[1])
        self.population[2, 0] += int(recruits[2])
        
        # 3. Rates
        gr_slope = np.random.uniform(0.01, 0.04)
        bins = np.arange(self.constants.MAX_BIN_ID)
        decline_factor = np.maximum(0, 1 - bins * gr_slope) # linear
        
        base_growth = np.array([
            self.params.growth_coefficient_branching * self.constants.DEFAULT_GROWTH_RATE_BRANCHING, 
            self.params.growth_coefficient_foliose * self.constants.DEFAULT_GROWTH_RATE_FOLIOSE,
            self.params.growth_coefficient_other * self.constants.DEFAULT_GROWTH_RATE_OTHER
        ])
        
        growth_rates = base_growth[:, None] * decline_factor[None, :]
        
        wcm_base = np.array([
            self.params.wcm_branching,
            self.params.wcm_foliose,
            self.params.wcm_other
        ])
        
        pcm_base = np.array([
            self.params.pcm_branching,
            self.params.pcm_foliose,
            self.params.pcm_other
        ])
        
        # Adjust Rates
        pcm_adj = CoralDynamics.adjust_pcm_for_bleaching(
            pcm_base / 100.0,
            dhw, 
            self.dhw_counter, 
            self.constants,
            self.params
        )
        
        wcm_adj = CoralDynamics.adjust_wcm_for_cyclone(
            wcm_base / 100.0,
            cyclone_sev, 
            cyclone_dist, 
            self.params, 
            self.constants
        )
        
        # 4. Grow/Die
        new_pop = CoralDynamics.grow_population(
            self.population,
            growth_rates,
            pcm_adj,
            wcm_adj,
            self.total_cover,
            self.params,
            self.constants
        )
        
        self.population = new_pop
        
        # 5. Update State
        self._update_derived_state()
        
        # 6. Benthic Dynamics
        self._update_benthic_dynamics(old_cover, dhw > 0, cyclone_sev > 0)
        
        # 7. Rugosity
        self._update_rugosity(old_cover)
        
        # 8. History
        self._record_history()
        
    def get_results_df(self) -> pd.DataFrame:
        """Return history as DataFrame."""
        return pd.DataFrame(self.history_cover)
    
    def get_rugosity_df(self) -> pd.DataFrame:
        return pd.DataFrame({'year': range(len(self.history_rugosity)), 'rugosity': self.history_rugosity})

    def get_benthic_df(self) -> pd.DataFrame:
        return pd.DataFrame(self.history_benthic)

def run_ensemble(n_iterations: int, params: Optional[CoralParameters] = None, constants: Optional[CoralConstants] = None) -> Dict[str, Any]:
    """
    Run the model multiple times to capture stochastic variations.
    Returns a dictionary containing:
      - 'cover': DataFrame of Total Cover (Mean, Std, Iterations)
      - 'rugosity': DataFrame of Rugosity (Mean, Std, Iterations)
      - 'metrics': Dictionary of aggregated final state metrics
    """
    if params is None:
        params = CoralParameters()
    if constants is None:
        constants = CoralConstants()
        
    cover_results = {}
    rugosity_results = {}
    
    final_pops = []
    final_taxa = []
    
    for i in range(n_iterations):
        model = CoralModel(params, constants)
        model.run()
        
        # 1. Total Cover History
        df = model.get_results_df()
        cover_results[f'iteration_{i+1}'] = df['total_cover'].values
        
        # 2. Rugosity History
        rug_df = model.get_rugosity_df()
        rugosity_results[f'iteration_{i+1}'] = rug_df['rugosity'].values
        
        # 3. Final State Metrics
        final_pops.append(model.population.sum())
        
        # Breakdown at final step
        last_step = df.iloc[-1]
        final_taxa.append({
            'Branching': last_step.get('Branching', 0),
            'Foliose': last_step.get('Foliose', 0),
            'Other': last_step.get('Other', 0)
        })

    # --- Process Cover Data ---
    ensemble_cover = pd.DataFrame(cover_results)
    ensemble_cover['year'] = range(len(ensemble_cover))
    iter_cols_cov = [c for c in ensemble_cover.columns if 'iteration' in c]
    ensemble_cover['mean'] = ensemble_cover[iter_cols_cov].mean(axis=1)
    ensemble_cover['std'] = ensemble_cover[iter_cols_cov].std(axis=1)
    # Reorder
    cols_cov = ['year', 'mean', 'std'] + iter_cols_cov
    ensemble_cover = ensemble_cover[cols_cov]
    
    # --- Process Rugosity Data ---
    ensemble_rugosity = pd.DataFrame(rugosity_results)
    ensemble_rugosity['year'] = range(len(ensemble_rugosity))
    iter_cols_rug = [c for c in ensemble_rugosity.columns if 'iteration' in c]
    ensemble_rugosity['mean'] = ensemble_rugosity[iter_cols_rug].mean(axis=1)
    ensemble_rugosity['std'] = ensemble_rugosity[iter_cols_rug].std(axis=1)
    # Reorder
    cols_rug = ['year', 'mean', 'std'] + iter_cols_rug
    ensemble_rugosity = ensemble_rugosity[cols_rug]
    
    # --- Process Final Metrics ---
    metrics = {}
    
    # Population
    metrics['pop_mean'] = float(np.mean(final_pops))
    metrics['pop_std'] = float(np.std(final_pops))
    
    # Rugosity Final
    metrics['rugosity_mean'] = float(ensemble_rugosity['mean'].iloc[-1])
    metrics['rugosity_std'] = float(ensemble_rugosity['std'].iloc[-1])
    
    # Total Cover Final
    metrics['cover_mean'] = float(ensemble_cover['mean'].iloc[-1])
    metrics['cover_std'] = float(ensemble_cover['std'].iloc[-1])
    
    # Dominant Taxa
    # Average the cover of each type across all runs
    avg_taxa = {
        'Branching': np.mean([x['Branching'] for x in final_taxa]),
        'Foliose': np.mean([x['Foliose'] for x in final_taxa]),
        'Other': np.mean([x['Other'] for x in final_taxa])
    }
    metrics['dominant_taxa'] = max(avg_taxa, key=avg_taxa.get)
    metrics['taxa_breakdown'] = avg_taxa
    
    return {
        "cover": ensemble_cover,
        "rugosity": ensemble_rugosity,
        "metrics": metrics
    }

