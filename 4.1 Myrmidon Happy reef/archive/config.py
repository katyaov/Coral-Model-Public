import os
import random
import pandas as pd
import numpy as np
import warnings
from user_inputs_old import *

# warnings.filterwarnings("ignore", category=RuntimeWarning, message="overflow encountered in double_scalars")
# warnings.resetwarnings()
# warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

if (year_end - year_start) <= 0:
    raise ValueError(f"The end year {year_end} should be greater than the starting year {year_start}.")
    
if bleaching:
    for key in dhw_years.keys():
        if key > MaxYear:
            raise ValueError(f"The dhw year {key} is greater than the maximum allowed year {MaxYear}.")

if cyclone:
    for key in cyclone_years.keys():
        if key > MaxYear:
            raise ValueError(f"The cyclone year {key} is greater than the maximum allowed year {MaxYear}.")
            

linear_decay_growth_rate = True    # True for linear growth rate or False for exponential decay growth rate            
coral_type = ['Branching','Foliose','Other']

#default growth rate values (cm/year)
default_growth_rate_branching      = 5.4
default_growth_rate_foliose         = 2.1
default_growth_rate_other          = 0.8

#slopes for calculationg new RI as RI_n= DTCC*slope + RI
slope_max = 0.0487
slope_min = 0.019
slope_av = 0.0340

#egg density (Eggs/cm3)
egg_density_spawner_branching_foliose = 375
egg_density_spawner_other = 600
 #THIS CODE NEEDS CLEANING
daily8_retention_rates_G1 = 0.95 * 0.9 * 0.8 * 0.8 * 0.7 #* 0.8 * 0.75 *  0.65  # very high NEED TO REMOVE
daily4_retention_rates_G1 = 0.95 * 0.9 * 0.8 * 0.8  * 0.7 # very high NEED TO REMOVE
 
daily8_retention_rates_G2 = 0.95 * 0.9 * 0.7 * 0.5 * 0.3 #* 0.4 * 0.3 * 0.2  #  high
daily4_retention_rates_G2 = 0.95 * 0.9 * 0.7 * 0.5 * 0.3 #  high
 
daily8_retention_rates_G3 = 0.95 * 0.8 * 0.5 * 0.3 * 0.1 #* 0.075 * 0.05 * 0.03   # medium
daily4_retention_rates_G3 = 0.95 * 0.8 * 0.5 * 0.3 * 0.1 # medium
 
daily8_retention_rates_G4 = 0.825 * 0.35 * 0.1 * 0.04 * 0.02 #* 0.01 * 0.005 * 0.001 #  low
daily4_retention_rates_G4 = 0.825 * 0.35 * 0.1 * 0.04 * 0.02 #  low


retention_rates_8d = [daily8_retention_rates_G1, daily8_retention_rates_G2, daily8_retention_rates_G3, daily8_retention_rates_G4]
retention_rates_4d = [daily4_retention_rates_G1, daily4_retention_rates_G2, daily4_retention_rates_G3, daily4_retention_rates_G4]

larval_survival_rate_branching_foliose = 0.84 * 0.87 * 0.93 * 0.94 * 0.95 * 0.96 * 0.965 * 0.97
larval_survival_rate_other = 0.915**4

brooder_survival_rates = [0.27, 0.61, 0.63, 0.65] #yearly rates
spawner_branching_survival_rates = [0.81, 0.93, 0.88, 0.9]
spawner_other_survival_rates = [0.865, 0.83, 0.91, 0.925]

if not use_custom_coral_population_size_distribution:
    PSD_T0 = pd.DataFrame({
    'Bins':[5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100],    
     'Branching': [1.0, 8.5, 11.5, 10.2, 9.3, 8.4, 7.5, 6.6, 5.7, 4.7, 3.8, 3.2, 3.0, 2.9, 2.7, 2.5, 2.4, 2.2, 2.1, 1.9],
    'Foliose': [2.8, 13.3, 14.2, 7.6, 7.0, 6.4, 5.8, 5.2, 4.6, 4.0, 3.5, 2.8, 2.8, 2.8, 2.8, 2.8, 2.8, 2.8, 2.8, 2.8],
    'Other': [18.8, 25.3, 19.7, 4.7, 4.3, 4.0, 3.6, 3.3, 2.9, 2.6, 2.2, 1.9, 1.6, 1.4, 1.2, 0.9, 0.7, 0.5, 0.3, 0.0]
})

