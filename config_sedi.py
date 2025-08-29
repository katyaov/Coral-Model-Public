import os
import random

import pandas as pd
import numpy as np
import warnings
from user_inputs import *

# warnings.filterwarnings("ignore", category=RuntimeWarning, message="overflow encountered in double_scalars")
# warnings.resetwarnings()
# warnings.filterwarnings(action='ignore', category=UserWarning, module='openpyxl')

years = list(range(year_end - year_start + 1)) 

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

if use_custom_growth_rate:
    growth_rate_dict
else:
    growth_rate_dict = {
        'Branching': default_growth_rate_branching,
        'Foliose': default_growth_rate_foliose,
        'Other': default_growth_rate_other
    }


# Grouped growth rate coefficients into a dictionary
growth_coefficients = {
    'Branching': 2,
    'Foliose': 2,
    'Other': 2
}

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


############# Coral Options Orginal location ############# 
class CoralOptions:
    def __init__(self):
        self.upper_diameter = MaxBinId * binSize
        self.growth_parameter = 0.5
        self.reef_area = reef_area
        self.reef_shape = reef_shape
        self.brooder_cover = initial_brooder_cover
        self.spawner_cover = initial_spawner_cover
        self.eggs_density = [egg_density_spawner_branching_foliose, egg_density_spawner_other]
        self.eggs_spawning_rate = [random.uniform(0.63,0.82), random.uniform(0.55,0.67)]
        self.eggs_fertilisation_rate = random.uniform(0.41,0.69) #
        if linear_decay_growth_rate:
            self.gr_slope = random.uniform(0.005, 0.045)
        else:
            self.gr_slope = random.uniform(0.05,1)
        self.initial_benthic_cover_dict = {
            "total": hard_substrate_cover + dead_coral_cover + CCA_cover + turfing_algae_cover + macro_algae_cover + rubble_cover + sediment_cover,
            "available_substrate": hard_substrate_cover + turfing_algae_cover + CCA_cover + dead_coral_cover,
            "hard_substrate": hard_substrate_cover,
            "dead_coral": dead_coral_cover,
            "CCA": CCA_cover,
            "turfing_algae": turfing_algae_cover,
            "macro_algae": macro_algae_cover,
            "rubble": rubble_cover,
            "sediment": sediment_cover
        }
        self.current_coral_cover = initial_coral_cover.copy()
        self.current_total_coral_cover = initial_total_coral_cover
        self.yearly_population_df_list = []
        self.yearly_surface_area_df_list = []
        self.current_total_coral_area_m2 = initial_total_coral_cover * reef_area / 100
        self.current_branching_total_area_m2 = initial_coral_cover['Branching'] * reef_area / 100
        self.current_foliose_total_area_m2 = initial_coral_cover['Foliose'] * reef_area / 100
        self.current_other_total_area_m2 = initial_coral_cover['Other'] * reef_area / 100
        self.available_substrate_percentage = self.initial_benthic_cover_dict['available_substrate']
        self.available_substrate_m2 = self.available_substrate_percentage * reef_area / 100
        self.unavailable_substrate_percentage = macro_algae_cover + rubble_cover + sediment_cover
        self.unavailable_substrate_m2 = self.unavailable_substrate_percentage * reef_area / 100
        self.maximum_achievable_substrate_percentage = 100 - self.unavailable_substrate_percentage


opts = CoralOptions()

# Sediment data processing

# Convert actual years to relative years (0, 1, 2, ...)
# This dictionary uses relative year as key for model calculations
sediment_years_months = {
    (int(row['Year']) - year_start, int(row['Month'])): [row['Suspended_sediment'], row['Deposited_sediment']]
    for _, row in sediment_df.iterrows()
    if pd.notna(row['Year']) and pd.notna(row['Month']) and pd.notna(row['Suspended_sediment']) and pd.notna(row['Deposited_sediment'])
}

# For model calculations, use relative years everywhere
years = list(range(year_end - year_start + 1))  # 0, 1, ..., N
bins = list(range(MaxBinId))

# For outputs/plots, you can always convert back:
actual_years = [year_start + year for year in years]

# Calculate additional sediment above baseline values (internal: relative years)
def calculate_additional_sediment():
    """
    Returns a dictionary with keys (relative_year, month) and values [additional_suspended, additional_deposited].
    Values are non-negative (minimum 0), scaled by sediment_susceptibility.
    """
    additional_sediment = {}
    for (year, month), values in sediment_years_months.items():
        suspended, deposited = values
        add_suspended = max(suspended - baseline_suspended_sediment, 0) * sediment_susceptibility
        add_deposited = max(deposited - baseline_deposited_sediment, 0) * sediment_susceptibility
        additional_sediment[(year, month)] = [add_suspended, add_deposited]
    return additional_sediment

