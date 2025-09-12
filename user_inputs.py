## User input values                   
## All units are (cm) or (%) unless otherwise is mentioned 

##NAME OF THE REEF: 
## Geographic Location: 
##COMMENTS:
#**********************************************************
import pandas as pd

growthOnly = False
no_recruitment = True
number_of_iterations = 100 #you can choose how many times to run the model (100 times is recommended)

# choose from ['protected','semiprotected','exposed']
reef_exposure = 'protected'

#-------------------------------------------------------------------------------------
#Rugosity
Initial_Rugosity          = 1.2

#Total reef area (m2)
reef_area                 = 10000
reef_shape                = 11 # 1-12 based of Black et al 1990

#start and end years
year_start                = 2005
year_end                  = 2024

MaxYear = year_end - year_start        # Number of years we want to calculate

#-------------------------------------------------------------------------------------
# benthic cover (%)
hard_substrate_cover = 2.4
dead_coral_cover= 4
CCA_cover = 0.8
turfing_algae_cover = 36.1
macro_algae_cover = 36.8
rubble_cover = 4
sediment_cover = 5

# initial_brooder_cover = 4.61
initial_brooder_cover = 1
# initial_spawner_cover = [43.8, 16.6]  # the first element is B+F and the second element is O
initial_spawner_cover = [9.9,7]  # the first element is B+F and the second element is O

# initial_coral_cover = {'Branching':7.38, 'Foliose':41.03, 'Other':16.6}
initial_coral_cover = {'Branching':2.6, 'Foliose':7.3, 'Other':8}
initial_total_coral_cover = sum(initial_coral_cover.values())

#----------------------------------------------------------------------------------------
#Define average polyp size. Default value polyp_size = 0.2cm
polyp_size = 0.2

#-----------------------------------------------------------------------------------------
# Change the rates here to change the bleaching effects
# Smaller rates give higher decrease in coral covers - so the higher the number, the more resilient (defaults: branching = 10, foliose = 20, other = 40)
branching_bleaching_rate = 10
foliose_bleaching_rate = 20
other_bleaching_rate = 40

#-------------------------------------------------------------------------------------------

# Change the rates to change the cyclone effects. A smaller coefficient gives less cyclone impact
# coefficients should be between 0 and 1. It should always be less than 1 (default values: branching = 0.8, foliose = 0.5, other = 0.3)
branching_cyclone_coefficient_input = 0.8 
foliose_cyclone_coefficient_input = 0.5
other_cyclone_coefficient_input = 0.3

#-------------------------------------------------------------------------------------
# choose between using your own custom parameters and the default parameters. To use
# your own custom parameters, set the use_custom variable to True. If using ANY own parameters, include an Excel table filled using the custom_user_input template in the working directory
#-------------------------------------------------------------------------------------
use_custom_coral_population_size_distribution = True
use_custom_partial_mortality_rate = True
use_custom_whole_mortality_rate = True
use_custom_growth_rate = True
bleaching = False
cyclone = False
enable_sediment_exposure = True

# Load the Excel file
excel_path = 'coral_data_and_custom_parameters.xlsx'

# 1. Load real coral cover data
real_df = pd.read_excel(excel_path, sheet_name='Real_Cover')

# 2. Load PSD from 'Custom_PSD_T0'
psd_df = pd.read_excel(excel_path, sheet_name='Population_size_distribution')
custom_PSD_T0 = {
    'Bins': psd_df['Bins'].tolist(),
    'Branching': psd_df['Branching'].tolist(),
    'Foliose': psd_df['Foliose'].tolist(),
    'Other': psd_df['Other'].tolist()
}

# 3. Load Partial Mortality Rates
pmr_df = pd.read_excel(excel_path, sheet_name='Partial_Mortality')
custom_partial_mortality_rates_branching = pmr_df['Branching_PMR'].tolist()
custom_partial_mortality_rates_foliose = pmr_df['Foliose_PMR'].tolist()
custom_partial_mortality_rates_other = pmr_df['Other_PMR'].tolist()

# 4. Load Whole Colony Mortality Rates
wcm_df = pd.read_excel(excel_path, sheet_name='Whole_Mortality')
custom_wcm_branching = wcm_df['Branching_WCM'].tolist()
custom_wcm_foliose = wcm_df['Foliose_WCM'].tolist()
custom_wcm_other = wcm_df['Other_WCM'].tolist()

# 5. Load Growth Rates
growth_rate_df = pd.read_excel(excel_path, sheet_name='Growth_Rates')
growth_rate_dict = dict(zip(growth_rate_df['CoralType'], growth_rate_df['GrowthRate_cm_per_year']))
custom_growth_rate_branching = growth_rate_dict.get('Branching')
custom_growth_rate_foliose = growth_rate_dict.get('Foliose')
custom_growth_rate_other = growth_rate_dict.get('Other')

# 6. Load DHW Years
dhw_df = pd.read_excel(excel_path, sheet_name='DHW_Years')
# Convert to relative year index (0-based or 1-based if your model needs it)
dhw_years = {int(row['Year']) - year_start: row['DHW']
             for _, row in dhw_df.iterrows()
             if pd.notna(row['Year']) and pd.notna(row['DHW'])}

# 7. Load Cyclone Years
cyclone_df = pd.read_excel(excel_path, sheet_name='Cyclone_Years')
cyclone_years = {
    int(row['Year']) - year_start: [row['Severity'], row['Distance_km']]
    for _, row in cyclone_df.iterrows()
    if pd.notna(row['Year']) and pd.notna(row['Severity']) and pd.notna(row['Distance_km'])
}

# 8. Load Sediment Exposure
# Typical clear water oligatrophic reef has suspended sediment < 5 mg/L (<15NTU) (Zweifler et al., 2024) and deposited sediment < 10 mg/cm^-2/day (Rogers 1990, Dutra et al., 2006, Falsarella et al., 2025), these can be used to inform the default baseline values.
baseline_suspended_sediment = 5
baseline_deposited_sediment = 10

sediment_df = pd.read_excel(excel_path, sheet_name='Sediment_Exposure')
sedi_years = {
    ((int(row['Year']) - year_start),int(row['Month'])): [row['Suspended_sediment'], row['Deposited_sediment']]
    for _, row in sediment_df.iterrows()
    if pd.notna(row['Year'])  and pd.notna(row['Month']) and pd.notna(row['Suspended_sediment']) and pd.notna(row['Deposited_sediment'])
}


sediment_susceptibility = 1 # value from 0 to 1 that indicates how susceptible the reef is to sediment impacting its trajectory. Reefs that have a value of 0 are not susceptible to sediment, while reefs with a value of 1 are very susceptible to sediment. Default value is 1.

#Reproduction - these values are only required if enable_sediment_exposure is True
spawning_month_known = True # if spawning month is known, set to True. If not, set to False
spawning_month = 1 # if spawning month is known, set the month number (1-12). 