else:
    reference_size = len(custom_PSD_T0[list(custom_PSD_T0.keys())[0]])
    if all(len(custom_PSD_T0[key]) == reference_size for key in custom_PSD_T0):
        PSD_T0 = pd.DataFrame(custom_PSD_T0)
    else:
        raise ValueError("Size mismatch found in the custom population size distribution. Make sure the population size distribution lists have equal sizes")

MaxBinId = len(PSD_T0['Branching'])
binSize = PSD_T0['Bins'][0] # bin size in cm

if not use_custom_partial_mortality_rate:
    #per bin size 5-95
    partial_mortality_rates_branching = [0.0163, 0.0191, 0.0219, 0.0247, 0.0275, 0.0303, 0.0330, 0.0358, 0.0386, 0.0414, 0.0442, 0.0470, 0.0498, 0.0525, 0.0553, 0.0581, 0.0609, 0.0637, 0.0665, 0.0675]
    partial_mortality_rates_foliose = [0.0117, 0.0136, 0.0156, 0.0176, 0.0196, 0.0216, 0.0236, 0.0256, 0.0276, 0.0296, 0.0316, 0.0335, 0.0355, 0.0375, 0.0395, 0.0415, 0.0435, 0.0455, 0.0475, 0.048]
    partial_mortality_rates_other = [0.0117, 0.0136, 0.0156, 0.0176, 0.0196, 0.0216, 0.0236, 0.0256, 0.0276, 0.0296, 0.0316, 0.0335, 0.0355, 0.0375, 0.0395, 0.0415, 0.0435, 0.0455, 0.0475, 0.048]
else:
    if len(custom_partial_mortality_rates_branching) != MaxBinId or len(custom_partial_mortality_rates_foliose) != MaxBinId or len(custom_partial_mortality_rates_other) != MaxBinId:
        raise ValueError(f"All lists must have a length of {MaxBinId}.")
    else:
        partial_mortality_rates_branching = custom_partial_mortality_rates_branching
        partial_mortality_rates_foliose = custom_partial_mortality_rates_foliose
        partial_mortality_rates_other = custom_partial_mortality_rates_other

