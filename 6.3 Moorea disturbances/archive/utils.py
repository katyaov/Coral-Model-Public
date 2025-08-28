from config import *
import matplotlib.pyplot as plt

opts = CoralOptions()

def get_recruited_corals(available_substrate_percentage, pop_flag = True):
    '''
    Calculates the estimated area or population of different coral species that will recruit to a given area of substrate.

    Parameters
    ----------
    available_substrate_percentage : float
        The percentage of substrate available for colonization by coral recruits.
    pop_flag : bool, optional
        A flag to specify the return type of the function. If True, the function returns the population of the recruited coral species. If False, the function returns the estimated area of recruitment. Default is True.

    Returns
    -------
    list
        A list containing the estimated area or population of different coral species, depending on whether the pop_flag argument is True or False.

    '''
    
    # Calculate the available substrate area for brooders    
    brooder_cover_m2 = opts.brooder_cover*colonies_spawning_decline_rate(opts.current_dhw)*opts.reef_area/100
    brooder_cover_cm2_per_m2 = brooder_cover_m2 * 10000 /opts.reef_area
    
    # Calculate the number of polyps that can grow on the available substrate area
    polyp_size = 200 * 1e-4
    number_polyps = brooder_cover_cm2_per_m2/polyp_size
    number_polyps_per_cm2 = number_polyps/brooder_cover_cm2_per_m2
    
    # Calculate the number of planulae released per unit area
    number_planulae_released_per_m2 = number_polyps_per_cm2 * 0.05 * brooder_cover_cm2_per_m2 / 25
    
    # brooder mortality rates
    brooder_mortality_rate = [0.73,0.39,0.37,0.35]
    
    # Calculate the number of brooder recruits that survive
    available_substrate_m2 = available_substrate_percentage * opts.reef_area / 100
    current_total_coral_cover = 100 - opts.unavailable_substrate_percentage - available_substrate_percentage
    num_recruits_brooder = number_planulae_released_per_m2 * available_substrate_m2 *(1-(current_total_coral_cover/opts.maximum_achievable_substrate_percentage)**opts.growth_parameter)
    
    for rate in brooder_mortality_rate:
        num_recruits_brooder *= (1 - rate)
    
    # Calculate the surface area covered by 5cm coral recruits 
    binDiameter = binSize
    surfaceArea5cm_br_cm2 = area_parameter * np.pi * (binDiameter/2)**2 * num_recruits_brooder
    
    surfaceArea_brooder_m2 = surfaceArea5cm_br_cm2/10000
    surfaceArea_brooder_percentage = 100*surfaceArea_brooder_m2/opts.reef_area
            
    # Calculate the surface area covered by spawner recruits
    spawner_cover_m2 = [cover*opts.reef_area/100 for cover in opts.spawner_cover]
    number_of_eggs = [10000 * eggs_decline_rate(opts.current_dhw) * opts.eggs_density[i] * spawner_cover_m2[i] for i in range(len(spawner_cover_m2))]
    num_eggs_spawning = [number_of_eggs[i]*opts.eggs_spawning_rate[i]* colonies_spawning_decline_rate(opts.current_dhw) for i in range(len(number_of_eggs))]
    fertilised_eggs = [opts.eggs_fertilisation_rate*eggs for eggs in num_eggs_spawning]
    
    coeff_retained =  get_retention_rate()
    eggs_retained = [coeff_retained[i]*fertilised_eggs[i]for i in range(len(fertilised_eggs))]
    
    coeff_survived = [0.84*0.87*0.93*0.94*0.95*0.96*0.965*0.97,0.915**3*0.91]
    larvae_survived = [coeff_survived[i]*eggs_retained[i]for i in range(len(eggs_retained))]
        
    opts.larvae_coeff = get_settlement_rate(available_substrate_percentage)
    larvae_settled = [opts.larvae_coeff*i for i in larvae_survived]
    spawner_bf_rate = [random.uniform(0.02,0.08),0.81,0.93,0.88,0.9]
    spawner_ot_rate = [random.uniform(0.02,0.08),0.865,0.83,0.91,0.925]
        
    num_recruits_spawner_bf = larvae_settled[0]
    num_recruits_spawner_ot = larvae_settled[1]
    for i in range(len(spawner_bf_rate)):
        num_recruits_spawner_bf *= spawner_bf_rate[i]
        num_recruits_spawner_ot *= spawner_ot_rate[i]
        
    num_recruits_spawner = [num_recruits_spawner_bf , num_recruits_spawner_ot]
    surfaceArea5cm_spawner_cm2 = [area_parameter * np.pi*(binDiameter/2)**2*i for i in num_recruits_spawner]
    surfaceArea_spawner_m2 = [i/10000 for i in surfaceArea5cm_spawner_cm2]
    surfaceArea_spawner_percentage = [100*i/opts.reef_area for i in surfaceArea_spawner_m2]
    
    recruited_branching_area_m2 = surfaceArea_brooder_m2 + surfaceArea_spawner_m2[0] * opts.current_coral_cover['Branching']/(opts.current_coral_cover['Branching'] + opts.current_coral_cover['Foliose'])
    recruited_foliose_area_m2 = surfaceArea_spawner_m2[0] * opts.current_coral_cover['Foliose']/(opts.current_coral_cover['Branching'] + opts.current_coral_cover['Foliose'])
    recruited_other_area_m2 = surfaceArea_spawner_m2[1]
    
    recruited_branching_population = get_population_number_from_surface_area(0,recruited_branching_area_m2)
    recruited_foliose_population = get_population_number_from_surface_area(0,recruited_foliose_area_m2)
    recruited_other_population = get_population_number_from_surface_area(0,recruited_other_area_m2)
    
    total_recruitment_m2 = surfaceArea_brooder_m2 + sum(surfaceArea_spawner_m2)
    total_recruitment_perc = surfaceArea_brooder_percentage + sum(surfaceArea_spawner_percentage)
    
    if no_recruitment:
        return [0, 0, 0]
    
    else:
    
        if pop_flag:
            return [ int(recruited_branching_population), int(recruited_foliose_population), int(recruited_other_population) ]

        else:
            return [ recruited_branching_area_m2, recruited_foliose_area_m2, recruited_other_area_m2 ]


def get_population_number_from_surface_area(binId, surface_area):
    '''
    Calculates the estimated population number of a coral species based on its surface area.

    Parameters
    ----------
    binId : int
        An integer representing the bin identifier for the coral species.
    surface_area : float
        A floating-point number representing the surface area of the coral species.

    Returns
    -------
    population_number : int
        An integer representing the estimated population number of the coral species.
    '''

    # get the bin diameter based on the bin identifier
    binDiameter = get_bin_diameter(binId)
    
    # convert bin diameter unit to meters
    binDiameter /= 100
                
    # calculate the population number
    population_number = surface_area / area_parameter / np.pi / (binDiameter/2)**2
    
    
    return int(population_number)

        

def get_retention_rate():
    """
    Calculates the retention rates for coral recruitment based on the shape of the reef.

    Parameters
    ----------
    None

    Returns
    -------
    tuple
        A tuple containing two float values representing the retention rates for branching and other coral species, respectively.
    """
    
  #  if opts.reef_shape in [7,8,9]: #very high rate
    #    retention_rate_bf = retention_rates_8d[0]
     #   retention_rate_o = retention_rates_4d[0]

    if opts.reef_shape in [3, 4, 7, 8, 9, 10]: # high rates 
        retention_rate_bf = retention_rates_8d[1]
        retention_rate_o = retention_rates_4d[1]

    elif opts.reef_shape in [2, 5, 6, 11]: # medium rate
        retention_rate_bf = retention_rates_8d[2]
        retention_rate_o = retention_rates_4d[2]

    elif opts.reef_shape in [1, 12]: # low rate
        retention_rate_bf = retention_rates_8d[3]
        retention_rate_o = retention_rates_4d[3]

    else:
        print("Wrong user input for reef shape. Cannot recognize %s as a valid reef shape" , str(opts.reef_shape))
    
    return retention_rate_bf, retention_rate_o


