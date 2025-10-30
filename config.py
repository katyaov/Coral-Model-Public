import os
import random
import pandas as pd
import numpy as np
import warnings
from user_inputs import *

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

#growth rate coefficients - fixed at 2 for all morphologies for the time being
growth_coefficient_branching = 2
growth_coefficient_foliose = 2
growth_coefficient_other = 2

#slopes for calculating new RI as RI_n DTCC*slope + RI
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

branching_cyclone_coefficient = branching_cyclone_coefficient_input * reef_type_coefficient
foliose_cyclone_coefficient = foliose_cyclone_coefficient_input * reef_type_coefficient
other_cyclone_coefficient = other_cyclone_coefficient_input * reef_type_coefficient

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
    def __init__(self):
        # Core reef geometry / globals
        self.upper_diameter = MaxBinId * binSize
        self.growth_parameter = 0.5
        self.reef_area = reef_area
        self.reef_shape = reef_shape

        # Disturbance switches (read from user_inputs.py)
        self.bleaching = bool(bleaching)
        self.cyclone = bool(cyclone)
        self.enable_sediment_exposure = bool(enable_sediment_exposure)

        # Reproduction & larvae
        self.brooder_cover = initial_brooder_cover
        self.spawner_cover = initial_spawner_cover
        self.eggs_density = [
            egg_density_spawner_branching_foliose,
            egg_density_spawner_other
        ]
        ####
        # self.eggs_spawning_rate = [
        #     random.uniform(0.63, 0.82),
        #     random.uniform(0.55, 0.67)
        # ]
        # self.eggs_fertilisation_rate = random.uniform(0.41, 0.69)

        # # Growth slope
        # if linear_decay_growth_rate:
        #     self.gr_slope = random.uniform(0.005, 0.045)
        #     self.rate_of_decline = np.array([1 if i == 0 else 1 - (i - 1) * self.gr_slope for i in range(MaxBinId)])
        # else:
        #     self.gr_slope = random.uniform(0.05, 1)
        #     self.rate_of_decline = np.array([np.exp(-self.gr_slope * binId) for binId in range(MaxBinId)])
        # Move randomized defaults out of the constructor: set placeholders (will be set in initialize_coral)
        self.eggs_spawning_rate = None           # will be assigned in initialize_coral()
        self.eggs_fertilisation_rate = None      # will be assigned in initialize_coral()
        # growth slope placeholder (randomized per run in initialize_coral / run_yearly_change)
        self.gr_slope = None
        # rate_of_decline will be computed in initialize_coral() (and recomputed per run in run_yearly_change)

####
        # Initial benthic cover dict
        self.initial_benthic_cover_dict = {
            "total": (
                hard_substrate_cover
                + dead_coral_cover
                + CCA_cover
                + turfing_algae_cover
                + macro_algae_cover
                + rubble_cover
                + sediment_cover
            ),
            "available_substrate": (
                hard_substrate_cover
                + turfing_algae_cover
                + CCA_cover
                + dead_coral_cover
            ),
            "hard_substrate": hard_substrate_cover,
            "dead_coral": dead_coral_cover,
            "CCA": CCA_cover,
            "turfing_algae": turfing_algae_cover,
            "macro_algae": macro_algae_cover,
            "rubble": rubble_cover,
            "sediment": sediment_cover,
        }

        # Current state 
        self.current_coral_cover = initial_coral_cover.copy()
        self.current_total_coral_cover = initial_total_coral_cover
        self.yearly_population_df_list = []
        self.yearly_surface_area_df_list = []

        # Substrate / area 
        self.current_total_coral_area_m2 = initial_total_coral_cover * self.reef_area / 100
        self.current_branching_total_area_m2 = initial_coral_cover['Branching'] * self.reef_area / 100
        self.current_foliose_total_area_m2 = initial_coral_cover['Foliose'] * self.reef_area / 100
        self.current_other_total_area_m2 = initial_coral_cover['Other'] * self.reef_area / 100

        self.available_substrate_percentage = self.initial_benthic_cover_dict['available_substrate']
        self.available_substrate_m2 = self.available_substrate_percentage * self.reef_area / 100

        #rio ask katya:Minor text/typo:
