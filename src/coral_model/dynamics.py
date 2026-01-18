import numpy as np
from typing import Tuple, List, Optional, Dict
from .parameters import CoralConstants, CoralParameters

class CoralDynamics:
    """Stateless class containing core mathematical functions for coral dynamics."""
    
    @staticmethod
    def adjust_pcm_for_bleaching(
        pcm_rates: np.ndarray,
        dhw: float,
        dhw_counter: int,
        constants: CoralConstants,
        params: CoralParameters
    ) -> np.ndarray:
        """
        Adjust Partial Colony Mortality (PCM) rates based on Degree Heating Weeks (DHW).
        Returns new PCM rates array.
        """
        if dhw <= 0:
            return pcm_rates
            
        # Rates from config/constants
        # In original code these were global variables: branching_bleaching_rate = 14 etc.
        # We can put them in constants or params. Let's assume they are constants for now or passed.
        # Using hardcoded values from original config.py for now as they weren't in params.
        
        # Original:
        # branching_bleaching_rate = 14
        # foliose_bleaching_rate = 34
        # other_bleaching_rate = 34
        
        b_rate = constants.BLEACHING_RATE_BRANCHING
        f_rate = constants.BLEACHING_RATE_FOLIOSE
        o_rate = constants.BLEACHING_RATE_OTHER
        
        # Resilience Logic: Rates decrease with experience (wait, rate increases resilience?)
        # Legacy: rate *= 1.05**(counter-1)
        # If counter=1 (first event), factor=1.
        # If counter=2, factor=1.05.
        # This INCREASES the bleaching rate parameter.
        # In the formula: (1 - PCM)/(1 + rate * exp) + PCM
        # If rate increases, denom increases, fraction decreases.
        # Result -> closer to PCM.
        # So "PCM_adjusted" is SMALLER (less mortality added).
        # Correct.
        
        factor = (1 + params.acclimatization_rate) ** (max(0, dhw_counter - 1))
        b_rate *= factor
        f_rate *= factor
        o_rate *= factor
        
        # A array: 0.5 * 2^(i/(MaxBin-1))
        # i = 0..MaxBin-1
        max_bin = pcm_rates.shape[1]
        i_arr = np.arange(max_bin)
        A = 0.5 * (2**(i_arr / (constants.MAX_BIN_ID - 1)))
        
        exp_term = np.exp(4 - A * dhw)
        
        # Formula: new_rate = (1 - old) / (1 + rate * exp) + old
        # Wait, original formula:
        # (1 - PCM) / (1 + b_rate * exp) + PCM
        # This seems to DECREASE mortality?? 
        # (1-PCM) is survival.
        # If term > 1, then (1-PCM)/term < (1-PCM).
        # So survival decreases? No.
        # Let's check logic.
        # If exp is large, denom is large, fraction is small.
        # result = small + PCM.
        # if PCM=0.01. result ~ 0.01.
        # Survival term (1-PCM) is being scaled down?
        # Actually (1-PCM) is the healthy portion.
        # It's adding back to PCM?
        # Let's trust the formula copy.
        
        # Vectorized for types:
        base_rates = np.array([b_rate, f_rate, o_rate])
        
        # Expand exp_term to (3, Bins)
        exp_term_broadcast = exp_term[None, :] 
        base_rates_broadcast = base_rates[:, None]
        
        denom = 1 + base_rates_broadcast * exp_term_broadcast
        
        new_pcm = (1 - pcm_rates) / denom + pcm_rates
        
        return new_pcm

    @staticmethod
    def adjust_wcm_for_cyclone(
        wcm_rates: np.ndarray,
        severity: float,
        distance: float,
        params: CoralParameters,
        constants: CoralConstants
    ) -> np.ndarray:
        """
        Adjust Whole Colony Mortality (WCM) rates based on Cyclone.
        """
        if severity <= 0:
            return wcm_rates
            
        # severity * factor
        sev = severity * constants.CYCLONE_SEVERITY_FACTOR
        
        # bins array for cyclone
        # pp = linspace(1, MaxBin+1, 20) ? Or just use bin indices?
        # Original: pp = np.linspace(1, MaxBinId+1, 20) matching bins?
        # bins = pp * cyclone_bin_coeff
        # If max_bin=20, this creates 20 points.
        # Effectively 1..21
        
        pp = np.linspace(1, constants.MAX_BIN_ID + 1, constants.MAX_BIN_ID)
        bins = pp * params.cyclone_bin_coefficient
        
        # exp terms
        # exp(-distance / bins / cyclone_bin_coeff)
        exponent = -distance / bins
        base_exp = sev * np.exp(exponent)
        
        # Coefficients
        coeffs = np.array([
            params.branching_cyclone_coefficient,
            params.foliose_cyclone_coefficient,
            params.other_cyclone_coefficient
        ])
        
        # Formula: 1 - 1 / (1 + coeff * exp) + WCM
        # Again adding to WCM.
        
        base_exp_broad = base_exp[None, :]
        coeffs_broad = coeffs[:, None]
        
        term = 1 + coeffs_broad * base_exp_broad
        
        new_wcm = 1 - (1.0 / term) + wcm_rates
        
        return new_wcm

    @staticmethod
    def calculate_recruitment(
        params: CoralParameters,
        constants: CoralConstants,
        available_substrate_percentage: float,
        current_dhw: float,
        current_cover_pct: Dict[str, float]
    ) -> List[int]:
        """
        Calculate recruitment population for Branching, Foliose, Other.
        """
        if not params.enable_recruitment:
            return [0, 0, 0]
        
        def recruitment_bleaching_rate(dhw):
            val = 1 - 1 / (1 + params.bleaching_recruitment_coefficient * np.exp(4 - dhw))
            return val

        reef_area = params.reef_area
        
        # --- Brooder Recruitment ---
        brooder_cover_m2 = (params.initial_brooder_cover *
                   recruitment_bleaching_rate(current_dhw) *
                   reef_area / 100)
        
        brooder_cover_cm2_per_m2 = brooder_cover_m2 * 10000 / reef_area
        
        # Polyps
        polyp_size_cm2 = 75e-4
        number_polyps_per_cm2 = 1 / polyp_size_cm2
        planulae_per_polyp = 0.05 / 25
        
        number_planulae_released_per_m2 = (number_polyps_per_cm2 * 
                                          planulae_per_polyp * 
                                          brooder_cover_cm2_per_m2)
        
        available_substrate_m2 = available_substrate_percentage * reef_area / 100
        
        # Space limitation
        unavailable_pct = (params.macro_algae_cover + params.rubble_cover + params.sediment_cover)
        current_total_cover = 100 - unavailable_pct - available_substrate_percentage
        max_achievable = 100 - unavailable_pct
        
        if max_achievable <= 1e-6:
             space_limitation = 0.0
        else:
             ratio = current_total_cover / max_achievable
             # Clamp ratio 0-1
             ratio = np.clip(ratio, 0, 1)
             space_limitation = 1 - (ratio ** params.space_limitation_exponent)
            
        num_recruits_brooder = (number_planulae_released_per_m2 * 
                               available_substrate_m2 * 
                               space_limitation)
        
        brooder_mort_rates = np.array(constants.BROODER_MORTALITY_RATES)
        num_recruits_brooder *= np.prod(1 - brooder_mort_rates)
        
        # --- Spawner Recruitment ---
        spawner_cover_m2 = np.array(params.initial_spawner_cover) * reef_area / 100
        
        egg_density = np.array([constants.EGG_DENSITY_BRANCHING_FOLIOSE, constants.EGG_DENSITY_OTHER])
        number_of_eggs = (10000 * recruitment_bleaching_rate(current_dhw) *
                 egg_density * spawner_cover_m2)
        
        eggs_spawning_rate = np.array([
            np.random.uniform(0.63, 0.82),
            np.random.uniform(0.55, 0.67)
        ])
        
        num_eggs_spawning = (number_of_eggs * eggs_spawning_rate *
                    recruitment_bleaching_rate(current_dhw))
        
        fertilization_rate = np.random.uniform(0.41, 0.69)
        fertilised_eggs = fertilization_rate * num_eggs_spawning
        
        shape = params.reef_shape
        if shape in [7,8,9]: idx = 0
        elif shape in [3,4,10]: idx = 1
        elif shape in [2,5,6,11]: idx = 2
        else: idx = 3
        
        retention_bf = constants.RETENTION_RATES_8D[idx]
        retention_o = constants.RETENTION_RATES_4D[idx]
        eggs_retained = np.array([retention_bf, retention_o]) * fertilised_eggs
        
        survival_coeff = np.array([
            constants.LARVAL_SURVIVAL_BRANCHING_FOLIOSE,
            constants.LARVAL_SURVIVAL_OTHER
        ])
        larvae_survived = survival_coeff * eggs_retained
        
        scale_factor = 0.05 / (np.exp(1) - 1)
        settlement_base = scale_factor * (np.exp(available_substrate_percentage/100) - 1)
        if params.enable_recruitment_noise:
            settlement_rate = np.random.uniform(0.5 * settlement_base, 1.5 * settlement_base)
        else:
            settlement_rate = settlement_base
        
        larvae_settled = settlement_rate * larvae_survived
        
        spawner_bf_surv_prod = np.prod(constants.SPAWNER_BRANCHING_SURVIVAL_RATES)
        spawner_ot_surv_prod = np.prod(constants.SPAWNER_OTHER_SURVIVAL_RATES)
        
        num_recruits_spawner = np.array([
            larvae_settled[0] * spawner_bf_surv_prod, 
            larvae_settled[1] * spawner_ot_surv_prod
        ])
        
        bin_diameter_cm = constants.BIN_SIZE
        single_recruit_area_cm2 = constants.AREA_PARAMETER * np.pi * (bin_diameter_cm/2)**2
        single_recruit_area_m2 = single_recruit_area_cm2 / 10000
        
        surfaceArea_brooder_m2 = num_recruits_brooder * single_recruit_area_m2
        surfaceArea_spawner_m2 = num_recruits_spawner * single_recruit_area_m2
        
        total_bf_cover = current_cover_pct.get('Branching', 0.0) + current_cover_pct.get('Foliose', 0.0)
        if total_bf_cover > 0:
            branching_ratio = current_cover_pct.get('Branching', 0.0) / total_bf_cover
        else:
            branching_ratio = 0.5
            
        recruited_areas_m2 = np.array([
            surfaceArea_brooder_m2 + surfaceArea_spawner_m2[0] * branching_ratio,
            surfaceArea_spawner_m2[0] * (1 - branching_ratio),
            surfaceArea_spawner_m2[1]
        ])
        
        recruited_pop = recruited_areas_m2 / single_recruit_area_m2
        return recruited_pop.astype(int).tolist()

    @staticmethod
    def grow_population(
        population: np.ndarray,
        growth_rates: np.ndarray,
        pcm_rates: np.ndarray,
        wcm_rates: np.ndarray,
        current_total_cover: float,
        params: CoralParameters,
        constants: CoralConstants
    ) -> np.ndarray:
        """
        Vectorized calculation of population dynamics (Growth + Mortality).
        """
        num_types, num_bins = population.shape
        bin_size = constants.BIN_SIZE
        
        steps = np.linspace(0, 1, 100)
        lower_edges = np.arange(num_bins) * bin_size
        diameters = lower_edges[None, :, None] + steps[None, None, :] * bin_size 
        
        unavailable = params.macro_algae_cover + params.rubble_cover + params.sediment_cover
        max_achievable = 100 - unavailable
        
        if max_achievable <= 1e-6:
            space_limitation = 0
        else:
             ratio = current_total_cover / max_achievable
             ratio = np.clip(ratio, 0, 1)
             space_limitation = 1 - (ratio ** params.space_limitation_exponent)
            
        growth_delta = growth_rates * space_limitation
        new_diameters = diameters + growth_delta[:, :, None]
        
        shrinkage = np.sqrt(1 - pcm_rates)
        # Check config check: PCM_rates = pd.DataFrame({...}) / 100.
        # So inputs to this function should be fractions 0..1.
        # But wait, utils.py ln 1245: arr *= np.sqrt(1-pcm_rate).
        # utils.py ln 160: PCM_rates = ... [pcm/100 for pcm in ...]
        # So yes, inputs should be 0..1.
        
        new_diameters = new_diameters * shrinkage[:, :, None]
        
        bin_indices = np.floor(new_diameters / bin_size).astype(int)
        bin_indices = np.clip(bin_indices, 0, num_bins - 1)
        
        survivors_fraction = (1 - wcm_rates)
        
        # Fix broadcasting: (3, 20) * (3, 20) -> (3, 20) -> (3, 20, 1)
        weights_per_bin = population * survivors_fraction
        weights = weights_per_bin[:, :, None] / 100.0
        
        new_population = np.zeros_like(population, dtype=np.float64)
        
        for t in range(num_types):
            flat_indices = bin_indices[t].ravel()
            # weight[t] is (20, 1). We need to replicate it for 100 particles.
            w_expanded = np.broadcast_to(weights[t], (num_bins, 100))
            flat_weights = w_expanded.ravel()
            
            np.add.at(new_population[t], flat_indices, flat_weights)
            
        return new_population.astype(int)