def get_settlement_rate(available_substrate_percentage):
    """
    Calculates the settlement rate for coral larvae given the percentage of substrate available for colonization.

    Parameters
    ----------
    available_substrate_percentage : float
        The percentage of substrate available for colonization by coral recruits.

    Returns
    -------
    float
        The settlement rate for coral larvae.
    """
    
    available_substrate_percentage = available_substrate_percentage / 100
    # scale_factor to normalize the function to 0.05. 0.05 is the maximum settlement rate given on Nikki's spreadsheet
    scale_factor = 0.05/(np.exp(1)-1)
    settlement_rate = scale_factor*(np.exp(available_substrate_percentage)-1)

    # Generate white noise
    noise = random.uniform(-settlement_rate/2, settlement_rate/2)
    settlement_rate += noise
    
    return settlement_rate



def get_coral_cover_in_percentage(surface_area_df,coral_type):
    """
    Calculate the percentage of a specific coral type on the reef.

    Parameters
    ----------
    surface_area_df : pandas.DataFrame
        DataFrame containing surface areas of different coral types on the reef.
    coral_type : str
        Name of the coral type for which to calculate the percentage cover.

    Returns
    -------
    float
        Percentage of the specified coral type on the reef.
    """
    
    coral_cover = sum(surface_area_df[coral_type])
    return 100*coral_cover/opts.reef_area


def get_total_coral_cover_in_percentage(surface_area_df):
    """
    Calculates the total percentage coral cover on a reef based on the surface area of different coral types.

    Parameters
    ----------
    surface_area_df : pandas.DataFrame
        A dataframe containing the surface area of different coral types.

    Returns
    -------
    float
        The total percentage coral cover on the reef based on the input surface area data.
    """
    
    # Calculate the total surface area covered by each coral type
    coral_cover = {i: surface_area_df[i][:].sum() for i in coral_type}
    
    # Calculate the total percentage coral cover on the reef
    return 100*sum(coral_cover.values())/opts.reef_area