#There is a stray line "available_substrate_percentage" (no assignment) in one of your files — that will raise NameError or SyntaxError if executed.

        # Unavailable substrate is macro + rubble + sediment (as in your code)
        self.unavailable_substrate_percentage = macro_algae_cover + rubble_cover + sediment_cover
        self.unavailable_substrate_m2 = self.unavailable_substrate_percentage * self.reef_area / 100
        self.maximum_achievable_substrate_percentage = 100 - self.unavailable_substrate_percentage

#sediment calculations


# Calculate additional sediment exposure per month and then aggregate to yearly totals.
# Assumes:
# - enable_sediment_exposure: bool flag from user inputs.
# - sedi_years: dict with keys (year, month) and values (suspended, deposited).
# - baseline_suspended_sediment, baseline_deposited_sediment: baseline scalar values to subtract.
# - MaxYear: integer maximum year index.
if enable_sediment_exposure:
    # For each (year, month) compute additional suspended and deposited sediment
    # relative to the baselines. Clamp negatives to 0.
    additional_sediment_exposure = {
        (year, month): (
            max(0.0, suspended - baseline_suspended_sediment),
            max(0.0, deposited - baseline_deposited_sediment)
        )
        for (year, month), (suspended, deposited) in sedi_years.items()
    }

    # Initialize yearly totals dictionary with zero tuples for each year index
    add_sedi_exp_per_year = {year: (0.0, 0.0) for year in range(MaxYear + 1)}

    # Sum the monthly additional values into yearly totals.
    for (year, month), (suspended, deposited) in additional_sediment_exposure.items():
        total_suspended, total_deposited = add_sedi_exp_per_year.get(year, (0.0, 0.0))
        add_sedi_exp_per_year[year] = (
            total_suspended + suspended,
            total_deposited + deposited
        )
else:
    # If sediment exposure is disabled, produce a zeroed yearly dictionary
    add_sedi_exp_per_year = {year: (0.0, 0.0) for year in range(MaxYear + 1)}



#sediment exposure partial mortality relationships for each morphology 
sedi_exp_PCM_coeff = {
    'Branching': 0.00154,
    'Foliose': 0.000724, 
    'Other': 0.001645  
    # 'Branching': 0.154,
    # 'Foliose': 0.0724, 
    # 'Other': 0.1645        
}


sedi_exp_growth_coeff = {
    'Branching': -0.00997,
    'Foliose': -0.00272, 
    'Other': -0.00533
}         



#sediment exposure settlement relationships for spawners and brooders
sedi_exp_settlement_coeff = {
    'spawner': -1.0609,
    'brooder': -0.2129      
}

#sediment exposure fertilisation relationships for spawners and brooders
sedi_exp_fertilisation_coeff = {
    'spawner': -0.006232,
    'brooder': 1   # this is a placeholder, as brooder fertilisation is not affected by sediment exposure  
}

#applied sediment coefficients 

###RIO MOVE IN FROM UTILS

def create_dhw_list(dhw_years):
	"""
	Create a list of degree heating week values given a dictionary of year-temperature pairs.
	If the temperature at a given year is 0, take two-thirds of the temperature of the previous year.
	Otherwise, take the temperature as it is given.

	Parameters
	----------
	dhw_years : dict
		A dictionary of year-temperature pairs.

	Returns
	-------
	list
		A list of degree heating week values.

	"""
	dhw_lst = [0] * (MaxYear+1)  # create a list of zeros length equals to MaxYear
	for year, temperature in dhw_years.items():
		dhw_lst[int(year)] = temperature  # set the temperature at the corresponding year index
	
	for i in range(len(dhw_lst)):
		if dhw_lst[i] == 0:
			if i == 0:
				dhw_lst[i] = dhw_lst[0]
			else:
				dhw_lst[i] = int(2*dhw_lst[i-1]/3)
	
	return dhw_lst


