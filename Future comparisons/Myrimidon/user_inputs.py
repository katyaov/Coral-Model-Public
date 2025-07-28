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
dhw_years = {15:12, 17:10, 22:15, 27:12} #just block out three last DHW for the future with no bleaching events

# specify which year and the severity and the distance of the cyclone in that year in the dictionary below.
# cyclone severity level 1 - 4. 1 minor severity to 4 catastrophic.
# distance to the cyclone in km
# for example if there is level 1 cyclone at 40 km on the 15th year, level 2 cyclone at 106 km on the 28th year, level 4 at 25km on the 35th year and level 3 at 258km on the 42nd year, cyclone_years will be {15:[1,40], 28:[2,106], 35:[4,25], 42:[3,258]}
cyclone_years = {2:[5,100]}
# choose from ['protected','semiprotected','exposed']
reef_exposure = 'semiprotected'


#-------------------------------------------------------------------------------------
#Rugosity
Initial_Rugosity          = 1.6

#Total reef area (m2)
reef_area                 = 10000
reef_shape                = 5 # 1-12 based of Black et al 1990

#start and end years
year_start                = 2009
year_end                  = 2037 #same file to be used for Myrmidon disturbances to 2024 and to 2037
MaxYear = year_end - year_start        # Number of years we want to calculate

#-------------------------------------------------------------------------------------
# benthic cover (%)
hard_substrate_cover = 0
dead_coral_cover= 0
CCA_cover = 10.5
turfing_algae_cover = 44.1
macro_algae_cover = 9.4
rubble_cover = 1
sediment_cover = 6.4

# initial_brooder_cover = 4.61
initial_brooder_cover = 2.6
# initial_spawner_cover = [43.8, 16.6]  # the first element is B+F and the second element is O
initial_spawner_cover = [5.7,20.3]  # the first element is B+F and the second element is O

# initial_coral_cover = {'Branching':7.38, 'Foliose':41.03, 'Other':16.6}
initial_coral_cover = {'Branching':5.7, 'Foliose':2.6, 'Other':20.3}
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
custom_partial_mortality_rates_branching = [0.0163, 0.0191, 0.0219, 0.0247, 0.0275, 0.0303, 0.0330, 0.0358, 0.0386, 0.0414, 0.0442, 0.0470, 0.0498, 0.0525, 0.0553, 0.0581, 0.0609, 0.0637, 0.0665, 0.0675]
custom_partial_mortality_rates_foliose = [0.0117, 0.0136, 0.0156, 0.0176, 0.0196, 0.0216, 0.0236, 0.0256, 0.0276, 0.0296, 0.0316, 0.0335, 0.0355, 0.0375, 0.0395, 0.0415, 0.0435, 0.0455, 0.0475, 0.048]
custom_partial_mortality_rates_other = [0.0117, 0.0136, 0.0156, 0.0176, 0.0196, 0.0216, 0.0236, 0.0256, 0.0276, 0.0296, 0.0316, 0.0335, 0.0355, 0.0375, 0.0395, 0.0415, 0.0435, 0.0455, 0.0475, 0.048]

#-------------------------------------------------------------------------------------
use_custom_whole_mortality_rate = False
# if use_custom_whole_mortality_rate is True, give your own whole colony mortality rates of each bins in percentage
# make sure the length of each list is the same for all the custom parameters
custom_wcm_branching = [20, 14.8, 14.8, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 7.6, 0]
custom_wcm_foliose = [20.0, 4.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 0]
custom_wcm_other = [20.0, 4.0, 4.0, 4.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 2.0, 0]

#-------------------------------------------------------------------------------------
use_custom_growth_rate = True

#custom growth rate values (cm/year)
custom_growth_rate_branching     = 3.7
custom_growth_rate_foliose        = 1.1
custom_growth_rate_other         = 0.25

growth_coefficient_branching = 2
growth_coefficient_foliose = 2
growth_coefficient_other = 2