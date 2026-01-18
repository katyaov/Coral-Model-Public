from dataclasses import dataclass, field
from typing import List, Dict, Optional
import numpy as np

@dataclass
class CoralConstants:
    """Fixed biological constants and model configuration limits."""
    # Coral types
    CORAL_TYPES: List[str] = field(default_factory=lambda: ['Branching', 'Foliose', 'Other'])
    
    # Growth parameters
    MAX_BIN_ID: int = 20
    BIN_SIZE: float = 5.0  # cm
    
    # Default Growth rates (cm/year)
    DEFAULT_GROWTH_RATE_BRANCHING: float = 5.4
    DEFAULT_GROWTH_RATE_FOLIOSE: float = 2.1
    DEFAULT_GROWTH_RATE_OTHER: float = 0.8
    
    # Egg density (Eggs/cm3)
    EGG_DENSITY_BRANCHING_FOLIOSE: int = 375
    EGG_DENSITY_OTHER: int = 600
    
    # Retention rates (Daily 8 and 4) based on connection group (G1-G4)
    # These are pre-calculated products from original config.py
    # G1: Very High, G2: High, G3: Medium, G4: Low
    RETENTION_RATES_8D: List[float] = field(default_factory=lambda: [
        1 * 0.98 * 0.95 * 0.9 * 0.85,                           # G1
        1 * 0.9 * 0.75 * 0.6 * 0.5,                             # G2
        1 * 0.8 * 0.5 * 0.2 * 0.1,                              # G3
        1 * 0.8 * 0.4 * 0.1 * 0.05                              # G4
    ])
    
    RETENTION_RATES_4D: List[float] = field(default_factory=lambda: [
        1 * 0.98 * 0.95 * 0.9 * 0.85,                           # G1 (Same as 8d in code?)
        1 * 0.9 * 0.75 * 0.6 * 0.5,                             # G2
        1 * 0.8 * 0.5 * 0.2 * 0.1,                              # G3
        1 * 0.8 * 0.4 * 0.1 * 0.05                              # G4
    ])

    # Larval survival rates
    LARVAL_SURVIVAL_BRANCHING_FOLIOSE: float = 0.84 * 0.87 * 0.93 * 0.94 * 0.95 * 0.96 * 0.965 * 0.97
    LARVAL_SURVIVAL_OTHER: float = 0.915**4

    # Post-settlement survival / mortality rates (Yearly)
    BROODER_MORTALITY_RATES: List[float] = field(default_factory=lambda: [0.0, 0.73, 0.39, 0.37, 0.35])
    SPAWNER_BRANCHING_SURVIVAL_RATES: List[float] = field(default_factory=lambda: [0.05, 0.81, 0.93, 0.88, 0.9])
    SPAWNER_OTHER_SURVIVAL_RATES: List[float] = field(default_factory=lambda: [0.05, 0.865, 0.83, 0.91, 0.925])
    
    # Area parameter (1=flat, 4=spherical)
    AREA_PARAMETER: int = 1
    UNIT_CONVERSION_M2_TOK_CM2: int = 10000

    # Rugosity Slopes (for RI calculation)
    SLOPE_MAX: float = 0.0487
    SLOPE_MIN: float = 0.019
    SLOPE_AV: float = 0.0340

    # Bleaching Susceptibility Rates
    BLEACHING_RATE_BRANCHING: float = 14.0
    BLEACHING_RATE_FOLIOSE: float = 34.0
    BLEACHING_RATE_OTHER: float = 34.0

    # Cyclone
    CYCLONE_SEVERITY_FACTOR: float = 2.0

    # Benthic Dynamics
    RUBBLE_EROSION_TIME_YEARS: float = 6.0  # Years to convert rubble to dead coral