def create_cyclone_list(cyc_years):
	"""
	Create a cyclone list based on the given cyclone years, severity and distances.

	Parameters
	----------
	cyc_years : dict
		A dictionary containing cyclone years as keys and severity and distances as values.

	Returns
	-------
	numpy.ndarray
		An array representing the cyclone list where each index corresponds to a year.
		If no cyclone data is available for a particular year, the corresponding entry is set to [0, 0].

	Notes
	-----
	The cyclone list is created by initializing an array of zeros with a length equal to `MaxYear`.
	The severity distances for each cyclone year are then inserted at the corresponding index in the list.
	If no cyclone data is available for a particular year, the entry is set to [0, 0].
	"""
	
	cyc_lst = [0] * (MaxYear+1)  # create a list of zeros length equals to MaxYear
	for year, severity_distance in cyc_years.items():
		cyc_lst[int(year)] = severity_distance  # set the temperature at the corresponding year index
	
	for i in range(len(cyc_lst)):
		if cyc_lst[i] == 0:
			cyc_lst[i] = [0,0]
			
	return cyc_lst

# ###Rio create  ds list 
# def create_deposited_sediment_list(add_sedi_exp_per_year):
#     """
#     Create a list of additional deposited sediment values per year.

#     Parameters
#     ----------
#     add_sedi_exp_per_year : dict
#         A dictionary with keys as relative year indices and values as (suspended, deposited) tuples.

#     Returns
#     -------
#     list
#         A list where each index corresponds to a year and contains the additional deposited sediment value.
#         If no data is available for a particular year, the entry is set to 0.

#     Notes
#     -----
#     The list is created by initializing an array of zeros with a length equal to MaxYear+1.
#     The deposited sediment values for each year are then inserted at the corresponding index in the list.
#     """
#     deposited_lst = [0] * (MaxYear + 1)
#     for year, (suspended, deposited) in add_sedi_exp_per_year.items():
#         deposited_lst[int(year)] = deposited  # set the deposited sediment at the corresponding year index

#     return deposited_lst

# def eggs_decline_rate(dhw):
# 	"""
# 	Calculates the egg decline rate based on the degree heating weeks (DHW).

# 	Parameters
# 	----------
# 	dhw : integer
# 		The degree heating weeks (DHW) value.

# 	Returns
# 	-------
# 	float
# 		The egg decline rate.

# 	"""
# 	return 1 - 1 / (1 + eggs_decline_coefficient*np.exp(4-dhw))

# def colonies_spawning_decline_rate(dhw):
# 	"""
# 	Calculate the decline rate of colonies spawning as a function of degree heating weeks (DHW).

# 	Parameters
# 	----------
# 	dhw : integer
# 		The degree heating weeks.

# 	Returns
# 	-------
# 	float
# 		The decline rate of colonies spawning.

# 	"""
# 	return 1 - 1 / (1 + colonies_spawning_decline_coefficient * np.exp(4 - dhw))



# def get_PCM_rates_after_dhw(PCM_rates, dhw, branching_bleaching_rate, foliose_bleaching_rate, other_bleaching_rate):
# 	"""
# 	Calculate the PCM rates for each coral growth form given the degree heating weeks (DHW).

# 	Parameters
# 	----------
# 	PCM_rates : pandas DataFrame
# 		A DataFrame containing the PCM rates for each coral growth form and bin id.
# 	dhw : integer
# 		The degree heating weeks (DHW) value for the given year.

# 	Returns
# 	-------
# 	pandas DataFrame
# 		A DataFrame containing the updated PCM rates for each coral growth form and bin id based on the given DHW value.
# 	"""
	
# 	# compute the array of A values
# 	A = np.array([0.5*2**(i/(MaxBinId-1)) for i in range(MaxBinId)])
# 	# compute the exponential term
# 	exp_term = np.exp(4 - A * dhw)
	
# 	branching_bleaching_rate *= 1.05**(opts.dhw_counter-1)
# 	foliose_bleaching_rate *= 1.05**(opts.dhw_counter-1)
# 	other_bleaching_rate *= 1.05**(opts.dhw_counter-1)
	
# 	if growthOnly:
# 		pcm_rates_dhw = WCM_rates
# 	else:
# 		# compute the PCM rates for each coral growth form and bin id
# 		pcm_rates_dhw = pd.DataFrame(
# 									{
# 										'Branching': [(1 - PCM_rates['Branching'][j]) / (1 + branching_bleaching_rate*exp_term[j]) + PCM_rates['Branching'][j] for j in range(MaxBinId)],
# 										'Foliose': [(1 - PCM_rates['Foliose'][j]) / (1 + foliose_bleaching_rate*exp_term[j]) + PCM_rates['Foliose'][j] for j in range(MaxBinId)],
# 										'Other': [(1 - PCM_rates['Other'][j]) / (1 + other_bleaching_rate*exp_term[j]) + PCM_rates['Other'][j] for j in range(MaxBinId)],
# 									}
# 									)
# 	return pcm_rates_dhw