additional_sediment_dict = calculate_additional_sediment()

#sediment exposure coefficients for processes
#sediment exposure growth relationships for each morphology
# used to adjust growth rate = growth rate value * (add_suspended * sedi_exp_growth_coeff)
sedi_exp_growth_coeff = {
    'Branching': -0.997,
    'Foliose': -0.272, 
    'Other': -0.533
}         

#sediment exposure partial mortality relationships for each morphology
sedi_exp_PCM_coeff = {
    'Branching': 0.3296,
    'Foliose': 0.0724, 
    'Other': 0.1645         
}

#sediment exposure settlement relationships for spawners and brooders
sedi_exp_settlement_coeff = {
    'spawner': -1.0609,
    'brooder': -0.2129      
}

#sediment exposure fertilisation relationships for spawners and brooders
sedi_exp_fertilisation_coeff = {
    'spawner': -0.6232,
    'brooder': 1   # this is a placeholder, as brooder fertilisation is not affected by sediment exposure  
}

#applying sediment expsoure coefficents on processes
#process: growth rate 

def calculate_monthly_adjusted_growth_rate(morphology, growth_rate_dict, additional_suspended):
    """
    Returns the monthly growth rate for a given morphology,
    adjusted by additional suspended sediment and the sediment exposure growth coefficient.
    """
    if enable_sediment_exposure:
        monthly_growth_rate = (growth_rate_dict / 12) * (1 + additional_suspended * sedi_exp_growth_coeff[morphology] / 100)
    else:
        monthly_growth_rate = growth_rate_dict / 12
    return monthly_growth_rate

def calculate_annual_growth_rate_SS(morphology, growth_rate_dict, additional_sediment_dict):
    """
    Calculates the annual growth rate for each year for a given morphology group.
    If sediment exposure is enabled, sums the monthly adjusted growth rates for each year.
    If not, returns the base growth rate for every year.
    Returns a dictionary: {year: total_annual_growth_rate}
    """
    annual_g_rates_SS = {}
    years = set(year for (year, _) in additional_sediment_dict.keys())
    for year in years:
        if enable_sediment_exposure:
            # Sum monthly adjusted growth rates for this year
            total = 0
            for month in range(1, 13):
                add_suspended = additional_sediment_dict.get((year, month), [0, 0])[0]
                monthly_rate = calculate_monthly_adjusted_growth_rate(morphology, growth_rate_dict, add_suspended)
                total += monthly_rate
            annual_g_rates_SS[year] = total
        else:
            # No sediment effect: use base growth rate
            annual_g_rates_SS[year] = growth_rate_dict
    return annual_g_rates_SS

# Calculate the rate of decline for growth rates based on the specified linear or exponential decay
opts = CoralOptions() 

if linear_decay_growth_rate:
    rate_of_decline = np.array([1 if i==0 else 1-(i-1) * opts.gr_slope for i in range(MaxBinId)])

else:
    rate_of_decline = np.array([np.exp(-opts.gr_slope * binId) for binId in range(MaxBinId)])

# Calculate annual growth rates for each morphology
#additional_sediment_dict = calculate_additional_sediment()



# Calculate annual growth rates for each coral type using the correct function
annual_g_rates_SS = {}
for morphology in coral_type:
    annual_g_rates_SS[morphology] = calculate_annual_growth_rate_SS(
        morphology,
        growth_rate_dict[morphology],
        additional_sediment_dict
    )

# Create a DataFrame to hold growth rates per bin per year for each morphology
# Create a DataFrame to hold growth rates per bin per year for each morphology
growth_rate_records_SS = []
for year in years:
    Year = year_start + year  # for output only
    for bin_id in bins:
        decline = rate_of_decline[bin_id]
        record = {'year': year, 'Year': Year, 'bin_id': bin_id}  # keep both for convenience
        for morphology in coral_type:
            record[morphology] = (
                annual_g_rates_SS[morphology].get(year, 0)
                * growth_coefficients[morphology]
                * decline
            )
        growth_rate_records_SS.append(record)
growth_rate_SS = pd.DataFrame(growth_rate_records_SS)
growth_rate_SS.set_index(['year', 'bin_id'], inplace=True)  # index by relative year for model logic

