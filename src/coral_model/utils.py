import numpy as np
import pandas as pd
from typing import List, Dict, Union, Tuple
from .parameters import CoralConstants, CoralParameters

class CoralUtils:
    """Helper functions for geometric conversions and initialization."""
    
    @staticmethod
    def get_bin_diameter(bin_id: Union[int, np.ndarray], constants: CoralConstants) -> Union[float, np.ndarray]:
        """Calculate bin diameter (cm)."""
        lower = bin_id * constants.BIN_SIZE
        upper = (bin_id + 1) * constants.BIN_SIZE
        # RMS diameter approximation used in original code
        return np.sqrt(lower**2/2 + upper**2/2)

    @staticmethod
    def get_colony_area_cm2(bin_id: Union[int, np.ndarray], constants: CoralConstants) -> Union[float, np.ndarray]:
        """Calculate projected colony surface area (cm2)."""
        diameter = CoralUtils.get_bin_diameter(bin_id, constants)
        return constants.AREA_PARAMETER * np.pi * (diameter/2)**2

    @staticmethod
    def population_to_area_m2(
        population: np.ndarray, 
        constants: CoralConstants
    ) -> np.ndarray:
        """Convert population counts to surface area (m2)."""
        # population shape: (3, MaxBins)
        # bin_ids: (MaxBins,)
        num_bins = population.shape[1]
        bin_ids = np.arange(num_bins)
        
        area_cm2 = CoralUtils.get_colony_area_cm2(bin_ids, constants) # (MaxBins,)
        
        # Broadcast multiply
        total_area_cm2 = population * area_cm2[None, :]
        return total_area_cm2 / 10000.0 # to m2

    @staticmethod
    def area_m2_to_population(
        area_m2: np.ndarray, 
        constants: CoralConstants
    ) -> np.ndarray:
        """Convert surface area (m2) to population counts."""
        num_bins = area_m2.shape[1]
        bin_ids = np.arange(num_bins)
        area_cm2 = CoralUtils.get_colony_area_cm2(bin_ids, constants)
        return (area_m2 * 10000.0 / area_cm2[None, :]).astype(int)

    @staticmethod
    def split_w(x: float, y: float, z: float, t: float, w: float) -> Tuple[float, float, float]:
        """
        Split value w proportionally into components based on x, y, z relative to total t.
        Used for distributing lost coral cover into benthic components.
        """
        if t == 0:
            return 0.0, 0.0, 0.0
            
        x_ratio = x / t
        y_ratio = y / t
        z_ratio = z / t
        
        w_x = x_ratio * w
        w_y = y_ratio * w
        w_z = z_ratio * w
        
        # Ensure sum conservation due to floating point or ratio sum mismatch
        current_sum = w_x + w_y + w_z
        if current_sum != w and current_sum != 0:
            factor = w / current_sum
            w_x *= factor
            w_y *= factor
            w_z *= factor
            
        return w_x, w_y, w_z

    @staticmethod
    def estimate_initial_population(
        params: CoralParameters,
        constants: CoralConstants
    ) -> np.ndarray:
        """
        Estimate initial population distribution from Cover % and PSD %.
        Returns array (3, MaxBins).
        """
        # 1. Target Coral Cover Area (m2)
        total_area_m2 = params.reef_area
        target_cover_m2 = {
            'Branching': params.initial_coral_cover['Branching'] * total_area_m2 / 100,
            'Foliose': params.initial_coral_cover['Foliose'] * total_area_m2 / 100,
            'Other': params.initial_coral_cover['Other'] * total_area_m2 / 100,
        }
        
        # 2. PSD (normalized to sum to 1.0)
        psd_dict = {
            'Branching': np.array(params.psd_branching),
            'Foliose': np.array(params.psd_foliose),
            'Other': np.array(params.psd_other)
        }
        
        # 3. Solve for N (Total Population)
        # Area = Sum( N * psd_i * area_i )
        # N = Area / Sum( psd_i * area_i )
        
        population = np.zeros((3, constants.MAX_BIN_ID), dtype=int)
        types = ['Branching', 'Foliose', 'Other']
        
        bin_ids = np.arange(constants.MAX_BIN_ID)
        unit_area_m2 = CoralUtils.get_colony_area_cm2(bin_ids, constants) / 10000.0
        
        for i, c_type in enumerate(types):
            target = target_cover_m2[c_type]
            psd = psd_dict[c_type]
            
            # Normalize PSD if not already
            if psd.sum() > 0:
                psd = psd / psd.sum()
            else:
                continue
                
            # Average area per colony given PSD
            avg_area = np.sum(psd * unit_area_m2)
            
            if avg_area > 0:
                total_N = target / avg_area
                # Distribute N according to PSD
                pop_distribution = total_N * psd
                population[i] = np.round(pop_distribution).astype(int)
                
        return population