# ###Rio lets try this 
# def get_PCM_rates_after_DS_exp(PCM_rates, add_sedi_exp_per_year, year, sedi_exp_PCM_coeff):
#     """
#     Calculate updated Partial Colony Mortality (PCM) rates for each coral type based on deposited sediment exposure.
#     Ensures PCM rates are clipped between 0 and 1.

#     This version uses a linear relationship:
#         new_rate = base_rate + (coefficient x additional deposited_sediment)

#     Parameters:
#     - PCM_rates: pd.DataFrame with columns ['Branching', 'Foliose', 'Other'] representing base PCM rates.
#     - add_sedi_exp_per_year: dict with keys as relative year indices and values as (suspended, deposited) tuples.
#     - year: int, relative year index (e.g., 0 for 2005).
#     - sedi_exp_PCM_coeff: dict with linear coefficients for each coral type.

#     Returns:
#     - updated_PCM_rates: pd.DataFrame with adjusted PCM rates.
#     """
#     import pandas as pd

#     pcm_rates_ds = pd.DataFrame(columns=PCM_rates.columns)
#     add_deposited_sediment = add_sedi_exp_per_year.get(year, (0, 0))[1]

#     for coral_type in PCM_rates.columns:
#         coeff = sedi_exp_PCM_coeff.get(coral_type, 0)
#         adjusted_rates = []
#         for base_rate in PCM_rates[coral_type]:
#             # Ensure PCM is always between 0 and 1
#             adjusted_rate = base_rate + coeff * add_deposited_sediment
#             adjusted_rate = max(0, min(adjusted_rate, 1))
#             adjusted_rates.append(adjusted_rate)
#         pcm_rates_ds[coral_type] = adjusted_rates

#     return pcm_rates_ds

# def get_GR_after_ss(current_add_suspended_sediment, gr_sedi_sus_coeff):
# 	"""
# 	Calculate the growth rate after considering the effect of suspended sediment.
# 	Parameters:
# 	-----------
# 	current_add_suspended_sediment : float
# 		The current amount of added suspended sediment.
# 	gr_sedi_sus_coeff : dict
# 		A dictionary containing the growth rate coefficients for each coral type.
# 	Returns:
# 	--------
# 	growth_rate_ss : dict
# 		A dictionary containing the updated growth rates for each coral type after considering the effect of suspended sediment.
# 	Notes:
# 	------
# 	This function calculates the growth rate for each coral type (Branching, Foliose, Other) after considering the effect of suspended sediment.
# 	The growth rate is adjusted based on the amount of suspended sediment and the corresponding growth rate coefficient for each coral type.
# 	The calculations are performed using an exponential decay function.
# 	"""

# 	if not enable_sediment_exposure:
# 		return growth_rate

# 	else:
# 		growth_rate_ss = {i: growth_rate[i] * np.exp(-gr_sedi_sus_coeff[i] * current_add_suspended_sediment) for i in coral_type}
# 		return growth_rate_ss


# def get_WCM_rates_after_cyclones(WCM_rates, cyclone_severity_level, distance_to_cyclone):
# 	"""
# 	Calculate the WCM rates during cyclone events.

# 	Parameters:
# 	-----------
# 	WCM_rates : DataFrame
# 		The WCM rates for branching, foliose, and other coral types.
# 	cyclone_severity_level : float
# 		The severity level of the cyclone event.
# 	distance_to_cyclone : float
# 		The distance to the cyclone event.

# 	Returns:
# 	--------
# 	wcm_rates_cyc : DataFrame
# 		The updated WCM rates during cyclone events.

# 	Notes:
# 	------
# 	This function calculates the WCM rates for branching, foliose, and other coral types during cyclone events.
# 	The WCM rates are adjusted based on the severity level of the cyclone and the distance to the cyclone event.
# 	The calculations are performed using exponential decay functions.