# For outputs, you can always add 'Year' column back:
growth_rate_SS['Year'] = growth_rate_SS.index.get_level_values('year') + year_start

output_folder = 'output'
os.makedirs(output_folder, exist_ok=True)

#make a dictionary of growth rates for each morphology for each year
#apply this if sedi exposure enabled
growth_rate_SS_dict = {
    'Branching': growth_rate_SS['Branching'].groupby(level=0).sum().to_dict(),
    'Foliose': growth_rate_SS['Foliose'].groupby(level=0).sum().to_dict(),
    'Other': growth_rate_SS['Other'].groupby(level=0).sum().to_dict()
}

#process: fertilisation rate
# fertilisation rate is adjusted by additional suspended sediment and the sediment exposure fertilisation coefficient
eggs_fertilisation_rate = random.uniform(0.41,0.69)

if enable_sediment_exposure:
    eggs_fertilisation_SS_rate = {}
    if spawning_month is not None:
        # Spawning month known: use sediment from that month
        for year in years:
            add_suspended = additional_sediment_dict.get((year, spawning_month), [0, 0])[0]
            adjustment = 1 + (sedi_exp_fertilisation_coeff['spawner'] * add_suspended) / 100
            eggs_fertilisation_SS_rate[year] = eggs_fertilisation_rate * adjustment
    else:
        # Spawning month unknown: use sediment from a random month each year
        import random
        for year in years:
            # Get all months available for this year
            months = [month for (y, month) in additional_sediment_dict.keys() if y == year]
            if months:
                rand_month = random.choice(months)
                add_suspended = additional_sediment_dict.get((year, rand_month), [0, 0])[0]
            else:
                add_suspended = 0
            adjustment = 1 + (sedi_exp_fertilisation_coeff['spawner'] * add_suspended) / 100
            eggs_fertilisation_SS_rate[year] = eggs_fertilisation_rate * adjustment
else:
    eggs_fertilisation_SS_rate = {year: eggs_fertilisation_rate for year in years}

# Create a dictionary of fertilisation rates for each year (not per coral type)
fertilisation_SS_rate_dict = eggs_fertilisation_SS_rate 

# Process: settlement rate
# Settlement rate is adjusted by additional deposited sediment and the sediment exposure settlement coefficient for spawners and brooders if enable sediment exposure:True if False default settlemnt rate is used .
###???? actually settlement is only applied to spawners not brooders in existing model structure
default_settlement_rate_spawner = random.uniform(0.41, 0.69)
default_settlement_rate_brooder = random.uniform(0.41, 0.69)

settlement_rate_DS_dict = {}

if enable_sediment_exposure:
    settlement_rate_DS_dict['spawner'] = {}
    settlement_rate_DS_dict['brooder'] = {}
    for year in years:
        # Spawner: use spawning month if known, else random month
        if spawning_month is not None:
            add_deposited = additional_sediment_dict.get((year, spawning_month), [0, 0])[1]
        else:
            months = [month for (y, month) in additional_sediment_dict.keys() if y == year]
            if months:
                rand_month = random.choice(months)
                add_deposited = additional_sediment_dict.get((year, rand_month), [0, 0])[1]
            else:
                add_deposited = 0
        adjustment_spawner = 1 + (sedi_exp_settlement_coeff['spawner'] * add_deposited) / 100
        settlement_rate_DS_dict['spawner'][year] = default_settlement_rate_spawner * adjustment_spawner

        # Brooder: use average additional deposited sediment for the year
        year_deposited = [values[1] for (y, m), values in additional_sediment_dict.items() if y == year]
        avg_deposited = np.mean(year_deposited) if year_deposited else 0
        adjustment_brooder = 1 + (sedi_exp_settlement_coeff['brooder'] * avg_deposited) / 100
        settlement_rate_DS_dict['brooder'][year] = default_settlement_rate_brooder * adjustment_brooder
else:
    # If sediment exposure is disabled, use default rates for all years
    settlement_rate_DS_dict['spawner'] = {year: default_settlement_rate_spawner for year in years}
    settlement_rate_DS_dict['brooder'] = {year: default_settlement_rate_brooder for year in years}

# Process: partial mortality rate
# Partial mortality rate is adjusted by additional deposited sediment and the sediment exposure partial mortality coefficient for each morphology if enable sediment exposure:True if False default partial mortality rate is used.
# Partial mortality rates are distributed across the bins, so we need to adjust them accordingly.
# Create a DataFrame to hold the adjusted partial mortality rates for each morphology