if not use_custom_whole_mortality_rate:
    wcm_branching = [20, 14.8, 14.8, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6]
    wcm_foliose = [20.0, 4.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
    wcm_other = [20.0, 4.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0]
else:
    if len(custom_wcm_branching) != MaxBinId or len(custom_wcm_foliose) != MaxBinId or len(custom_wcm_other) != MaxBinId:
        raise ValueError(f"All lists must have a length of {MaxBinId}.")
    else:
        wcm_branching = custom_wcm_branching
        wcm_foliose = custom_wcm_foliose
        wcm_other = custom_wcm_other


area_parameter = 1    # Fitting parameter for area. Value between 1 and 4. 1 for flat coral surface area and 4 for spherical coral surface area. Used for estimation of the population in a bin

rugosity_initial = Initial_Rugosity
slope_max = 0.0487
slope_min = 0.0199
slope_av = 0.03385

unit_conversion_m2_to_cm2 = 10000
area_parameter = 1

if bleaching:
    dhw_years = dhw_years
else:
    dhw_years = {0:0}

# Change the rates here to change the bleaching effects
# Smaller rates gives higher decrease in coral covers - so higher the number, the more resilient
branching_bleaching_rate = 10
foliose_bleaching_rate = 20
other_bleaching_rate = 40

eggs_decline_coefficient = 34
colonies_spawning_decline_coefficient = 25

if cyclone:
    cyclone_years = cyclone_years
else:
    cyclone_years = {0:[0,0]}
    
    
cyclone_bin_coefficient = 5

if reef_exposure == 'protected' or reef_exposure == 'Protected':
    reef_type_coefficient = 0.25
elif reef_exposure == 'semiprotected' or reef_exposure == 'Semiprotected' or reef_exposure == 'Semi-protected' or reef_exposure == 'semi-protected':
    reef_type_coefficient = 0.5
elif reef_exposure == 'exposed' or reef_exposure == 'Exposed':
    reef_type_coefficient = 1
else:
    raise ValueError("reef type must be one of the following ['protected','semiprotected','exposed'].")

# Change the rates to change the cyclone effects. Smaller coefficient gives less cyclone impacts
# coefficients should be between 0 and 1. It should always be less than 1
branching_cyclone_coefficient = 0.8 * reef_type_coefficient
foliose_cyclone_coefficient = 0.5 * reef_type_coefficient
other_cyclone_coefficient = 0.3 * reef_type_coefficient

if not growthOnly:
    WCM_rates = pd.DataFrame({
                'Branching': [wcm/100 for wcm in wcm_branching],
                'Foliose': [wcm/100 for wcm in wcm_foliose],
                'Other': [wcm/100 for wcm in wcm_other],
                })
    
    PCM_rates = pd.DataFrame({
                'Branching': [pcm/100 for pcm in partial_mortality_rates_branching],
                'Foliose': [pcm/100 for pcm in partial_mortality_rates_foliose],
                'Other': [pcm/100 for pcm in partial_mortality_rates_other],
                })
    
else:
    WCM_rates = pd.DataFrame({
                'Branching': [0] * MaxBinId,
                'Foliose': [0] * MaxBinId,
                'Other': [0] * MaxBinId,
                 })
    PCM_rates = WCM_rates

                                                     
class CoralOptions:
    upper_diameter = MaxBinId * binSize
    growth_parameter = 0.5
    reef_area = reef_area 
    reef_shape = reef_shape
    
    # initial_spawner_cover = [43.8, 16.6]  # the first element is B+F and the second element is O
    brooder_cover = initial_brooder_cover
    spawner_cover = initial_spawner_cover
    eggs_density = [egg_density_spawner_branching_foliose, egg_density_spawner_other]
    eggs_spawning_rate = [random.uniform(0.63,0.82), random.uniform(0.55,0.67)]
    eggs_fertilisation_rate = random.uniform(0.41,0.69)
        
    if linear_decay_growth_rate:
        gr_slope = random.uniform(0.005, 0.045)
    else:
        gr_slope = random.uniform(0.05,1)
    
    initial_benthic_cover_dict = {
                        "total": hard_substrate_cover \
                                + dead_coral_cover \
                                + CCA_cover  \
                                + turfing_algae_cover \
                                + macro_algae_cover \
                                + rubble_cover \
                                + sediment_cover,
                        "available_substrate" : hard_substrate_cover \
                                                + turfing_algae_cover \
                                                + CCA_cover \
                                                + dead_coral_cover,
                        "hard_substrate" : hard_substrate_cover,
                        "dead_coral" : dead_coral_cover,
                        "CCA" : CCA_cover,
                        "turfing_algae" : turfing_algae_cover,
                        "macro_algae" : macro_algae_cover,
                        "rubble" : rubble_cover,
                        "sediment" : sediment_cover
                    }
    
    current_coral_cover = initial_coral_cover.copy()
    current_total_coral_cover = initial_total_coral_cover
    yearly_population_df_list = []
    yearly_surface_area_df_list = []
    
    current_total_coral_area_m2 = initial_total_coral_cover * reef_area / 100
    current_branching_total_area_m2 = initial_coral_cover['Branching'] * reef_area / 100
    current_foliose_total_area_m2 = initial_coral_cover['Foliose'] * reef_area / 100
    current_other_total_area_m2 = initial_coral_cover['Other'] * reef_area / 100
    
    available_substrate_percentage = initial_benthic_cover_dict['available_substrate']
    available_substrate_m2 = available_substrate_percentage * reef_area / 100
    # unavailable_substrate_percentage = 100 - initial_total_coral_cover - available_substrate_percentage
    unavailable_substrate_percentage = macro_algae_cover + rubble_cover + sediment_cover
    unavailable_substrate_m2 = unavailable_substrate_percentage*reef_area/100
    
    maximum_achievable_substrate_percentage = 100 - unavailable_substrate_percentage
    
    
opts = CoralOptions()

if linear_decay_growth_rate:
    rate_of_decline = np.array([1 if i==0 else 1-(i-1) * opts.gr_slope for i in range(MaxBinId)])

else:
    rate_of_decline = np.array([np.exp(-opts.gr_slope * binId) for binId in range(MaxBinId)])

if use_custom_growth_rate:
    growth_rate_branching = growth_coefficient_branching * custom_growth_rate_branching
    growth_rate_foliose = growth_coefficient_foliose * custom_growth_rate_foliose
    growth_rate_other = growth_coefficient_other * custom_growth_rate_other

else:
    growth_rate_branching = 2 * default_growth_rate_branching
    growth_rate_foliose = 2 * default_growth_rate_foliose
    growth_rate_other = 2 * default_growth_rate_other

growth_rate = pd.DataFrame({'Branching': growth_rate_branching * rate_of_decline,
                            'Foliose': growth_rate_foliose * rate_of_decline,
                            'Other': growth_rate_other * rate_of_decline,
                            })

output_folder = 'output'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