# 	"""
# 	if not cyclone:
# 		return WCM_rates
	
# 	else:
# 		cyclone_severity_level = cyclone_severity_level*2


# 		# Fix: Create arrays that match MaxBinId exactly
# 		pp = np.linspace(1, MaxBinId+1, MaxBinId)  # Ensures length = MaxBinId
# 		bins = np.array([p*cyclone_bin_coefficient for p in pp])
		
# 		exp_term_branching = cyclone_severity_level*np.exp(-distance_to_cyclone/bins/cyclone_bin_coefficient)
# 		exp_term_foliose = cyclone_severity_level*np.exp(-distance_to_cyclone/bins/cyclone_bin_coefficient)
# 		exp_term_other = cyclone_severity_level*np.exp(-distance_to_cyclone/bins/cyclone_bin_coefficient)


# 		# wcm_rates_cyc = pd.DataFrame(
# 		# 								{
# 		# 									'Branching': [1 - 1 / (1 + branching_cyclone_coefficient * exp_term_branching[j]) + WCM_rates['Branching'][j] for j in range(MaxBinId)],
# 		# 									'Foliose': [1 - 1 / (1 + foliose_cyclone_coefficient * exp_term_foliose[j]) + WCM_rates['Foliose'][j] for j in range(MaxBinId)],
# 		# 									'Other': [1 - 1 / (1 + other_cyclone_coefficient * exp_term_other[j]) + WCM_rates['Other'][j] for j in range(MaxBinId)],
# 		# 								}
# 		# 								)
# 		wcm_rates_cyc = pd.DataFrame({
#             'Branching': [1 - 1 / (1 + branching_cyclone_coefficient * exp_term_branching[j]) + WCM_rates['Branching'][j] for j in range(MaxBinId)],
#             'Foliose': [1 - 1 / (1 + foliose_cyclone_coefficient * exp_term_foliose[j]) + WCM_rates['Foliose'][j] for j in range(MaxBinId)],
#             'Other': [1 - 1 / (1 + other_cyclone_coefficient * exp_term_other[j]) + WCM_rates['Other'][j] for j in range(MaxBinId)],
#         })
		
# 		return wcm_rates_cyc

# ### end of moved in from utils



# instantiate options
opts = CoralOptions()

# ###
# if linear_decay_growth_rate:
#     rate_of_decline = np.array([1 if i == 0 else 1 - (i - 1) * opts.gr_slope for i in range(MaxBinId)])
# else:
#     rate_of_decline = np.array([np.exp(-opts.gr_slope * binId) for binId in range(MaxBinId)])
# instantiate options
opts = CoralOptions()

# Ensure a deterministic default gr_slope is available to build module-level rate_of_decline and growth_rate.
# This default is only used to create the initial `growth_rate` object; the randomized gr_slope used per-run
# will be set inside initialize_coral() and/or run_yearly_change().
_default_gr_slope = 0.0340
_effective_gr_slope = _default_gr_slope if getattr(opts, 'gr_slope', None) is None else opts.gr_slope

if linear_decay_growth_rate:
    rate_of_decline = np.array([1 if i == 0 else 1 - (i - 1) * _effective_gr_slope for i in range(MaxBinId)])
else:
    rate_of_decline = np.array([np.exp(-_effective_gr_slope * binId) for binId in range(MaxBinId)])
    ###
if use_custom_growth_rate:
    growth_rate_branching = growth_coefficient_branching * custom_growth_rate_branching
    growth_rate_foliose = growth_coefficient_foliose * custom_growth_rate_foliose
    growth_rate_other = growth_coefficient_other * custom_growth_rate_other
else:
    growth_rate_branching = 2 * default_growth_rate_branching
    growth_rate_foliose = 2 * default_growth_rate_foliose
    growth_rate_other = 2 * default_growth_rate_other

growth_rate = pd.DataFrame({
    'Branching': growth_rate_branching * rate_of_decline,
    'Foliose':   growth_rate_foliose   * rate_of_decline,
    'Other':     growth_rate_other     * rate_of_decline,
})

output_folder = 'output'
os.makedirs(output_folder, exist_ok=True)