# If sediment exposure is disabled, use default or custom partial mortality rates

if not use_custom_partial_mortality_rate:
    # per bin size 5-95
    partial_mortality_rates_branching = [1.63, 1.91, 2.19, 2.47, 2.75, 3.03, 3.30, 3.58, 3.86, 4.14, 4.42, 4.70, 4.98, 5.25, 5.53, 5.81, 6.09, 6.37, 6.65, 6.75]
    partial_mortality_rates_foliose = [1.17, 1.36, 1.56, 1.76, 1.96, 2.16, 2.36, 2.56, 2.76, 2.96, 3.16, 3.35, 3.55, 3.75, 3.95, 4.15, 4.35, 4.55, 4.75, 4.8]
    partial_mortality_rates_other = [1.17, 1.36, 1.56, 1.76, 1.96, 2.16, 2.36, 2.56, 2.76, 2.96, 3.16, 3.35, 3.55, 3.75, 3.95, 4.15, 4.35, 4.55, 4.75, 4.8]
else:
    if len(custom_partial_mortality_rates_branching) != MaxBinId or len(custom_partial_mortality_rates_foliose) != MaxBinId or len(custom_partial_mortality_rates_other) != MaxBinId:
        raise ValueError(f"All lists must have a length of {MaxBinId}.")
    else:
        partial_mortality_rates_branching = custom_partial_mortality_rates_branching
        partial_mortality_rates_foliose = custom_partial_mortality_rates_foliose
        partial_mortality_rates_other = custom_partial_mortality_rates_other

# Output a dictionary called pmr_without_sedi_exp - pmr for coral type and bin
pmr_without_sedi_exp = {
    'Branching': partial_mortality_rates_branching,
    'Foliose': partial_mortality_rates_foliose,
    'Other': partial_mortality_rates_other
}

### Adjust partial mortality rates based on sediment exposure if enabled
if enable_sediment_exposure:
    # Calculate monthly adjusted partial mortality rates for each coral type 
    monthly_pcm = {morph: {} for morph in coral_type}
    for morphology in coral_type:
        for (year, month), values in additional_sediment_dict.items():
            add_deposited = values[1]
            # Adjust each bin's pmr for this month (convert annual to monthly by dividing by 12)
            adjusted_bin_rates = [
                pmr_without_sedi_exp[morphology][bin_id] / 12 * (1 + sedi_exp_PCM_coeff[morphology] * add_deposited / 100)
                for bin_id in bins
            ]
            monthly_pcm[morphology][(year, month)] = adjusted_bin_rates

    # Aggregate monthly rates to annual rates per bin (sum over months)
    annual_rates_matrix = np.zeros((len(bins), len(coral_type)))
    for morph_idx, morphology in enumerate(coral_type):
        for bin_idx, bin_id in enumerate(bins):
            annual_rates = []
            for year in years:
                rates_this_year = [
                    monthly_pcm[morphology].get((year, month), [pmr_without_sedi_exp[morphology][bin_id] / 12])[bin_id]
                    for month in range(1, 13)
                ]
                valid_rates = [r for r in rates_this_year if r is not None]
                if valid_rates:
                    annual_rate = np.sum(valid_rates)
                else:
                    annual_rate = pmr_without_sedi_exp[morphology][bin_id]
                annual_rates.append(annual_rate)
            annual_rates_matrix[bin_idx, morph_idx] = np.mean(annual_rates)
    PCM_rates_DS = pd.DataFrame(annual_rates_matrix, index=bins, columns=coral_type)
else:
    # If sediment exposure is disabled use pmr_without_sedi_exp
    PCM_rates = pd.DataFrame(pmr_without_sedi_exp)
    

####################THIS IS BAD BUT IT LETS THE CODE RUN WILL FIX LATER ##########################
if not growthOnly: #
    
    WCM_rates = pd.DataFrame({
                'Branching': [wcm/100 for wcm in wcm_branching],
                'Foliose': [wcm/100 for wcm in wcm_foliose],
                'Other': [wcm/100 for wcm in wcm_other],
                })
    
    if not enable_sediment_exposure:
        PCM_rates = pd.DataFrame(pmr_without_sedi_exp)
    
    else:
        PCM_rates = PCM_rates_DS

else:
    # If growth only scenario, set WCM and PCM to zero
    WCM_rates = pd.DataFrame({
        'Branching': [0] * MaxBinId,
        'Foliose': [0] * MaxBinId,
        'Other': [0] * MaxBinId,
    })
    PCM_rates = WCM_rates