def plot_population_distribution(year, log=False):
    """
    Plots the population distribution of different coral types for a given year.

    Parameters
    ----------
    year : int
        The year for which the population distribution needs to be plotted.

    log : bool, optional
        If True, the y-axis scale will be set to logarithmic. Default is False.

    Returns
    -------
    None

    """
    
    # Get the population distribution data for the given year
    df = opts.yearly_population_df_list[year][1:]
    
    # Set up the x-axis (bin diameter)
    binId = np.array(range(1,MaxBinId))
    binDiameter = get_bin_diameter(binId)
    
    # Plot the data for each coral type
    plt.plot(binDiameter,df['Branching'], '-*',label = 'Branching')
    plt.plot(binDiameter,df['Foliose'], '-*',label = 'Foliose')
    plt.plot(binDiameter,df['Other'], '-*',label = 'Other')
    
    # Add title and axis labels
    plt.title(f'Population distribution of year {year}')
    plt.xlabel('Bin Diameter (cm)', fontsize = '15')
    plt.ylabel('Population number', fontsize = '15')
    if log:
        plt.yscale('log')
    # Add legend and display the plot
    plt.legend()
    plot_file = os.path.join(output_folder, 'pop_distribution.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()
    

def plot_population_distribution_in_percentage(year, log=False):
    """
    Plot the percentage population distribution of coral types for a given year.

    Parameters
    ----------
    year : int
        The year for which to plot the percentage population distribution.

    log : bool, optional
        If True, the y-axis scale will be set to logarithmic. Default is False.

    Returns
    -------
    None
    """
    
    df = opts.yearly_population_df_list[year]
    total_branching_pop = df['Branching'].sum()
    total_foliose_pop = df['Foliose'].sum()
    total_other_pop = df['Other'].sum()
    
    branching = 100 * df['Branching'] / total_branching_pop
    foliose = 100 * df['Foliose'] / total_foliose_pop
    other = 100 * df['Other'] / total_other_pop
    
    binId = np.array(range(0,MaxBinId))
    binDiameter = get_bin_diameter(binId)
    
    plt.plot(binDiameter,branching ,'-*',label = 'Branching')
    plt.plot(binDiameter,foliose ,'-*',label = 'Foliose')
    plt.plot(binDiameter,other,'-*',label = 'Other')
    plt.title(f'Percentage population distribution of year {year}')
    plt.xlabel('Bin Diameter (cm)', fontsize = '15')
    plt.ylabel('Percentage population number', fontsize = '15')
    if log:
        plt.yscale('log')
    plt.legend()
    plot_file = os.path.join(output_folder, 'Percentage_pop_distribution.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()
    
    
def plot_surface_area_distribution(year, log=False):
    """
    Plots the surface area distribution of different coral types in a given year.

    Parameters
    ----------
    year : int
        The year for which to plot the surface area distribution.

    log : bool, optional
        If True, the y-axis scale will be set to logarithmic. Default is False.

    Returns
    -------
    None.

    """
    
    # Get the surface area distribution data for the given year
    df = opts.yearly_surface_area_df_list[year]
    
    # Set up the x-axis (bin diameter)
    binId = np.array(range(0, MaxBinId))
    binDiameter = get_bin_diameter(binId)
    
    # Plot the data for each coral type
    plt.plot(binDiameter, 100 * df['Branching'] / opts.reef_area,'-*',label='Branching')
    plt.plot(binDiameter, 100 * df['Foliose'] / opts.reef_area, '-*',label='Foliose')
    plt.plot(binDiameter, 100 * df['Other'] / opts.reef_area, '-*',label='Other')
    
    # Add title and axis labels
    plt.title(f'Surface Area Distribution of Year {year}')
    plt.xlabel('Bin Diameter (cm)', fontsize='15')
    plt.ylabel('Percentage Contribution / Reef Area (%)', fontsize='15')
    if log:
        plt.yscale('log')
    # Add legend and display the plot
    plt.legend()
    plot_file = os.path.join(output_folder, 'percentage_area_distribution.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()
    

def plot_coral_type_areal_change(coral_type,log=False, *args):
    """
    Plot the areal change in coral type over time based on the provided arguments, while ensuring all years are within the specified range.

    Parameters
    ----------
    coral_type : str
        The type of coral to plot.
    log : bool, optional
        If True, the y-axis scale will be set to logarithmic. Default is False.
    *args : int
        Variable number of integers indicating the years to plot.

    Returns
    -------
    None

    """
    for year in args:
        if year > MaxYear:
            raise ValueError(f"Year {year} is greater than the maximum allowed year {MaxYear}.")
            
    # Set up the x-axis (bin diameter)
    binId = np.array(range(0,MaxBinId))
    binDiameter = get_bin_diameter(binId)
    for arg in args:
        df = opts.yearly_surface_area_df_list[arg][coral_type]
        
        # Plot the data for each coral type
        plt.plot(binDiameter,df,'-*',label = f'year = {arg}')
        
    
    # Add title and axis labels
    plt.title(f'Coral cover of {coral_type}')
    plt.xlabel('Bin Diameter (cm)', fontsize = '15')
    plt.ylabel(f'{coral_type} Area (m$^2$)', fontsize = '15')
    if log:
        plt.yscale('log')
    # Add legend and display the plot
    plt.legend()
    plot_file = os.path.join(output_folder, 'yearly_surface_area.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()

    
def plot_coral_type_population_change(coral_type, log=False, *args):
    """
    Plot the population change in coral type over time based on the provided arguments, while ensuring all years are within the specified range.

    Parameters
    ----------
    coral_type : str
        The type of coral to plot.
    log : bool, optional
        If True, the y-axis scale will be set to logarithmic. Default is False.
    *args : int
        Variable number of integers indicating the years to plot.

    Returns
    -------
    None

    """
    for year in args:
        if year > MaxYear:
            raise ValueError(f"Year {year} is greater than the maximum allowed year {MaxYear}.")
    # Set up the x-axis (bin diameter)
    binId = np.array(range(0,MaxBinId))
    binDiameter = get_bin_diameter(binId)
    for arg in args:
        df = opts.yearly_population_df_list[arg][coral_type]
        
        # Plot the data for each coral type
        plt.plot(binDiameter,df,'-*' ,label = f'year = {arg}')
        
    
    # Add title and axis labels
    plt.title(f'Coral cover of {coral_type}')
    plt.xlabel('Bin Diameter (cm)', fontsize = '15')
    plt.ylabel(f'{coral_type} population', fontsize = '15')
    if log:
        plt.yscale('log')
    # Add legend and display the plot
    plt.legend()
    plot_file = os.path.join(output_folder, 'yearly_population_change.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()
    

def get_initial_surface_area(PSD):
    """
    Returns the initial surface area of coral colonies based on the coral population size distribution (PSD) and current coral cover.
    Parameters
    ----------
    PSD : pandas DataFrame
        The coral population size distribution for different coral types in different size bins.

    Returns
    -------
    surface_area : pandas DataFrame
        A DataFrame containing the initial surface area of coral colonies for different coral types in different size bins.

    """
    
    # Calculate the surface area of coral colonies based on PSD and current coral cover
    surface_area = pd.DataFrame(
        {
            'Branching': [PSD['Branching'][j] * opts.current_coral_cover['Branching'] * opts.reef_area/100/100 for j in range(MaxBinId)],
            'Foliose': [PSD['Foliose'][j] * opts.current_coral_cover['Foliose'] * opts.reef_area/100/100 for j in range(MaxBinId)],
            'Other': [PSD['Other'][j] * opts.current_coral_cover['Other'] * opts.reef_area/100/100 for j in range(MaxBinId)],

        }
    )
    
    # Calculate recruitment
    recruitment = pd.DataFrame({'Branching': get_recruited_corals(opts.available_substrate_percentage, False)[0], 'Foliose': get_recruited_corals(opts.available_substrate_percentage, False)[1], 'Other': get_recruited_corals(opts.available_substrate_percentage, False)[2] }, index=[0])
    
    # Set initial values for year and total coral cover
    opts.year = 0
    opts.total_coral_cover_df = pd.DataFrame(columns=['Year', 'Branching_Area (%)', 'Foliose_Area (%)', 'Other_Area (%)', 'total_coral_cover (%)'])
    
    # Calculate and store the initial total coral cover
    yearly_total_coral_cover = pd.DataFrame({'Year':int(opts.year), 'Branching_Area (%)':opts.current_coral_cover['Branching'], 'Foliose_Area (%)':opts.current_coral_cover['Foliose'], 'Other_Area (%)':opts.current_coral_cover['Other'], 'total_coral_cover (%)': opts.current_total_coral_cover}, index=[0])
    opts.total_coral_cover_df = pd.concat([opts.total_coral_cover_df.loc[:], yearly_total_coral_cover]).reset_index(drop = True)
    
    return surface_area  


def estimate_initial_number_of_corals(x_i, reef_area, target_coral_cover):
    """
    Estimates the initial number of corals in the entire reef area based on the given number fraction, reef area,
    and target coral cover.

    Parameters:
    ----------
    - x_i: numpy array-like
        Number fraction of diameters representing the distribution of corals in different bins.
    - reef_area: float
        Total area of the reef in square meters.
    - target_coral_cover: float
        Target coral cover percentage of the reef area.

    Returns:
    ----------
    - N: int
        Estimated initial number of corals in the entire reef area.
    """

    # Generate a random initial estimate for the number of corals
    N = np.random.randint(1, 10000)

    # Calculate the number of corals per bin from the number fraction x_i and total number of corals N
    n_i = x_i * N / 100

    # Get the bin IDs and corresponding bin diameters
    binId = np.array(np.arange(0, MaxBinId))
    bin_diameter = get_bin_diameter(binId) / 100

    # Calculate the area of a single coral in each bin
    single_coral_area = area_parameter * np.pi * bin_diameter**2 / 4

    # Calculate the area of each bin based on the number of corals
    bin_area = n_i * single_coral_area

    # Estimate the coral cover from the calculated areas
    estimate_coral_cover = 100 * np.sum(bin_area) / reef_area

    # Iterate until the coral cover matches the target
    while abs(estimate_coral_cover - target_coral_cover) > 0.001:
        # Adjust the total number of corals based on the coral cover ratio
        N *= target_coral_cover / estimate_coral_cover

        # Recalculate the number of corals per bin
        n_i = x_i * N / 100

        # Recalculate the bin diameters
        binId = np.array(np.arange(0, MaxBinId))
        bin_diameter = get_bin_diameter(binId) / 100

        # Recalculate the area of a single coral in each bin
        single_coral_area = area_parameter * np.pi * bin_diameter**2 / 4

        # Recalculate the area of each bin based on the new number of corals
        bin_area = n_i * single_coral_area

        # Recalculate the estimated coral cover
        estimate_coral_cover = 100 * np.sum(bin_area) / reef_area

    # Round off the estimated number of corals to the nearest integer
    return np.round(N)


def get_initial_population(PSD):
    """
    Computes the initial population of each coral type given the initial surface area of each bin.

    Parameters
    ----------
    initial_surface_area_m2_df : pandas DataFrame
        A DataFrame containing the initial surface area of each bin for each coral type.

    Returns
    -------
    pandas DataFrame
        A DataFrame containing the initial population of each bin for each coral type.

    """
    branching_total_population = estimate_initial_number_of_corals(PSD['Branching'], reef_area, initial_coral_cover['Branching'])
    foliose_total_population = estimate_initial_number_of_corals(PSD['Foliose'], reef_area, initial_coral_cover['Foliose'])
    other_total_population = estimate_initial_number_of_corals(PSD['Other'], reef_area, initial_coral_cover['Other'])
    
#     population = pd.DataFrame(
#         {
#             'Branching': branching_total_population*np.array(PSD['Branching'])/100,
#             'Foliose': [get_population_number_from_surface_area(binId,initial_surface_area_m2_df['Foliose'][binId]) for binId in range(MaxBinId)],
#             'Other': [get_population_number_from_surface_area(binId,initial_surface_area_m2_df['Other'][binId]) for binId in range(MaxBinId)],

#         }
#     )
    
    population = pd.DataFrame(
        {
            'Branching': branching_total_population*np.array(PSD['Branching'])/100,
            'Foliose': foliose_total_population*np.array(PSD['Foliose'])/100,
            'Other': other_total_population*np.array(PSD['Other'])/100,

        }
    )
    return population



def get_bin_diameter(binId):
    """
    Calculate the average diameter of a coral colony in a bin based on its ID.

    Parameters
    ----------
    binId : int
        The ID of the bin for which the diameter needs to be calculated.
    
    Returns
    -------
    float
        The average diameter of a coral colony in the bin in centimeters.

    """
    
    lowerBinRange = binId * binSize
    upperBinRange = (binId+1) * binSize
    
    binDiameter = np.sqrt(lowerBinRange**2/2 + upperBinRange**2/2)
    
    return binDiameter



def get_surface_area_from_population(binId,population):
    """
    Calculate the surface area of a coral population in a given bin, based on its population and bin ID.

    Parameters
    ----------
    binId : int
        The ID of the bin for which the surface area needs to be calculated.
    population : int
        The population of the coral population in the bin.

    Returns
    -------
    float
        The surface area of the coral population in the bin, in square meters.

    """
    global MaxBinId
    
    if binId == MaxBinId-1:
        lowerBinDiameter = binId * binSize
        upperBinDiameter = opts.upper_diameter
        binDiameter = np.sqrt(lowerBinDiameter**2/2 + upperBinDiameter**2/2)
    else:
        binDiameter = get_bin_diameter(binId)
    
    binDiameter /= 100
    surface_area = population * area_parameter*np.pi*(binDiameter/2)**2
    return surface_area


def get_surface_area(population_df):
    """
    Calculates the surface area of each coral type in each bin based on their populations.

    Parameters
    ----------
    population_df : pandas DataFrame
        A DataFrame containing the population of each coral type in each bin.

    Returns
    -------
    pandas DataFrame
        A DataFrame containing the surface area of each coral type in each bin.
    """

    surface_area = pd.DataFrame({
                'Branching': [get_surface_area_from_population(j,population_df['Branching'][j])  for j in range(0,MaxBinId)],
                'Foliose': [get_surface_area_from_population(j,population_df['Foliose'][j])  for j in range(0,MaxBinId)],
                'Other': [get_surface_area_from_population(j,population_df['Other'][j])  for j in range(0,MaxBinId)],
                })

    return surface_area


       
def initialize_coral():
    """
    Initialize the coral ecosystem at year = 0.

    Returns
    -------
    None.

    """
        
    opts.year = 0
    opts.dhw_lst = create_dhw_list(dhw_years)
    opts.current_dhw = opts.dhw_lst[opts.year]
    opts.cyc_lst = create_cyclone_list(cyclone_years)
    opts.current_cyc = opts.cyc_lst[opts.year]
    opts.current_coral_cover = initial_coral_cover.copy()
    opts.brooder_cover = initial_brooder_cover
    opts.spawner_cover = initial_spawner_cover
    opts.current_total_coral_cover = initial_total_coral_cover
    opts.yearly_total_coral_cover_df = pd.DataFrame({'Year':0, 
                                                'Branching_Area (%)':initial_coral_cover['Branching'], 
                                                'Foliose_Area (%)':initial_coral_cover['Foliose'], 
                                                'Other_Area (%)':initial_coral_cover['Other'], 
                                                'total_coral_cover (%)':initial_total_coral_cover}, index=[0])
    
    opts.current_benthic_cover = opts.initial_benthic_cover_dict.copy()
    opts.yearly_benthic_cover_df = pd.DataFrame({'Year':opts.year, 
                                          'total_benthic_cover (%)':opts.current_benthic_cover['total'], 
                                          'available_substrate (%)':opts.current_benthic_cover['available_substrate'], 
                                          'hard_substrate (%)':opts.current_benthic_cover['hard_substrate'], 
                                          'dead_coral (%)':opts.current_benthic_cover['dead_coral'], 
                                          'CCA (%)':opts.current_benthic_cover['CCA'], 
                                          'turfing_algae (%)':opts.current_benthic_cover['turfing_algae'], 
                                          'macro_algae (%)':opts.current_benthic_cover['macro_algae'], 
                                          'rubble (%)':opts.current_benthic_cover['rubble'], 
                                          'sediment (%)':opts.current_benthic_cover['sediment'], 
                                          'total_cc ':opts.current_total_coral_cover,
                                          'unavailable_sub':opts.unavailable_substrate_percentage,
                                          'tot':opts.available_substrate_percentage + opts.unavailable_substrate_percentage + opts.current_total_coral_cover, 
                                         }, index=[0])
    
    opts.current_population_df = get_initial_population(PSD_T0)
    opts.yearly_population_df_list = [opts.current_population_df]
    opts.current_surface_area_m2_df = get_surface_area(opts.current_population_df)
    opts.yearly_surface_area_df_list = [opts.current_surface_area_m2_df]
    opts.unavailable_substrate_percentage = opts.current_benthic_cover['macro_algae'] + opts.current_benthic_cover['rubble'] + opts.current_benthic_cover['sediment']
    opts.available_substrate_percentage = get_available_substrate()
    opts.maximum_achievable_substrate_percentage = 100 - opts.unavailable_substrate_percentage
    # PCM_rates_dhw = get_PCM_rates_after_dhw(PCM_rates,opts.current_dhw,branching_bleaching_rate, foliose_bleaching_rate, other_bleaching_rate)
    opts.upper_diameter = MaxBinId * binSize
        


def update_coral_parameters():
    """
    Update the current coral parameters based on the current surface area and population.

    Returns
    -------
    None.

    """
    
    for coral in coral_type:
        opts.current_coral_cover[coral] = get_coral_cover_in_percentage(opts.current_surface_area_df,coral)
    opts.current_total_coral_cover = sum(opts.current_coral_cover.values())
    current_df = pd.DataFrame({'Year':int(opts.year), 'Branching_Area (%)':opts.current_coral_cover['Branching'], 'Foliose_Area (%)':opts.current_coral_cover['Foliose'], 'Other_Area (%)':opts.current_coral_cover['Other'], 'total_coral_cover (%)': opts.current_total_coral_cover }, index=[0])
    opts.yearly_total_coral_cover_df = pd.concat([opts.yearly_total_coral_cover_df[:],current_df]).reset_index(drop = True)
    opts.available_substrate_percentage = get_available_substrate()
    opts.unavailable_substrate_percentage = get_unavailable_substrate()
    
    
    opts.brooder_cover, opts.spawner_cover[0], opts.spawner_cover[1] = get_brooder_spawner_cover(opts.current_coral_cover)
    
    old_coral_cover_perc = opts.yearly_total_coral_cover_df.iloc[opts.year-1]['total_coral_cover (%)']
    new_coral_cover_perc = opts.yearly_total_coral_cover_df.iloc[opts.year]['total_coral_cover (%)']
    change_total_coral_cover = new_coral_cover_perc - old_coral_cover_perc
    
    old_branching_coral_cover = opts.yearly_total_coral_cover_df.iloc[opts.year-1]['Branching_Area (%)']
    new_branching_coral_cover = opts.yearly_total_coral_cover_df.iloc[opts.year]['Branching_Area (%)']
    change_branching_cover = new_branching_coral_cover - old_branching_coral_cover
    old_foliose_coral_cover = opts.yearly_total_coral_cover_df.iloc[opts.year-1]['Foliose_Area (%)']
    new_foliose_coral_cover = opts.yearly_total_coral_cover_df.iloc[opts.year]['Foliose_Area (%)']
    change_foliose_cover = new_foliose_coral_cover - old_foliose_coral_cover
    old_other_coral_cover = opts.yearly_total_coral_cover_df.iloc[opts.year-1]['Other_Area (%)']
    new_other_coral_cover = opts.yearly_total_coral_cover_df.iloc[opts.year]['Other_Area (%)']
    change_other_cover = new_other_coral_cover - old_other_coral_cover
    
    if opts.current_cyc[0] != 0:     
        calculate_benthos_after_cyclone(change_branching_cover, change_foliose_cover, change_other_cover)
        
    elif opts.current_dhw != 0:
        calculate_benthos_after_bleaching(change_branching_cover, change_foliose_cover, change_other_cover)
    
    else:
        if change_branching_cover > 0:
            w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_branching_cover)
            opts.current_benthic_cover['hard_substrate'] -= w_hs
            opts.current_benthic_cover['dead_coral'] -= w_dc
            opts.current_benthic_cover['turfing_algae'] -= w_tf
                        
        else:
            opts.current_benthic_cover['dead_coral'] += abs(change_branching_cover)
            
        if change_foliose_cover > 0:
            w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_foliose_cover)
            opts.current_benthic_cover['hard_substrate'] -= w_hs
            opts.current_benthic_cover['dead_coral'] -= w_dc
            opts.current_benthic_cover['turfing_algae'] -= w_tf
                        
        else:
            opts.current_benthic_cover['dead_coral'] += abs(change_foliose_cover)
            
        if change_other_cover > 0:
            # total coral cover increases, the available substrate decreases
            w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_other_cover)
            opts.current_benthic_cover['hard_substrate'] -= w_hs
            opts.current_benthic_cover['dead_coral'] -= w_dc
            opts.current_benthic_cover['turfing_algae'] -= w_tf
                        
        else:
            opts.current_benthic_cover['dead_coral'] += abs(change_other_cover)
            
            
    # Every year 1/6 of rubble cover converts to dead coral
    opts.current_benthic_cover['rubble'] -= opts.current_benthic_cover['rubble'] / 6
    opts.current_benthic_cover['dead_coral'] += opts.current_benthic_cover['rubble'] / 6    
        
    reef_minus_total_corals = 100 - opts.current_total_coral_cover     
    opts.available_substrate_percentage = get_available_substrate()
    opts.unavailable_substrate_percentage = get_unavailable_substrate()
    total_substrate_without_corals = opts.available_substrate_percentage + opts.unavailable_substrate_percentage
    
    if total_substrate_without_corals != reef_minus_total_corals:
        multiplying_factor = reef_minus_total_corals / total_substrate_without_corals
        opts.current_benthic_cover['hard_substrate'] *= multiplying_factor
        opts.current_benthic_cover['dead_coral'] *= multiplying_factor
        opts.current_benthic_cover['CCA'] *= multiplying_factor
        opts.current_benthic_cover['turfing_algae'] *= multiplying_factor
        opts.current_benthic_cover['macro_algae'] *= multiplying_factor
        opts.current_benthic_cover['rubble'] *= multiplying_factor
        opts.current_benthic_cover['sediment'] *= multiplying_factor
        
    
    # opts.available_substrate_percentage = 100 - opts.current_total_coral_cover - opts.unavailable_substrate_percentage  
    opts.current_benthic_cover['total'] = opts.current_benthic_cover['hard_substrate'] + opts.current_benthic_cover['dead_coral'] + opts.current_benthic_cover['CCA'] + opts.current_benthic_cover['turfing_algae'] + opts.current_benthic_cover['macro_algae'] + opts.current_benthic_cover['rubble'] + opts.current_benthic_cover['sediment']
    # print(f'available_substrate_percentage {opts.available_substrate_percentage} and {turfing_algae}')#hard_substrate + dead_coral + CCA + turfing_algae}')
    current_bentic_cover = pd.DataFrame({'Year':opts.year, 
                                          'total_benthic_cover (%)':opts.current_benthic_cover['total'], 
                                          'available_substrate (%)':opts.available_substrate_percentage, 
                                          'hard_substrate (%)':opts.current_benthic_cover['hard_substrate'], 
                                          'dead_coral (%)':opts.current_benthic_cover['dead_coral'], 
                                          'CCA (%)':opts.current_benthic_cover['CCA'], 
                                          'turfing_algae (%)':opts.current_benthic_cover['turfing_algae'], 
                                          'macro_algae (%)':opts.current_benthic_cover['macro_algae'], 
                                          'rubble (%)':opts.current_benthic_cover['rubble'], 
                                          'sediment (%)':opts.current_benthic_cover['sediment'], 
                                          'total_cc ':opts.current_total_coral_cover,
                                          'unavailable_sub':opts.unavailable_substrate_percentage,
                                          'tot':opts.available_substrate_percentage + opts.unavailable_substrate_percentage + opts.current_total_coral_cover, 
                                         }, index=[0])
    opts.yearly_benthic_cover_df = pd.concat([opts.yearly_benthic_cover_df[:],current_bentic_cover]).reset_index(drop = True)
    
    

    
    
def count_new_population_per_bin(binId,population,growth_rate,pcm_rate,wcm_rate,current_total_coral_cover):
    """
    Calculate the new population of corals in a given bin, based on various growth parameters.

    Parameters
    ----------
    binId : int
        The ID of the bin for which to calculate the new population.
    population : float
        The current population of corals in the bin.
    growth_rate : int
        The growth rate of the corals.
    pcm_rate : float
        The percentage of the population that is affected by partial colony mortality (PCM).
    wcm_rate : float
        The percentage of the population that is affected by whole colony mortality (WCM).
    current_total_coral_cover : float
        The current total coral cover on the reef.

    Returns
    -------
    tuple
        A tuple of four floats representing the count of corals in four different categories based on their size:
        (count_lower, count_remain, count_upper, count_upper_upper).
    """
    
    lower_diameter = binSize * binId
    if binId == MaxBinId-1 :
        upper_diameter = opts.upper_diameter
    else:
        upper_diameter = (binId + 1) * binSize
    
    
    if population == 0:
        # if the bin has no corals, then there are no corals to grow or shrink
        # return 0
        return 0, 0, 0, 0
    
    else:
        
        arr = np.array(np.linspace(lower_diameter,upper_diameter,100))
        arr += growth_rate * (1 - (current_total_coral_cover / opts.maximum_achievable_substrate_percentage)**opts.growth_parameter)
        arr *= np.sqrt(1-pcm_rate)
        # arr *= np.sqrt(1-wcm_rate)
        
        if binId == MaxBinId-1:
            # since there are no upper bin, set the upper_diameter of the last bin to be the largest diameter of the coral.
            # the corals won't grow to any other larger bin. 
            upper_diameter = arr[-1]
            opts.upper_diameter = upper_diameter
            # print(f'opts.upper_diameter {opts.upper_diameter}')
            
        count_lower = 0
        count_upper = 0
        count_remain = 0
        count_upper_upper = 0

        for i in arr:
            if i < lower_diameter:
                count_lower += 1
            elif i > upper_diameter and i < upper_diameter + binSize:
                count_upper += 1
            elif i > upper_diameter + binSize:

                count_upper_upper += 1
            else:
                count_remain += 1
                
        # out of which (1-wcm_rate) survives and change that to percentage
        count_lower *= (1-wcm_rate) * population/100
        count_remain *= (1-wcm_rate) * population/100
        count_upper *= (1-wcm_rate) * population/100
        count_upper_upper *= (1-wcm_rate) * population/100
        
        return count_lower, count_remain, count_upper, count_upper_upper


def calculate_population_change(oldPop,growth_rate,pcm_rate,wcm_rate,available_substrate_percentage,coral_type):
    """
    Calculate the change in population of a particular coral type based on various parameters.

    Parameters
    ----------
    oldPop : numpy array
        The current population of the coral type in each bin.
    growth_rate : float
        The growth rate of the coral type.
    pcm_rate : float
        The rate of partial coral mortality of the coral type.
    wcm_rate : float
        The rate of whole colony mortality of the coral type.
    available_substrate_percentage : float
        The percentage of available substrate for the coral type.
    coral_type : str
        The type of coral for which population change needs to be calculated.

    Returns
    -------
    numpy array
        The new population of the coral type in each bin.
    """
    
    if coral_type == 'Branching':
        recruitment = get_recruited_corals(opts.available_substrate_percentage, pop_flag = True)[0]
    elif coral_type == 'Foliose':
        recruitment = get_recruited_corals(opts.available_substrate_percentage, pop_flag = True)[1]
    else:
        recruitment = get_recruited_corals(opts.available_substrate_percentage, pop_flag = True)[2]
    
    MaxBinId = len(oldPop)
    newPoplist = np.zeros(MaxBinId)
    
    for i in range(MaxBinId):
        shrnk,rmn,grw,grw_grw = count_new_population_per_bin(i, oldPop[i],growth_rate[i],pcm_rate[i],wcm_rate[i],available_substrate_percentage)
        if i == 0:
            newPoplist[i] += recruitment 
            newPoplist[i] += rmn
            newPoplist[i+1] += grw
            newPoplist[i+2] += grw_grw
            
        elif i == MaxBinId-2:
            newPoplist[i] += rmn
            newPoplist[i-1] += shrnk
            newPoplist[i+1] += grw
        
        elif i == MaxBinId-1:
            newPoplist[i] += rmn
            newPoplist[i-1] += shrnk
            
        else:
            newPoplist[i-1] += shrnk 
            newPoplist[i] += rmn
            newPoplist[i+1] += grw
            newPoplist[i+2] += grw_grw
        
    return newPoplist.astype(int)



def run_yearly_change(PSD_df, Years):
    """
    Runs yearly coral population growth based on the given parameters.

    Parameters
    ----------
    PSD_df : pandas.DataFrame
        A dataframe containing initial surface area data.
    Years : int
        The number of years to run the simulation.

    Returns
    -------
    pandas.DataFrame
        A dataframe containing yearly total coral cover data.
    """
    
    # generate a random growth slope for growth rate
    opts.gr_slope = random.uniform(0.01, 0.04)
    
    opts.dhw_counter = 0
        
    # Run simulation for given number of years
    for year in range(1,Years + 1):
        opts.year = year
        opts.current_dhw = opts.dhw_lst[opts.year]
        
        # count the number of bleaching that took place
        if opts.current_dhw !=0 :
            # every time bleaching happens the coral becomes resilient to bleaching
            # hence update the coefficient
            opts.dhw_counter += 1
        
        opts.current_cyc = opts.cyc_lst[opts.year]
        PCM_rates_dhw = get_PCM_rates_after_dhw(PCM_rates,opts.current_dhw,branching_bleaching_rate, foliose_bleaching_rate, other_bleaching_rate)
        WCM_rate_cyc = get_WCM_rates_after_cyclones(WCM_rates, opts.current_cyc[0], opts.current_cyc[1])
        new_branching_pop = calculate_population_change(opts.current_population_df['Branching'], growth_rate['Branching'],PCM_rates_dhw['Branching'],WCM_rate_cyc['Branching'],opts.current_total_coral_cover,'Branching')
        new_foliose_pop = calculate_population_change(opts.current_population_df['Foliose'], growth_rate['Foliose'],PCM_rates_dhw['Foliose'],WCM_rate_cyc['Foliose'],opts.current_total_coral_cover,'Foliose')
        new_other_pop = calculate_population_change(opts.current_population_df['Other'], growth_rate['Other'],PCM_rates_dhw['Other'],WCM_rate_cyc['Other'],opts.current_total_coral_cover,'Other')
        opts.current_population_df = pd.DataFrame({ 'Branching': np.array([pop for pop in new_branching_pop]), 
                                                    'Foliose': np.array([pop for pop in new_foliose_pop]), 
                                                    'Other': np.array([pop for pop in new_other_pop])})
        
        # Calculate new surface area based on new population
        new_branching_area = np.array([get_surface_area_from_population(j,new_branching_pop[j])  for j in range(0,MaxBinId)])
        new_foliose_area = np.array([get_surface_area_from_population(j,new_foliose_pop[j])  for j in range(0,MaxBinId)])
        new_other_area = np.array([get_surface_area_from_population(j,new_other_pop[j])  for j in range(0,MaxBinId)])
        
        opts.current_surface_area_df = pd.DataFrame({ 'Branching': np.array([area for area in new_branching_area]), 
                                                      'Foliose': np.array([area for area in new_foliose_area]), 
                                                      'Other': np.array([area for area in new_other_area])})
        
        # Update yearly parameters
        opts.yearly_surface_area_df_list.append(opts.current_surface_area_df)
        opts.yearly_population_df_list.append(opts.current_population_df)
        update_coral_parameters()
        
    # Return dataframe containing yearly total coral cover data    
    return opts.yearly_total_coral_cover_df


def run_coral_model(PSD_df, Years):
    """
    Runs the coral model for the specified number of years using the given initial parameter data.

    Parameters:
    -----------
    PSD_df : pandas DataFrame
        The initial parameter data for the coral model, in the form of a DataFrame.

    Years : int
        The number of years to run the coral model.

    Returns:
    --------
    pandas DataFrame
        The result of running the coral model for the specified number of years.

    
    """
    
    initialize_coral()
    return run_yearly_change(PSD_df, Years)


def run_multiple_model_iterations(number_of_iteration):
    """
    Runs the yearly growth simulation for a given number of iterations and returns a DataFrame with the yearly total coral cover for each iteration.
    
    Parameters
    ----------
    number_of_iteration : int
        The number of iterations to run the simulation.
    
    Returns
    -------
    pandas.DataFrame
        A DataFrame with the yearly total coral cover for each iteration.
    """
    
    total_cover_df = pd.DataFrame({})
    for i in range(1,number_of_iteration+1):
        
        yearly_total_coral_cover = run_coral_model(PSD_T0,MaxYear)['total_coral_cover (%)']
        export_to_excel(opts.yearly_population_df_list,f'yearly_population_iteration_{i}')
        export_to_excel(opts.yearly_surface_area_df_list,f'yearly_surface_area_iteration_{i}')
        export_to_excel(opts.yearly_total_coral_cover_df,f'yearly_total_coral_cover_iteration_{i}')
        export_to_excel(opts.yearly_benthic_cover_df,f'yearly_benthic_cover_iteration_{i}')
        total_cover_df[f'iteration_{i}'] = [i for i in yearly_total_coral_cover]
    
    total_cover_df['averaged'] = [row_avg for row_avg in total_cover_df.mean(axis=1)]
    # total_cover_df['year'] = np.arange(0,MaxYear+1)
    total_cover_df.insert(loc = 0, column = 'year', value = np.arange(0,MaxYear+1))
    file_name = os.path.join(output_folder, f'{number_of_iteration}_model_iteration.xlsx')
    total_cover_df.to_excel(file_name, index=False)
    
    return total_cover_df


def plot_growth_rate_iterations(total_cover_df):
    """
    Plot the growth rate iterations.

    Parameters
    ----------
    growth_rate_total_cover_df : pandas DataFrame
        A pandas DataFrame containing the total coral cover values for each year of each iteration,
        as well as an "averaged" column with the average values for each year across all iterations.

    Returns
    -------
    None

    """
    
    import matplotlib as mpl
    label_size = 12
    mpl.rcParams['xtick.labelsize'] = label_size 
    mpl.rcParams['ytick.labelsize'] = label_size 
    total_cover_df = total_cover_df.drop(columns=['year'])
    # fig = plt.figure(figsize=(15, 10))
    for gr in total_cover_df.columns:
        if gr == 'averaged':
            plt.plot(range(0,MaxYear+1),total_cover_df[gr],'-k',label='Average', linewidth=2.5)
        else:
            plt.plot(range(0,MaxYear+1),total_cover_df[gr], '--', linewidth=1)
        
    plt.xlabel('Years', fontsize = '15')
    plt.ylabel('Total coral cover (%)', fontsize = '15')
    plt.legend()
    plot_file = os.path.join(output_folder, 'growth_rate_iterations.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()
        

def get_relative_increase_coral_cover(old_coral_cover, new_coral_cover):
    """
    Calculate the relative increase in coral cover for different coral types.

    Parameters
    ----------
    old_coral_cover : dict
        A dictionary containing the initial coral cover values for each coral type.
    new_coral_cover : dict
        A dictionary containing the updated coral cover values for each coral type.

    Returns
    -------
    dict
        A dictionary containing the relative increase in coral cover for each coral type.

    """
    relative_increase = {i: 0 if old_coral_cover[i]==0 else 100*(new_coral_cover[i]-old_coral_cover[i])/old_coral_cover[i] for i in coral_type}
    return relative_increase



def get_brooder_spawner_cover(coral_cover):
    """
    Calculate the initial brooder and spawner coral cover values for each coral type.

    Parameters
    ----------
    coral_cover : dict
        A dictionary containing the initial total coral cover values for each coral type.

    Returns
    -------
    tuple
        A tuple containing the initial brooder and spawner coral cover values for the Brooder-Foliose, Spawner-Foliose, and Other coral types, respectively.

    """
    # Extract the total cover values for each coral type
    branching_cover = coral_cover['Branching']
    foliose_cover = coral_cover['Foliose']
    other_cover = coral_cover['Other']
    
    # Calculate the ratios of brooder to spawner cover for the Brooder-Foliose and Spawner-Foliose coral types
    ratio_branching_bf = initial_brooder_cover / (initial_brooder_cover + initial_spawner_cover[0])
    ratio_foliose_bf = initial_spawner_cover[0] / (initial_brooder_cover + initial_spawner_cover[0])
    
    # Calculate the initial brooder and spawner cover values for the Brooder-Foliose coral type
    if ratio_foliose_bf == 0:
        brooder = branching_cover/2
        spawner_bf = branching_cover/2
        
    else:
        spawner_bf = foliose_cover / ratio_foliose_bf
        brooder = branching_cover - ratio_branching_bf * spawner_bf
    
    # Set the initial spawner cover value for the Other coral type to be equal to its total cover value
    spawner_o = other_cover
    
    # Return the initial brooder and spawner cover values for each coral type
    return brooder, spawner_bf, spawner_o


def export_to_excel(df,file_name):
    """
    Export a pandas DataFrame or a list of DataFrames to an Excel file.

    Parameters
    ----------
    df : pandas DataFrame or list of pandas DataFrames
        The DataFrame or list of DataFrames to be exported to Excel.
    file_name : str
        The name of the Excel file to be created.

    Returns
    -------
    None

    Notes
    -----
    - If a single DataFrame is provided, it will be written to the Excel file.
    - If a list of DataFrames is provided, each DataFrame will be written as a separate sheet
      in the Excel file, with sheet names in the format "sheet_i" where i is the index of the DataFrame.

    """

    file_name = os.path.join(output_folder, file_name)
    
    # Check if the input is a list of floats
    if all(isinstance(x, float) for x in df):
        df = pd.DataFrame(df, columns=[file_name])
        df.to_excel(f'{file_name}_growth_param_{opts.growth_parameter}.xlsx', index=True)
        
    elif isinstance(df, pd.DataFrame):
        df.to_excel(f'{file_name}_growth_param_{opts.growth_parameter}.xlsx', index=False)
    
    else:
        # create an ExcelWriter object
        with pd.ExcelWriter(f'{file_name}_growth_param_{opts.growth_parameter}.xlsx') as writer:
            # loop over the dataframes and write each one as a separate sheet
            for i, df in enumerate(df):
                df.to_excel(writer, sheet_name=f'year_{i}', index=True)
                
                
                
                
def get_slope(rugosity_list):
    """
    Calculate the slope of a line given a list of rugosity values.

    Parameters
    ----------
    rugosity_list : list
        A list of rugosity values.

    Returns
    -------
    float
        The slope of the line.

    """
    
    del_y = rugosity_list[-1] - rugosity_list[0]
    del_x = opts.yearly_total_coral_cover_df['total_coral_cover (%)'].iloc[-1] - opts.yearly_total_coral_cover_df['total_coral_cover (%)'][0]
    return del_y/del_x
    

def get_rugosity_list():
    """
    Calculates the rugosity values for each year based on the annual change in total coral cover and the ratio of 
    branching, foliose, and other coral cover.

    Returns
    -------
    rugosity_list : list
        A list of rugosity values for each year.

    """
    
    global rugosity_initial
    ri_initial = rugosity_initial
    rugosity_list = [ri_initial]
    total_cover_initial = opts.yearly_total_coral_cover_df['total_coral_cover (%)'][0]
    
    for i in range(1,MaxYear+1):

        new_branching_cover = opts.yearly_total_coral_cover_df['Branching_Area (%)'][i]
        new_foliose_cover = opts.yearly_total_coral_cover_df['Foliose_Area (%)'][i]
        new_other_cover = opts.yearly_total_coral_cover_df['Other_Area (%)'][i]

        ratio_i = new_branching_cover / (new_foliose_cover + new_other_cover)
        total_cover_i = opts.yearly_total_coral_cover_df['total_coral_cover (%)'][i]

        if ratio_i > 1.0:
            m = slope_max
        elif (ratio_i <= 1.0 and ratio_i > 0.1):
            m = slope_av
        else: #ratio<0.1
            m = slope_min

        ri = ri_initial + m * (total_cover_i - total_cover_initial)
        rugosity_list.append(ri)
        ri_initial = ri
        total_cover_initial = total_cover_i
    
    return rugosity_list


def plot_rugosity_year():
    """
    Plot the rugosity values over the years.

    Parameters
    ----------
    None

    Returns
    -------
    None

    """
    
    rugosity_list = get_rugosity_list()
    plt.plot(range(0,MaxYear+1),rugosity_list,'-*')
    plt.xlabel('Years', fontsize = '15')
    plt.ylabel('Rugosity', fontsize = '15')
    plot_file = os.path.join(output_folder, 'rugosity_year.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()
    

def plot_rugosity_total_coral_cover():
    """
    Plots the relationship between rugosity and total coral cover percentage.

    Parameters
    ----------
    None

    Returns
    -------
    None

    """
    
    rugosity_list = get_rugosity_list()
    model_slope = get_slope(rugosity_list)
    b_min = rugosity_initial - slope_min * opts.yearly_total_coral_cover_df['total_coral_cover (%)'][0] 
    b_max = rugosity_initial - slope_max * opts.yearly_total_coral_cover_df['total_coral_cover (%)'][0] 
    min_plot = slope_min * opts.yearly_total_coral_cover_df['total_coral_cover (%)'] + b_min
    max_plot = slope_max * opts.yearly_total_coral_cover_df['total_coral_cover (%)'] + b_max
    plt.plot(opts.yearly_total_coral_cover_df['total_coral_cover (%)'],max_plot,'--b', label = f'max, slope = {slope_max}')
    plt.plot(opts.yearly_total_coral_cover_df['total_coral_cover (%)'],rugosity_list,'-*r', label = f'model, slope = {model_slope:.4f}')
    plt.plot(opts.yearly_total_coral_cover_df['total_coral_cover (%)'],min_plot,'--b', label = f'min, slope = {slope_min}')
    x = opts.yearly_total_coral_cover_df['total_coral_cover (%)']
    y1 = min_plot
    y2 = max_plot
    y3 = rugosity_list
    # plt.annotate(f"Slope : {slope_min:}", xy=(x.iloc[-1], y1.iloc[-1]), xytext=(x.iloc[-1]-12, y1.iloc[-1]-0.5), color='blue')
    # plt.annotate(f"Slope = {slope_max:}", xy=(x.iloc[-1], y1.iloc[-1]), xytext=(x.iloc[-1]-20, y2.iloc[-1]-0.3), color='blue')
    # plt.annotate(f"Slope : {model_slope:.4f}", xy=(x.iloc[-1], y3[-1]), xytext=(x.iloc[-1]-12, y3[-1]-0.75), color='red')
    
    plt.xlabel('Total Coral Cover (%)', fontsize = '15')
    plt.ylabel('Rugosity', fontsize = '15')
    plt.legend()
    plot_file = os.path.join(output_folder, 'rugosity_total_cover.svg')
    plt.savefig(plot_file, format='svg')
    plt.show()
    
    

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



def eggs_decline_rate(dhw):
    """
    Calculates the egg decline rate based on the degree heating weeks (DHW).

    Parameters
    ----------
    dhw : integer
        The degree heating weeks (DHW) value.

    Returns
    -------
    float
        The egg decline rate.

    """
    return 1 - 1 / (1 + eggs_decline_coefficient*np.exp(4-dhw))

def colonies_spawning_decline_rate(dhw):
    """
    Calculate the decline rate of colonies spawning as a function of degree heating weeks (DHW).

    Parameters
    ----------
    dhw : integer
        The degree heating weeks.

    Returns
    -------
    float
        The decline rate of colonies spawning.

    """
    return 1 - 1 / (1 + colonies_spawning_decline_coefficient * np.exp(4 - dhw))



def get_PCM_rates_after_dhw(PCM_rates, dhw, branching_bleaching_rate, foliose_bleaching_rate, other_bleaching_rate):
    """
    Calculate the PCM rates for each coral growth form given the degree heating weeks (DHW).

    Parameters
    ----------
    PCM_rates : pandas DataFrame
        A DataFrame containing the PCM rates for each coral growth form and bin id.
    dhw : integer
        The degree heating weeks (DHW) value for the given year.

    Returns
    -------
    pandas DataFrame
        A DataFrame containing the updated PCM rates for each coral growth form and bin id based on the given DHW value.
    """
    
    # compute the array of A values
    A = np.array([0.5*2**(i/(MaxBinId-1)) for i in range(MaxBinId)])
    # compute the exponential term
    exp_term = np.exp(4 - A * dhw)
    
    branching_bleaching_rate *= 1.05**(opts.dhw_counter-1)
    foliose_bleaching_rate *= 1.05**(opts.dhw_counter-1)
    other_bleaching_rate *= 1.05**(opts.dhw_counter-1)
    
    if growthOnly:
        pcm_rates_dhw = WCM_rates
    else:
        # compute the PCM rates for each coral growth form and bin id
        pcm_rates_dhw = pd.DataFrame(
                                    {
                                        'Branching': [(1 - PCM_rates['Branching'][j]) / (1 + branching_bleaching_rate*exp_term[j]) + PCM_rates['Branching'][j] for j in range(MaxBinId)],
                                        'Foliose': [(1 - PCM_rates['Foliose'][j]) / (1 + foliose_bleaching_rate*exp_term[j]) + PCM_rates['Foliose'][j] for j in range(MaxBinId)],
                                        'Other': [(1 - PCM_rates['Other'][j]) / (1 + other_bleaching_rate*exp_term[j]) + PCM_rates['Other'][j] for j in range(MaxBinId)],
                                    }
                                    )
    return pcm_rates_dhw



def get_WCM_rates_after_cyclones(WCM_rates, cyclone_severity_level, distance_to_cyclone):
    """
    Calculate the WCM rates during cyclone events.

    Parameters:
    -----------
    WCM_rates : DataFrame
        The WCM rates for branching, foliose, and other coral types.
    cyclone_severity_level : float
        The severity level of the cyclone event.
    distance_to_cyclone : float
        The distance to the cyclone event.

    Returns:
    --------
    wcm_rates_cyc : DataFrame
        The updated WCM rates during cyclone events.

    Notes:
    ------
    This function calculates the WCM rates for branching, foliose, and other coral types during cyclone events.
    The WCM rates are adjusted based on the severity level of the cyclone and the distance to the cyclone event.
    The calculations are performed using exponential decay functions.

    """
    if not cyclone:
        return WCM_rates
    
    else:
        cyclone_severity_level = cyclone_severity_level*2
        pp = np.linspace(1,MaxBinId+1,20)
        bins = np.array([p*cyclone_bin_coefficient for p in pp])
        
        exp_term_branching = cyclone_severity_level*np.exp(-distance_to_cyclone/bins/cyclone_bin_coefficient)
        exp_term_foliose = cyclone_severity_level*np.exp(-distance_to_cyclone/bins/cyclone_bin_coefficient)
        exp_term_other = cyclone_severity_level*np.exp(-distance_to_cyclone/bins/cyclone_bin_coefficient)


        wcm_rates_cyc = pd.DataFrame(
                                        {
                                            'Branching': [1 - 1 / (1 + branching_cyclone_coefficient * exp_term_branching[j]) + WCM_rates['Branching'][j] for j in range(MaxBinId)],
                                            'Foliose': [1 - 1 / (1 + foliose_cyclone_coefficient * exp_term_foliose[j]) + WCM_rates['Foliose'][j] for j in range(MaxBinId)],
                                            'Other': [1 - 1 / (1 + other_cyclone_coefficient * exp_term_other[j]) + WCM_rates['Other'][j] for j in range(MaxBinId)],
                                        }
                                        )
        
        return wcm_rates_cyc



def split_w(x, y, z, t, w):
    """
    This function calculates ratios based on 'x', 'y', 'z' and 't', and then uses these ratios to
    split the value 'w' into 'w_x', 'w_y', and 'w_z'. If the sum of 'w_x', 'w_y', and 'w_z' does not equal 'w', 
    'w_x', 'w_y', and 'w_z' are adjusted proportionally to ensure that their sum equals 'w'.

    Parameters
    ----------
    x : float
        First component to which 'w' should be proportioned.
    y : float
        Second component to which 'w' should be proportioned.
    z : float
        Third component to which 'w' should be proportioned.
    t : float
        Total of 'x', 'y', and 'z'.
    w : float
        Value to be split among 'x', 'y', and 'z'.

    Returns
    -------
    w_x : float
        The portion of 'w' assigned to 'x'.
    w_y : float
        The portion of 'w' assigned to 'y'.
    w_z : float
        The portion of 'w' assigned to 'z'.
    """
    
    x_ratio = x / t
    y_ratio = y / t
    z_ratio = z / t

    # Calculate the split values of w for x and y based on their contribution ratios
    w_x = x_ratio * w
    w_y = y_ratio * w
    w_z = z_ratio * w

    # Adjust the split values to satisfy w_x + w_y = w, if necessary
    if w_x + w_y + w_z != w:
        # Decrease w_x and/or w_y proportionally
        factor = w / (w_x + w_y + w_z)
        w_x *= factor
        w_y *= factor
        w_z *= factor

    return w_x, w_y, w_z


def get_available_substrate():
    """
    This function computes the total available substrate by summing up the current benthic cover 
    of hard substrate, dead coral, CCA, and turfing algae.

    Returns
    -------
    float
        The total available substrate, computed as the sum of the current benthic cover of hard substrate, 
        dead coral, CCA, and turfing algae.

    """
    
    return opts.current_benthic_cover['hard_substrate'] + opts.current_benthic_cover['dead_coral'] + opts.current_benthic_cover['CCA'] + opts.current_benthic_cover['turfing_algae']



def get_unavailable_substrate():
    """
    This function computes the total unavailable substrate by summing up the current benthic cover 
    of macro algae, rubble, and sediment.

    Returns
    -------
    float
        The total unavailable substrate, computed as the sum of the current benthic cover of macro algae, 
        rubble, and sediment.

    """
    
    return opts.current_benthic_cover['macro_algae'] + opts.current_benthic_cover['rubble'] + opts.current_benthic_cover['sediment']



def calculate_benthos_after_cyclone(change_branching_cover, change_foliose_cover, change_other_cover):
    
    """
    This function adjusts the benthic cover values according to the changes caused by a cyclone. The 
    changes in branching cover, foliose cover, and other cover are specified as input arguments. 
    
    Parameters
    ----------
    change_branching_cover : float
        The change in the branching cover due to the cyclone.
    change_foliose_cover : float
        The change in the foliose cover due to the cyclone.
    change_other_cover : float
        The change in the other cover types due to the cyclone.

    Returns
    -------
    None

    """
    
    if change_branching_cover < 0:
        opts.current_benthic_cover['rubble'] += abs(change_branching_cover)
        
    else:
        w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_branching_cover)
        opts.current_benthic_cover['hard_substrate'] -= w_hs
        opts.current_benthic_cover['dead_coral'] -= w_dc
        opts.current_benthic_cover['turfing_algae'] -= w_tf
        
    if change_foliose_cover < 0 :
        opts.current_benthic_cover['rubble'] += abs(change_foliose_cover)
        
    else:
        w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_foliose_cover)
        opts.current_benthic_cover['hard_substrate'] -= w_hs
        opts.current_benthic_cover['dead_coral'] -= w_dc
        opts.current_benthic_cover['turfing_algae'] -= w_tf
        
    if change_other_cover < 0:
        opts.current_benthic_cover['rubble'] += abs(change_other_cover)/4
        opts.current_benthic_cover['dead_coral'] += abs(change_other_cover)/2
        opts.current_benthic_cover['turfing_algae'] += abs(change_other_cover)/4
        
    else:
        w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_other_cover)
        opts.current_benthic_cover['hard_substrate'] -= w_hs
        opts.current_benthic_cover['dead_coral'] -= w_dc
        opts.current_benthic_cover['turfing_algae'] -= w_tf
        
        
        
def calculate_benthos_after_bleaching(change_branching_cover, change_foliose_cover, change_other_cover):
    """
    This function adjusts the benthic cover values according to the changes caused by a bleaching event. The 
    changes in branching cover, foliose cover, and other cover are specified as input arguments. 
    
    Parameters
    ----------
    change_branching_cover : float
        The change in the branching cover due to the bleaching event.
    change_foliose_cover : float
        The change in the foliose cover due to the bleaching event.
    change_other_cover : float
        The change in the other cover types due to the bleaching event.

    Returns
    -------
    None

    """
    
    if change_branching_cover < 0:
        opts.current_benthic_cover['rubble'] += abs(change_branching_cover)
        
    else:
        w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_branching_cover)
        opts.current_benthic_cover['hard_substrate'] -= w_hs
        opts.current_benthic_cover['dead_coral'] -= w_dc
        opts.current_benthic_cover['turfing_algae'] -= w_tf
        
    if change_foliose_cover < 0:
        opts.current_benthic_cover['dead_coral'] += abs(change_foliose_cover)/3
        opts.current_benthic_cover['turfing_algae'] += abs(change_foliose_cover)/3
        opts.current_benthic_cover['macro_algae'] += abs(change_foliose_cover)/3
        
    else:
        w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_foliose_cover)
        opts.current_benthic_cover['hard_substrate'] -= w_hs
        opts.current_benthic_cover['dead_coral'] -= w_dc
        opts.current_benthic_cover['turfing_algae'] -= w_tf
        
    if change_other_cover < 0:
        opts.current_benthic_cover['dead_coral'] += abs(change_other_cover)/3
        opts.current_benthic_cover['turfing_algae']  += abs(change_other_cover)/3
        opts.current_benthic_cover['macro_algae']  += abs(change_other_cover)/3
        
    else:
        w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_other_cover)
        opts.current_benthic_cover['hard_substrate'] -= w_hs
        opts.current_benthic_cover['dead_coral'] -= w_dc
        opts.current_benthic_cover['turfing_algae'] -= w_tf