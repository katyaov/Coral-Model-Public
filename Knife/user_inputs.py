## User input values                   
## All units are (cm) or (%) unless otherwise is mentioned          
#**********************************************************

growthOnly = False
no_recruitment = False
bleaching = True
cyclone = True

#-------------------------------------------------------------------------------------
# degree of heating weeks. specify which year and the dhw of that year in the dictionary below.
# for example if there is 4 dhw on the 5th year, 3 dhw on the 12th year and 12 dhw on the 20th year, dhw_years will be {5:4, 12:3, 20:12}
dhw_years = {14:12}

# specify which year and the severity and the distance of the cyclone in that year in the dictionary below.
# cyclone severity level 1 - 4. 1 minor severity to 4 catastrophic.
# distance to the cyclone in km
# for example if there is level 1 cyclone at 40 km on the 15th year, level 2 cyclone at 106 km on the 28th year, level 4 at 25km on the 35th year and level 3 at 258km on the 42nd year, cyclone_years will be {15:[1,40], 28:[2,106], 35:[4,25], 42:[3,258]}
cyclone_years = {1:[5,100]}
# choose from ['protected','semiprotected','exposed']
reef_exposure = 'semiprotected'


#-------------------------------------------------------------------------------------
#Rugosity
Initial_Rugosity          = 1.5

#Total reef area (m2)
reef_area                 = 10000
reef_shape                = 5 # 1-12 based of Black et al 1990

#start and end years
year_start                = 2010
year_end                  = 2024
MaxYear = year_end - year_start        # Number of years we want to calculate

#-------------------------------------------------------------------------------------
# benthic cover (%)
hard_substrate_cover = 1.3
dead_coral_cover= 1.3
CCA_cover = 16.7
turfing_algae_cover = 41.1
macro_algae_cover = 13.2
rubble_cover = 1
sediment_cover = 1

# initial_brooder_cover = 4.61
initial_brooder_cover = 4.2
# initial_spawner_cover = [43.8, 16.6]  # the first element is B+F and the second element is O
initial_spawner_cover = [8.5,11.7]  # the first element is B+F and the second element is O

# initial_coral_cover = {'Branching':7.38, 'Foliose':41.03, 'Other':16.6}
initial_coral_cover = {'Branching':10.7, 'Foliose':2, 'Other':11.7}
initial_total_coral_cover = sum(initial_coral_cover.values())

#-------------------------------------------------------------------------------------
# choose between using your own custom parameters and the default parameters. To use
# your own custom parameters set the use_custom variable to True
#-------------------------------------------------------------------------------------
use_custom_coral_population_size_distribution = False
# if use_custom_coral_population_size_distribution is set to True, give your population size distribution of each bins in percentage at year 0
# make sure the length of each list is the same for all the custom parameters
custom_PSD_T0 = {
    'Bins': [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100],
    'Branching': [0.0, 1.5, 19.0, 15.8, 11.7, 10.0, 8.3, 6.6, 4.9, 3.2, 2.5, 2.1, 2.0, 2.0, 1.9, 1.9, 1.8, 1.8, 1.6, 1.5],
    'Foliose': [0.0, 0.0, 16.5, 12.0, 11.2, 7.4, 7.2, 6.0, 6.4, 4.3, 3.8, 3.1, 3.0, 3.0, 2.9, 2.8, 2.7, 2.6, 2.6, 2.5],
    'Other': [7.8, 10.1, 23.4, 10.3, 9.7, 5.8, 5.7, 4.7, 5.3, 3.3, 2.9, 2.5, 2.2, 1.8, 1.5, 1.2, 0.9, 0.6, 0.3, 0.0]
}

#-------------------------------------------------------------------------------------
use_custom_partial_mortality_rate = False
# if use_custom_partial_mortality_rate is True, give your own partial colony mortality rates of each bins in percentage
# make sure the length of each list is the same for all the custom parameters
custom_partial_mortality_rates_branching = [0.0195, 0.0229, 0.0262, 0.0296, 0.0329, 0.0363, 0.0396, 0.0429, 0.0463, 0.0496, 0.0530, 0.0563, 0.0597, 0.0630, 0.0663, 0.0697, 0.0730, 0.0764, 0.0797, 0.081]
custom_partial_mortality_rates_foliose = [0.0139, 0.0163, 0.0187, 0.0211, 0.0235, 0.0259, 0.0281, 0.0307, 0.0330, 0.0354, 0.0378, 0.0402, 0.0426, 0.0450, 0.0474, 0.0498, 0.0521, 0.0545, 0.0569, 0.0576]
custom_partial_mortality_rates_other = [0.0139, 0.0163, 0.0187, 0.0211, 0.0235, 0.0259, 0.0281, 0.0307, 0.0330, 0.0354, 0.0378, 0.0402, 0.0426, 0.0450, 0.0474, 0.0498, 0.0521, 0.0545, 0.0569, 0.0576]

#-------------------------------------------------------------------------------------
use_custom_whole_mortality_rate = False
# if use_custom_whole_mortality_rate is True, give your own whole colony mortality rates of each bins in percentage
# make sure the length of each list is the same for all the custom parameters NOTE that this one here is for sensitivity analysis at 20% greater
custom_wcm_branching = [24, 17.6, 17.6, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12, 9.12]
custom_wcm_foliose = [24, 4.8, 4.8, 4.8, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4]
custom_wcm_other = [24, 4.8, 4.8, 4.8, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4, 2.4]

#-------------------------------------------------------------------------------------
use_custom_growth_rate = True

#custom growth rate values (cm/year)
custom_growth_rate_branching     = 3.7
custom_growth_rate_foliose        = 1.7
custom_growth_rate_other         = 0.5

growth_coefficient_branching = 2
growth_coefficient_foliose = 2
growth_coefficient_other = 2