@dataclass
class CoralParameters:
    """Simulated scenario parameters (user configurable)."""
    
    # Simulation Time
    year_start: int = 2000
    year_end: int = 2050
    
    # Reef Configuration
    reef_area: float = 10000.0
    reef_shape: int = 5  # 1-12
    initial_rugosity: float = 1.6
    reef_exposure: str = 'protected'  # 'protected', 'semiprotected', 'exposed'
    
    # Benthic Cover (%)
    hard_substrate_cover: float = 0.0
    dead_coral_cover: float = 1.0
    cca_cover: float = 8.5
    turfing_algae_cover: float = 62.4
    macro_algae_cover: float = 3.5
    rubble_cover: float = 1.0
    sediment_cover: float = 2.9
    
    # Initial Coral Cover (%)
    initial_coral_cover: Dict[str, float] = field(default_factory=lambda: {
        'Branching': 1.8, 'Foliose': 6.9, 'Other': 11.9
    })
    
    # Initial Spawner/Brooder Cover
    initial_brooder_cover: float = 0.9
    initial_spawner_cover: List[float] = field(default_factory=lambda: [7.8, 11.9]) # [B+F, O]
    
    # Stressor Configuration
    enable_bleaching: bool = True
    enable_cyclone: bool = True
    enable_recruitment: bool = True
    enable_recruitment_noise: bool = False
    bleaching_recruitment_coefficient: float = 25.0
    
    # Acclimatization (Resilience)
    acclimatization_rate: float = 0.05
    
    # Dictionary of Year: DHW
    dhw_years: Dict[int, float] = field(default_factory=lambda: {5: 8, 12: 6, 20: 12, 35: 8})
    
    # Dictionary of Year: [Severity, Distance]
    cyclone_years: Dict[int, List[float]] = field(default_factory=lambda: {
        15: [1, 40], 28: [2, 106], 35: [4, 25], 42: [3, 258]
    })
    
    # Growth Coefficients (modifiers)
    growth_coefficient_branching: float = 1.0
    growth_coefficient_foliose: float = 1.0
    growth_coefficient_other: float = 1.0
    
    # Mortality Rates (Default Lists)
    # Whole Colony Mortality (%)
    wcm_branching: List[float] = field(default_factory=lambda: [
        20.0, 14.8, 14.8, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6,
        7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6
    ])
    wcm_foliose: List[float] = field(default_factory=lambda: [
        20.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
        2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0
    ])
    wcm_other: List[float] = field(default_factory=lambda: [
        20.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0,
        2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0
    ])
    
    # Partial Colony Mortality (%)
    pcm_branching: List[float] = field(default_factory=lambda: [
        1.63, 1.91, 2.19, 2.47, 2.75, 3.03, 3.30, 3.58, 3.86, 4.14,
        4.42, 4.70, 4.98, 5.25, 5.53, 5.81, 6.09, 6.37, 6.65, 6.75
    ])
    pcm_foliose: List[float] = field(default_factory=lambda: [
        1.17, 1.36, 1.56, 1.76, 1.96, 2.16, 2.36, 2.56, 2.76, 2.96,
        3.16, 3.35, 3.55, 3.75, 3.95, 4.15, 4.35, 4.55, 4.75, 4.80
    ])
    pcm_other: List[float] = field(default_factory=lambda: [
        1.17, 1.36, 1.56, 1.76, 1.96, 2.16, 2.36, 2.56, 2.76, 2.96,
        3.16, 3.35, 3.55, 3.75, 3.95, 4.15, 4.35, 4.55, 4.75, 4.80
    ])
    
    # Population Size Distribution (PSD) at T0 (%)
    psd_branching: List[float] = field(default_factory=lambda: [
        0.0, 1.5, 19.0, 15.8, 11.7, 10.0, 8.3, 6.6, 4.9, 3.2, 
        2.5, 2.1, 2.0, 2.0, 1.9, 1.9, 1.8, 1.8, 1.6, 1.5
    ])
    psd_foliose: List[float] = field(default_factory=lambda: [
        0.0, 0.0, 16.5, 12.0, 11.2, 7.4, 7.2, 6.0, 6.4, 4.3, 
        3.8, 3.1, 3.0, 3.0, 2.9, 2.8, 2.7, 2.6, 2.6, 2.5
    ])
    psd_other: List[float] = field(default_factory=lambda: [
        7.8, 10.1, 23.4, 10.3, 9.7, 5.8, 5.7, 4.7, 5.3, 3.3, 
        2.9, 2.5, 2.2, 1.8, 1.5, 1.2, 0.9, 0.6, 0.3, 0.0
    ])

    # Cyclone Constants
    cyclone_bin_coefficient: float = 5.0
    
    # Growth Limitation
    space_limitation_exponent: float = 1.0

    @property
    def max_year(self) -> int:
        return self.year_end - self.year_start
        
    @property
    def reef_type_coefficient(self) -> float:
        if self.reef_exposure.lower() == 'protected':
            return 0.25
        elif 'semi' in self.reef_exposure.lower():
            return 0.5
        else: # exposed
            return 1.0

    @property
    def branching_cyclone_coefficient(self) -> float:
        return 0.9 * self.reef_type_coefficient
    
    @property
    def foliose_cyclone_coefficient(self) -> float:
        return 0.75 * self.reef_type_coefficient
    
    @property
    def other_cyclone_coefficient(self) -> float:
        return 0.5 * self.reef_type_coefficient

