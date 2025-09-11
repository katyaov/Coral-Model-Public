from config import *
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import os
import numpy as np
import pandas as pd   
from matplotlib.ticker import FormatStrFormatter, MaxNLocator
import re
from datetime import datetime
from zoneinfo import ZoneInfo 
### Rio
opts = CoralOptions()

try:
	from user_inputs import bleaching, cyclone, enable_sediment_exposure
except Exception:
	bleaching = True  # Default values
	cyclone = True
	enable_sediment_exposure = True

if not hasattr(opts, "bleaching"):
	opts.bleaching = bool(bleaching)
if not hasattr(opts, "cyclone"):
	opts.cyclone = bool(cyclone)
###Rio
if not hasattr(opts, "enable_sediment_exposure"):
	opts.enable_sediment_exposure = bool(enable_sediment_exposure)

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
	#    retention_rate_o = retention_rates_4d[0]

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
	actual_year = int(year_start) + int(year)  # convert model year index to actual year
	plt.title(f'Surface Area Distribution in {actual_year}')
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
		actual_year = int(year_start) + int(arg)  # convert model year index to actual year
		# Plot the data for each coral type
		plt.plot(binDiameter,df,'-*',label = f'year = {actual_year}')
		
	# Add title and axis labels
	plt.title(f'Coral cover of {coral_type}')
	plt.xlabel('Bin Diameter (cm)', fontsize = '15')
	plt.ylabel(f'{coral_type} Area (m$^2$)', fontsize = '15')
	if log:
		plt.yscale('log')
		
	# Add legend and display the plot
	plt.legend()
	plt.legend(title="Year")
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
	plt.figure(figsize=(8,5))

	binId = np.arange(0, MaxBinId)
	binDiameter = get_bin_diameter(binId)
	
	n_slices = len(opts.yearly_population_df_list)
	lines, labels = [], []
	
	for year in map(int, args):     # args are model years (0-based)
		if not (0 <= year < n_slices):
			raise ValueError(
				f"Model year {year} out of range [0, {n_slices-1}]. "
				f"(MaxYear={MaxYear}, list_len={n_slices})"
			)
	
		df = opts.yearly_population_df_list[year][coral_type]
		actual_year = int(year_start) + year
		(ln,) = plt.plot(binDiameter, df, '-*')
		lines.append(ln)
		labels.append(str(actual_year))
	
	plt.title(f'Coral cover of {coral_type}')
	plt.xlabel('Bin Diameter (cm)', fontsize=15)
	plt.ylabel(f'{coral_type} population', fontsize=15)
	if log:
		plt.yscale('log')
	plt.legend(lines, labels, title="Year")
	
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
		'Branching': [get_surface_area_from_population(j, population_df['Branching'][j]) for j in range(0, MaxBinId)],
		'Foliose': [get_surface_area_from_population(j, population_df['Foliose'][j]) for j in range(0, MaxBinId)],
		'Other': [get_surface_area_from_population(j, population_df['Other'][j]) for j in range(0, MaxBinId)],
	})

	return surface_area


def initialize_coral():
	"""
	Initialize the coral ecosystem at year = 0.
	Returns
	-------
	None.
	"""
	# Ensure attributes exist with defaults
	if not hasattr(opts, "bleaching"):
		opts.bleaching = True
	if not hasattr(opts, "cyclone"):
		opts.cyclone = True
	if not hasattr(opts, "enable_sediment_exposure"):
		opts.enable_sediment_exposure = True

	opts.year = 0

	# --- DHW handling ---
	if opts.bleaching:
		opts.dhw_lst = create_dhw_list(dhw_years)
		opts.current_dhw = opts.dhw_lst[opts.year]
		opts.dhw_counter = 0
	else:
		opts.dhw_lst = None
		opts.current_dhw = 0
		opts.dhw_counter = 0

	# --- Cyclone handling ---
	if opts.cyclone:
		opts.cyc_lst = create_cyclone_list(cyclone_years)
		opts.current_cyc = opts.cyc_lst[opts.year]
	else:
		opts.cyc_lst = None
		opts.current_cyc = [0, 0]

	# --- Sediment handling ---
	if opts.enable_sediment_exposure:
		# Create lists for additional suspended and deposited sediment exposure per year
		opts.add_suspended_sediment_lst = [0] * (MaxYear + 1)
		opts.add_deposited_sediment_lst = [0] * (MaxYear + 1)
		for year in range(MaxYear + 1):
			# Each year is a relative year index (0-based)
			suspended, deposited = add_sedi_exp_per_year.get(year, (0, 0))
			opts.add_suspended_sediment_lst[year] = suspended
			opts.add_deposited_sediment_lst[year] = deposited
		opts.current_add_suspended_sediment = opts.add_suspended_sediment_lst[opts.year]
		opts.current_add_deposited_sediment = opts.add_deposited_sediment_lst[opts.year]
	else:
		opts.add_suspended_sediment_lst = None
		opts.add_deposited_sediment_lst = None
		opts.current_add_suspended_sediment = 0
		opts.current_add_deposited_sediment = 0

	opts.current_coral_cover = initial_coral_cover.copy()
	opts.brooder_cover = initial_brooder_cover
	opts.spawner_cover = initial_spawner_cover
	opts.current_total_coral_cover = initial_total_coral_cover
	opts.yearly_total_coral_cover_df = pd.DataFrame({'Year': 0,
		'Branching_Area (%)': initial_coral_cover['Branching'],
		'Foliose_Area (%)': initial_coral_cover['Foliose'],
		'Other_Area (%)': initial_coral_cover['Other'],
		'total_coral_cover (%)': initial_total_coral_cover}, index=[0])

	opts.current_benthic_cover = opts.initial_benthic_cover_dict.copy()
	opts.yearly_benthic_cover_df = pd.DataFrame({'Year': opts.year,
		'total_benthic_cover (%)': opts.current_benthic_cover['total'],
		'available_substrate (%)': opts.current_benthic_cover['available_substrate'],
		'hard_substrate (%)': opts.current_benthic_cover['hard_substrate'],
		'dead_coral (%)': opts.current_benthic_cover['dead_coral'],
		'CCA (%)': opts.current_benthic_cover['CCA'],
		'turfing_algae (%)': opts.current_benthic_cover['turfing_algae'],
		'macro_algae (%)': opts.current_benthic_cover['macro_algae'],
		'rubble (%)': opts.current_benthic_cover['rubble'],
		'sediment (%)': opts.current_benthic_cover['sediment'],
		'total_cc ': opts.current_total_coral_cover,
		'unavailable_sub': opts.unavailable_substrate_percentage,
		'tot': opts.available_substrate_percentage + opts.unavailable_substrate_percentage + opts.current_total_coral_cover,
	}, index=[0])

	opts.current_population_df = get_initial_population(PSD_T0)
	opts.yearly_population_df_list = [opts.current_population_df]
	opts.current_surface_area_m2_df = get_surface_area(opts.current_population_df)
	opts.yearly_surface_area_df_list = [opts.current_surface_area_m2_df]
	opts.unavailable_substrate_percentage = opts.current_benthic_cover['macro_algae'] + opts.current_benthic_cover['rubble'] + opts.current_benthic_cover['sediment']
	opts.available_substrate_percentage = get_available_substrate()
	opts.maximum_achievable_substrate_percentage = 100 - opts.unavailable_substrate_percentage
	opts.upper_diameter = MaxBinId * binSize

#
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
    
	##RIO: impacts of diturbance to benthic cover is not cummulative. 
	###The code applies only one disturbance impact per year, with the following priority:
#Cyclone > Bleaching > Sediment > Normal change.
#This ensures that if multiple disturbances could occur in the same year, only the highest-priority event is processed, and its effects are reflected in the benthic cover update.
    if opts.current_cyc[0] != 0:     
        calculate_benthos_after_cyclone(change_branching_cover, change_foliose_cover, change_other_cover)
        
    elif opts.current_dhw != 0:
        calculate_benthos_after_bleaching(change_branching_cover, change_foliose_cover, change_other_cover)
	
	#below is currently redundent as reduction in coral cover converts to dead coral anyway
    elif opts.current_add_deposited_sediment > 0:
        calculate_benthos_after_pcm_ds(change_branching_cover, change_foliose_cover, change_other_cover)
    
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

		#RIO: might have to apply current growth rate here
		arr += growth_rate * (1 - (current_total_coral_cover / opts.maximum_achievable_substrate_percentage)**opts.growth_parameter)

		#arr *= np.sqrt(1-pcm_rate) # high values of pcm_rate can lead to negative values inside sqrt - so below I have changed the code to prevent negative numbers - this may now be redundent
		arr *= np.sqrt(np.clip(1-pcm_rate, 0, None)) # ensure non-negative values for very high pcm_rate
		#arr *= np.sqrt(1-wcm_rate) #RIO - why is this commented out is it commented out in Katyas code
		
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
	

	#Rio - i have removed the following line it is already defined in config and this is the only plac ein this script gr_slope occurs - I think its a mistake 
	#opts.gr_slope = random.uniform(0.01, 0.04) #Rio: Katya: this overwrites parameter set in config.py - is this intended?





	
	opts.dhw_counter = 0
		
	# Run simulation for given number of years
	for year in range(1, Years + 1):
		opts.year = year
		
		# Handle bleaching only if enabled
		if getattr(opts, "bleaching", True) and opts.dhw_lst is not None:
			opts.current_dhw = opts.dhw_lst[opts.year]
			# count the number of bleaching that took place
			if opts.current_dhw != 0:
				# every time bleaching happens the coral becomes resilient to bleaching
				# hence update the coefficient
				opts.dhw_counter += 1
		else:
			opts.current_dhw = 0
		
		# Handle cyclones only if enabled
		if getattr(opts, "cyclone", True) and opts.cyc_lst is not None:
			opts.current_cyc = opts.cyc_lst[opts.year]
		else:
			opts.current_cyc = [0, 0]




		
		
		###Rio 
		
		# Handle sediment exposure only if enabled
		if getattr(opts, "enable_sediment_exposure", True) and opts.add_deposited_sediment_lst is not None:
			opts.current_add_deposited_sediment = opts.add_deposited_sediment_lst[opts.year]
			###RIO adjust below if you want to add resilince with exposure 
			# count the number of bleaching that took place
			#if opts.current_add_deposited_sediment != 0:
				# every time bleaching happens the coral becomes resilient to bleaching
				# hence update the coefficient
			#	opts.dhw_counter += 1
		else:
			opts.current_add_deposited_sediment = 0
		#rio gr
		GR_ss = get_GR_after_ss(opts.current_add_suspended_sediment, gr_sedi_sus_coeff)


		PCM_rates_dhw = get_PCM_rates_after_dhw(PCM_rates, opts.current_dhw, branching_bleaching_rate, foliose_bleaching_rate, other_bleaching_rate)
		#PCM_rates_ds = get_PCM_rates_after_DS_exp(PCM_rates, opts.current_add_deposited_sediment, sedi_exp_PCM_coeff)
		PCM_rates_ds = get_PCM_rates_after_DS_exp(
    		PCM_rates,
    		add_sedi_exp_per_year,   # dictionary from config.py
    		opts.year,               # current year index
    		sedi_exp_PCM_coeff      # coefficients from config.py
		)

		WCM_rate_cyc = get_WCM_rates_after_cyclones(WCM_rates, opts.current_cyc[0], opts.current_cyc[1])

#tried to include both decline from ds and from dhw.. didnt work 
#		new_branching_pop = calculate_population_change(opts.current_population_df['Branching'], growth_rate['Branching'],PCM_rates_dhw['Branching'],PCM_rates_ds['Branching'],WCM_rate_cyc['Branching'],opts.current_total_coral_cover,'Branching')
#		new_foliose_pop = calculate_population_change(opts.current_population_df['Foliose'], growth_rate['Foliose'],PCM_rates_dhw['Foliose'],PCM_rates_ds['Foliose'],WCM_rate_cyc['Foliose'],opts.current_total_coral_cover,'Foliose')
#		new_other_pop = calculate_population_change(opts.current_population_df['Other'], growth_rate['Other'],PCM_rates_dhw['Other'],PCM_rates_ds['Other'],WCM_rate_cyc['Other'],opts.current_total_coral_cover,'Other')
#for this version of the model I will include only the impact of ds
		new_branching_pop = calculate_population_change(
    		opts.current_population_df['Branching'],
    		growth_rate['Branching'],
    		PCM_rates_ds['Branching'],
   		 	WCM_rate_cyc['Branching'],
    		opts.current_total_coral_cover,
    		'Branching'
		)
		new_foliose_pop = calculate_population_change(
    		opts.current_population_df['Foliose'],
    		growth_rate['Foliose'],
    		PCM_rates_ds['Foliose'],
    		WCM_rate_cyc['Foliose'],
    		opts.current_total_coral_cover,
    		'Foliose'
		)
		new_other_pop = calculate_population_change(
    		opts.current_population_df['Other'],
    		growth_rate['Other'],
    		PCM_rates_ds['Other'],
    		WCM_rate_cyc['Other'],
    		opts.current_total_coral_cover,
    		'Other'
		)



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


def run_multiple_model_iterations_total_cover(number_of_iteration, workbook_path=None):
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
	
	# pick an engine that actually exists in this kernel
	try:
		import xlsxwriter  # noqa: F401
		engine = "xlsxwriter"
	except ModuleNotFoundError:
		try:
			import openpyxl  # noqa: F401
			engine = "openpyxl"
		except ModuleNotFoundError:
			raise RuntimeError(
				"No Excel engine found. Install one of: pip install XlsxWriter OR pip install openpyxl"
			)

	iteration_series = []
	
	run_id = "Run_" + make_run_id(output_folder)+ "_"              # e.g. '20250808_01'
	
	if workbook_path is None:
		workbook_path = os.path.join(output_folder, f"{run_id}{number_of_iteration}_model_iterations.xlsx")

	os.makedirs(os.path.dirname(workbook_path), exist_ok=True)

	with pd.ExcelWriter(workbook_path, engine=engine) as writer:
		for i in range(1, number_of_iteration + 1):
			yearly_total_coral_cover = run_coral_model(PSD_T0, MaxYear)['total_coral_cover (%)']
			iteration_series.append(pd.Series(yearly_total_coral_cover.values, name=f'iteration_{i}'))

			pop_long = pd.concat({yr: df for yr, df in enumerate(opts.yearly_population_df_list)},
								 names=['Year']).reset_index(level='Year')
			pop_long.to_excel(writer, sheet_name=f'population_{i:03d}', index=False)

			area_long = pd.concat({yr: df for yr, df in enumerate(opts.yearly_surface_area_df_list)},
								  names=['Year']).reset_index(level='Year')
			area_long.to_excel(writer, sheet_name=f'area_{i:03d}', index=False)

			opts.yearly_benthic_cover_df.to_excel(writer, sheet_name=f'benthic_{i:03d}', index=False)
			opts.yearly_total_coral_cover_df.to_excel(writer, sheet_name=f'total_cover_{i:03d}', index=False)

		iters_df = pd.concat(iteration_series, axis=1)
		averaged = iters_df.mean(axis=1)
		years = pd.Series(np.arange(0, len(iters_df)), name='year')
		
		total_cover_df = pd.concat([years.to_frame(), iters_df, averaged.rename('averaged').to_frame()], axis=1)
		total_cover_df.to_excel(writer, sheet_name='summary_total_cover', index=False)

	return total_cover_df, workbook_path


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
	
	label_size = 12
	plt.rcParams['xtick.labelsize'] = label_size
	plt.rcParams['ytick.labelsize'] = label_size

	# 1) Build x as ACTUAL years
	yrs = total_cover_df['year'].to_numpy()
	# If 'year' already holds real years, this keeps them; if it's indices, add year_start
	x = (yrs + year_start) if yrs.min() < 1000 else yrs

	# 2) Pick iteration columns and (optionally) averaged
	iter_cols = [c for c in total_cover_df.columns if c.startswith('iteration_')]
	has_avg = 'averaged' in total_cover_df.columns

	# 3) Plot
	plt.figure(figsize=(9, 5))
	for c in iter_cols:
		plt.plot(x, total_cover_df[c].to_numpy(), '--', linewidth=1, alpha=0.6)
	if has_avg:
		plt.plot(x, total_cover_df['averaged'].to_numpy(), '-k', linewidth=2.5, label='Average')

	plt.xlabel('Year', fontsize=15)
	plt.ylabel('Total coral cover (%)', fontsize=15)
	if has_avg:
		plt.legend()

	# Keep year labels as integers (no 2005.5)
	plt.gca().xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))

	plot_file = os.path.join(output_folder, 'growth_rate_iterations.svg')
	plt.savefig(plot_file, format='svg')
	plt.show()    

# Function to run the model multiple iterations and collect the results 
def run_model_iterations_all_parameters(number_of_iterations):
	population_results = []
	percentage_population_results = []
	area_results = []
	final_results = []
	
	for iteration in range(number_of_iterations):
		#np.random.seed(42 + iteration)
		#random.seed(42 + iteration)
		
		coral_model_results = run_coral_model(PSD_T0, MaxYear)
		benthic_cover_results = opts.yearly_benthic_cover_df
		rugosity_results = get_rugosity_list()
		
		# Merge the results into a single DataFrame
		merged_results = pd.merge(coral_model_results, benthic_cover_results, on='Year')
		merged_results['Rugosity'] = rugosity_results
		
		final_results.append(merged_results)
		
		# Collect population, percentage population, and area results
		for year in range(MaxYear + 1):
			population_df = opts.yearly_population_df_list[year]
			surface_area_df = opts.yearly_surface_area_df_list[year]
			
			for mg in ['Branching', 'Foliose', 'Other']:
				# Population Size DataFrame
				pop_size_row = [mg, year] + population_df[mg].tolist()
				population_results.append(pop_size_row)
				
				# Percentage Population Size DataFrame
				total_pop = population_df[mg].sum()
				perc_pop_size_row = [mg, year] + (100 * population_df[mg] / total_pop).tolist()
				percentage_population_results.append(perc_pop_size_row)
				
				# Area DataFrame
				total_area = reef_area  # Total area in m²
				perc_area_row = [mg, year] + (100 * surface_area_df[mg] / total_area).tolist()
				area_results.append(perc_area_row)
	
	# Concatenate all the results into a single DataFrame
	final_df = pd.concat(final_results)
	
	return final_df, population_results, percentage_population_results, area_results


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
	rugosity_list = get_rugosity_list()                 # length should be MaxYear+1
	years = np.arange(year_start, year_start + len(rugosity_list))

	fig, ax = plt.subplots(figsize=(8, 5))
	ax.plot(years, rugosity_list, '-*')
	ax.set_xlabel('Year', fontsize=15)
	ax.set_ylabel('Rugosity', fontsize=15)

	# integer year labels (no 2005.5)
	ax.xaxis.set_major_formatter(mticker.FormatStrFormatter('%d'))
	ax.xaxis.set_major_locator(mticker.MaxNLocator(integer=True))

	plot_file = os.path.join(output_folder, 'rugosity_year.svg')
	fig.savefig(plot_file, format='svg', bbox_inches='tight')
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

###Rio create  ds list 
def create_deposited_sediment_list(add_sedi_exp_per_year):
    """
    Create a list of additional deposited sediment values per year.

    Parameters
    ----------
    add_sedi_exp_per_year : dict
        A dictionary with keys as relative year indices and values as (suspended, deposited) tuples.

    Returns
    -------
    list
        A list where each index corresponds to a year and contains the additional deposited sediment value.
        If no data is available for a particular year, the entry is set to 0.

    Notes
    -----
    The list is created by initializing an array of zeros with a length equal to MaxYear+1.
    The deposited sediment values for each year are then inserted at the corresponding index in the list.
    """
    deposited_lst = [0] * (MaxYear + 1)
    for year, (suspended, deposited) in add_sedi_exp_per_year.items():
        deposited_lst[int(year)] = deposited  # set the deposited sediment at the corresponding year index

    return deposited_lst

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

 
def get_PCM_rates_after_DS_exp(PCM_rates, add_sedi_exp_per_year, year, sedi_exp_PCM_coeff):
    """
    Calculate updated Partial Colony Mortality (PCM) rates for each coral type based on deposited sediment exposure.
    Ensures PCM rates are clipped between 0 and 1.

    This version uses a linear relationship:
        new_rate = base_rate + (coefficient x additional deposited_sediment)

    Parameters:
    - PCM_rates: pd.DataFrame with columns ['Branching', 'Foliose', 'Other'] representing base PCM rates.
    - add_sedi_exp_per_year: dict with keys as relative year indices and values as (suspended, deposited) tuples.
    - year: int, relative year index (e.g., 0 for 2005).
    - sedi_exp_PCM_coeff: dict with linear coefficients for each coral type.

    Returns:
    - updated_PCM_rates: pd.DataFrame with adjusted PCM rates.
    """
    import pandas as pd

    pcm_rates_ds = pd.DataFrame(columns=PCM_rates.columns)
    add_deposited_sediment = add_sedi_exp_per_year.get(year, (0, 0))[1]

    for coral_type in PCM_rates.columns:
        coeff = sedi_exp_PCM_coeff.get(coral_type, 0)
        adjusted_rates = []
        for base_rate in PCM_rates[coral_type]:
            # Ensure PCM is always between 0 and 1
            adjusted_rate = base_rate + coeff * add_deposited_sediment
            adjusted_rate = max(0, min(adjusted_rate, 1))
            adjusted_rates.append(adjusted_rate)
        pcm_rates_ds[coral_type] = adjusted_rates

    return pcm_rates_ds


def get_GR_after_ss(current_add_suspended_sediment, gr_sedi_sus_coeff):
	"""
	Calculate the growth rate after considering the effect of suspended sediment.

	Parameters:
	-----------
	current_add_suspended_sediment : float
		The current amount of added suspended sediment.
	gr_sedi_sus_coeff : dict
		A dictionary containing the growth rate coefficients for each coral type.

	Returns:
	--------
	growth_rate_ss : dict
		A dictionary containing the updated growth rates for each coral type after considering the effect of suspended sediment.

	Notes:
	------
	This function calculates the growth rate for each coral type (Branching, Foliose, Other) after considering the effect of suspended sediment.
	The growth rate is adjusted based on the amount of suspended sediment and the corresponding growth rate coefficient for each coral type.
	The calculations are performed using an exponential decay function.

	"""
	
	if not enable_sediment_exposure:
		return growth_rate
	
	else:
		growth_rate_ss = {i: growth_rate[i] * np.exp(-gr_sedi_sus_coeff[i] * current_add_suspended_sediment) for i in coral_type}
		return growth_rate_ss
	



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

##RIO: below is implimented if deposited sediment event happens but cyclones and bleaching dont happen in that year
#impacts of these events are not culumative 
#can test out impact of converting to changes in coral cover to different proportions of dead coral and sediment
## could do a sensitivity analysis later to see if converting all lost coral to dead coral (as it currently is) or to a proportion of sediment is better

def calculate_benthos_after_pcm_ds(change_branching_cover, change_foliose_cover, change_other_cover):
	"""
	This function adjusts the benthic cover values according to the changes caused by a depsoited sediment event. The 
	changes in branching cover, foliose cover, and other cover are converted to dead coral and added to the dead coral cover.
	
	Parameters
	----------
	change_branching_cover : float
		The change in the branching cover due to the  event.
	change_foliose_cover : float
		The change in the foliose cover due to the  event.
	change_other_cover : float
		The change in the other cover types due to the  event.

	Returns
	-------
	None

	"""
	
	if change_branching_cover < 0:
		opts.current_benthic_cover['dead_coral'] += abs(change_branching_cover)
		
	else:
		w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_branching_cover)
		opts.current_benthic_cover['hard_substrate'] -= w_hs
		opts.current_benthic_cover['dead_coral'] -= w_dc
		opts.current_benthic_cover['turfing_algae'] -= w_tf
		
	if change_foliose_cover < 0:
		opts.current_benthic_cover['dead_coral'] += abs(change_foliose_cover)
		
		
	else:
		w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_foliose_cover)
		opts.current_benthic_cover['hard_substrate'] -= w_hs
		opts.current_benthic_cover['dead_coral'] -= w_dc
		opts.current_benthic_cover['turfing_algae'] -= w_tf
		
	if change_other_cover < 0:
		opts.current_benthic_cover['dead_coral'] += abs(change_other_cover)
		
		
	else:
		w_hs, w_dc, w_tf = split_w(opts.current_benthic_cover['hard_substrate'], opts.current_benthic_cover['dead_coral'], opts.current_benthic_cover['turfing_algae'], opts.available_substrate_percentage, change_other_cover)
		opts.current_benthic_cover['hard_substrate'] -= w_hs
		opts.current_benthic_cover['dead_coral'] -= w_dc
		opts.current_benthic_cover['turfing_algae'] -= w_tf


#===========================================================================================
#Assistant functions for exporting

def output_title(base: str, iteration: int, separator: str = "_", zero_pad: int = 3) -> str:
	"""
	Build labels like 'Run_1', 'Run_002', etc.

	base: prefix text, e.g. "Run"
	iteration: the run number (1-based)
	separator: string between base and number
	zero_pad: width for zero-padding (0 = no padding)
	"""
	num = str(int(iteration)).zfill(zero_pad) if zero_pad > 0 else str(int(iteration))
	return f"{base}{separator}{num}"

#create ID that includes current date
def make_run_id(folder: str, tz: str = "Australia/Brisbane", width: int = 2) -> str:
	"""Return a run id like 'YYYYMMDD_01', 'YYYYMMDD_02', ..."""
	date_str = datetime.now(ZoneInfo(tz)).strftime("%Y%m%d")
	pat = re.compile(rf"^{date_str}_(\d+)")
	nums = []
	for name in os.listdir(folder):
		m = pat.match(name)
		if m:
			nums.append(int(m.group(1)))
	n = (max(nums) + 1) if nums else 1
	return f"{date_str}_{n:0{width}d}"

#Fill missing columns in the data by averaging nearest neighbours:
def fill_nans_columnwise(df, year_col: str | None = 'Year',
						 make_full_years: bool = False,
						 fallback: str = 'mean',
						 return_mask: bool = True):
	"""
	Fill NaNs independently in each numeric column and (optionally) return a mask
	of cells that were created (filled).
	"""
	out = df.copy()

	# Optionally create missing year rows
	if year_col and year_col in out.columns and make_full_years:
		y = pd.to_numeric(out[year_col], errors='coerce')
		y_min, y_max = int(y.min()), int(y.max())
		out = out.set_index(year_col).reindex(range(y_min, y_max + 1))
		out.index.name = year_col
		out = out.reset_index()

	# Pick numeric-like columns (don’t touch year col)
	num_cols = [c for c in out.columns if c != (year_col or '')]
	num_cols = [c for c in num_cols
				if pd.api.types.is_numeric_dtype(out[c]) or
				   pd.to_numeric(out[c], errors='coerce').notna().any()]

	# Track where cells were originally NaN
	orig_nan = pd.DataFrame(False, index=out.index, columns=num_cols)

	for c in num_cols:
		s = pd.to_numeric(out[c], errors='coerce')
		orig_nan[c] = s.isna()

		# isolated single NaNs -> avg of neighbors
		mask = s.isna()
		prev, nxt = s.shift(1), s.shift(-1)
		isolated = mask & prev.notna() & nxt.notna()
		s.loc[isolated] = (prev.loc[isolated] + nxt.loc[isolated]) / 2.0

		# interpolate remaining (handles long gaps + edges)
		s = s.interpolate(method='linear', limit_direction='both')

		# fallback so no NaNs remain (handles all-NaN columns)
		if s.isna().any():
			if fallback == 'mean' and s.notna().any():
				s = s.fillna(s.mean())
			elif fallback == 'ffill':
				s = s.ffill().bfill()
			else:  # 'zero'
				s = s.fillna(0)

		out[c] = s.astype(float)

	if not return_mask:
		return out

	# created mask = was NaN before AND has a value now
	created_mask = pd.DataFrame(False, index=out.index, columns=out.columns)
	for c in num_cols:
		created_mask[c] = orig_nan[c] & out[c].notna()

	return out, created_mask

def plot_bubble_chart_from_dataframe(df, title, category_col='MG', year_interval=4, bubble_scale=100, parallel_offset = 1.2, figsize=(18, 12), x_spacing=1.5, y_spacing=5):
	"""
	Create a bubble chart showing population distribution by category over time.
	
	Parameters:
	- df: DataFrame with columns for category, year, and bin data (percentages)
	- y_label: Label for y-axis (default: "Bin Size")
	- y_unit: Unit for y-axis (default: "cm")
	- category_col: Column name for categories (default: 'MG')
	- year_interval: Select every Nth year (default: 4 for every 4th year)
	- year_start: Starting year for converting model years to actual years (default: 2000)
	- bubble_scale: Multiplier for bubble sizes (default: 100)
	
	Expected DataFrame structure:
	- Column 0: Category (MG)
	- Column 1: Year (model years: 0, 1, 2, 3, ...)
	- Columns 2+: Bin diameter columns (5, 10, 15, ..., 100) with percentages
	"""
	
	# Configuration parameters
	parallel_offset = parallel_offset  # Horizontal offset between categories
	
	# Get actual bin diameter columns (columns 2 onwards contain bin data)
	bin_columns = df.columns[2:].tolist()  # Skip category and year columns
	
	# Extract bin diameters from column names (assuming they contain numeric values)
	bin_diameters = []
	for col in bin_columns:
		# Extract numeric value from column name (e.g., "Bin_5" -> 5, "5cm" -> 5, etc.)
		import re
		numbers = re.findall(r'\d+', str(col))
		if numbers:
			bin_diameters.append(float(numbers[0]))
		else:
			# If no number found, use column index * 5 (assuming 5cm increments)
			bin_diameters.append((len(bin_diameters)) * 5 + 5)
	
	MaxBinId = len(bin_diameters)
	
	# Get unique years and categories from the data
	if 'Year' in df.columns:
		all_years_list = sorted(df['Year'].unique().tolist())
	else:
		all_years_list = [0, 4, 7, 11]
	
	# Select every Nth year to reduce clutter - filter by year values, not array indices
	if year_interval > 1:
		# Select years that are multiples of the interval
		years = [year for year in all_years_list if year % year_interval == 0]
	else:
		# If interval is 1, use all years
		years = all_years_list.copy()
	
	print(f"All years in data: {all_years_list}")
	print(f"Selected years (multiples of {year_interval}): {years}")
	
	# Convert model years to actual years
	actual_years = [year + year_start for year in years]
	print(f"Actual years for display: {actual_years}")
	
	categories = sorted(df[category_col].unique()) if category_col in df.columns else ['Branching', 'Foliose', 'Other']
	
	# Color schemes for each category
	color_palette = ["#1F77B4", "#C026D3", "#FF7F0E"]  # blue, fuchsia, orange
	colors = {}
	for i, category in enumerate(categories):
		base_color = color_palette[i % len(color_palette)]
		colors[category] = {
			'mean': base_color,
			'std': base_color + '40'  # Add transparency for std
		}
	
	# Calculate category offsets for parallel display
	category_offsets = {}
	if len(categories) == 1:
		category_offsets[categories[0]] = 0
	elif len(categories) == 2:
		category_offsets[categories[0]] = -parallel_offset/2
		category_offsets[categories[1]] = parallel_offset/2
	else:  # 3 or more categories
		for i, cat in enumerate(categories):
			category_offsets[cat] = (i - (len(categories)-1)/2) * parallel_offset
	
	# Prepare data for plotting
	plot_data = []
	
	for category in categories:
		for model_year in years:  # Use model years for filtering data
			actual_year = model_year + year_start  # Convert to actual year for positioning
			# Filter data for this category and model year
			year_df = df[(df[category_col] == category) & (df['Year'] == model_year)]
			
			if not year_df.empty:
				# Get bin data (columns 2 onwards contain the percentage data)
				bin_data = year_df.iloc[:, 2:]  # All bin columns
				
				# Calculate mean and std for each bin across all rows for this category/year
				mean_values = bin_data.mean(axis=0)
				std_values = bin_data.std(axis=0)
				
				# Create data points for each bin using actual bin diameters
				for bin_idx, (col_name, mean_val, std_val) in enumerate(zip(bin_columns, mean_values, std_values)):
					if bin_idx < len(bin_diameters):
						# Convert to float and check if valid
						try:
							mean_val = float(mean_val) if pd.notna(mean_val) else 0
							std_val = float(std_val) if pd.notna(std_val) else 0
						except (ValueError, TypeError):
							mean_val = 0
							std_val = 0
						
						# Always define position variables
						x_pos = actual_year + category_offsets[category]  # Use actual year for positioning
						y_pos = bin_diameters[bin_idx]  # Use actual bin diameter from column
						
						if mean_val > 0:
							# Add mean point (main bubble)
							plot_data.append({
								'x': x_pos,
								'y': y_pos,
								'size': mean_val,
								'color': colors[category]['mean'],
								'category': category,
								'year': actual_year,  # Store actual year
								'type': 'mean',
								'bin_idx': bin_idx
							})
						
						# Add std point (background shading) if std exists
						if std_val > 0:
							plot_data.append({
								'x': x_pos,
								'y': y_pos,
								'size': std_val,
								'color': colors[category]['std'],
								'category': category,
								'year': actual_year,  # Store actual year
								'type': 'std',
								'bin_idx': bin_idx
							})
	
	# Create the plot
	fig, ax = plt.subplots(figsize=(15, 10))
	
	# Group data by position for proper std shading around mean
	position_data = {}
	for point in plot_data:
		key = (point['x'], point['y'], point['category'])
		if key not in position_data:
			position_data[key] = {'mean': None, 'std': None}
		position_data[key][point['type']] = point
	
	# Plot standard deviation as shading around mean bubbles
	for (x, y, category), data in position_data.items():
		if data['mean'] is not None:
			mean_point = data['mean']
			
			# Plot mean bubble
			ax.scatter(
				mean_point['x'], 
				mean_point['y'], 
				s=float(mean_point['size']) * bubble_scale,  # Ensure float conversion
				c=mean_point['color'],
				alpha=0.8,
				linewidth=0.5,
				edgecolors='black',
				zorder=2,
				label=f'{category}' if mean_point['bin_idx'] == 0 and mean_point['year'] == actual_years[0] else ""
			)
			
			# Plot std shading around the mean if std data exists
			if data['std'] is not None:
				std_point = data['std']
				# Create larger bubble for std shading
				std_size = float(mean_point['size']) + float(std_point['size'])  # Ensure float conversion
				
				ax.scatter(
					std_point['x'], 
					std_point['y'], 
					s=std_size * bubble_scale,  # Use configurable scale factor
					c=std_point['color'],
					alpha=0.2,  # Very light for background
					edgecolors='none',
					zorder=1
				)
	
	# Add vertical lines to separate years (optional) - position at actual years
	if len(actual_years) > 1:
		for i in range(len(actual_years)-1):
			separator_x = (actual_years[i] + actual_years[i+1]) / 2
			ax.axvline(x=separator_x, color='lightgray', linestyle='--', alpha=0.5)
	
	# Customize plot appearance
	ax.set_xlabel('Year', fontsize=14, fontweight='bold')
	ax.set_ylabel(f'Bin diameter (cm)', fontsize=14, fontweight='bold')
	
	# Set x-axis ticks and labels with actual years - more robust approach
	ax.set_xticks(actual_years)
	
	# Create distinct labels for each year
	year_labels = []
	for actual_year in actual_years:
		year_labels.append(str(int(actual_year)))
	
	ax.set_xticklabels(year_labels, rotation=0, ha='center')
	
	# Force the x-axis to show the full range with proper spacing
	if len(actual_years) > 1:
		year_span = max(actual_years) - min(actual_years)
		margin = max(1, year_span * 0.1)  # 10% margin
		ax.set_xlim(min(actual_years) - margin, max(actual_years) + margin)
	else:
		ax.set_xlim(actual_years[0] - 1, actual_years[0] + 1)
	
	# Ensure ticks are visible and properly spaced
	ax.tick_params(axis='x', labelsize=12)
	
	# Update title to reflect actual year range
	if len(actual_years) > 1:
		year_range = f"({actual_years[0]}-{actual_years[-1]})"
	else:
		year_range = f"({actual_years[0]})"
	
	ax.set_title(f'{title} by Category Over Time {year_range}\n(Bubble size represents {title})', fontsize=16, fontweight='bold', pad=20)

# Set y-axis to show actual bin diameters with custom spacing
	if len(bin_diameters) > 0:
		ax.set_ylim(min(bin_diameters) - y_spacing, max(bin_diameters) + y_spacing)
		# Use actual bin diameters for y-axis ticks
		ax.set_yticks(bin_diameters)
		ax.set_yticklabels([f'{int(diameter)}' for diameter in bin_diameters]) 

	# Add grid for better readability
	ax.grid(True, alpha=0.3, linestyle='-', linewidth=0.5)
	
	# Create legend
	legend_elements = []
	for category in categories:
		legend_elements.append(plt.Line2D([0], [0], marker='o', color='w', 
										markerfacecolor=colors[category]['mean'], 
										markersize=10, label=f'{category}',
										markeredgecolor='black', markeredgewidth=0.5))
	
	# Add legend with better positioning
	cat_legend = ax.legend(
	handles=legend_elements,
	loc='upper right',
	bbox_to_anchor=(0.99, 1.00),   # (x, y) in axes coords
	bbox_transform=ax.transAxes,   # interpret bbox in axes coords
	frameon=True,
	fancybox=True,
	shadow=True,
	fontsize=12
)

	# Bubble size legend: collect the sizes used for mean bubbles
	_used_sizes = [p['size'] for p in plot_data if p['type'] == 'mean' and p['size'] > 0]

	if _used_sizes:
		vmin = float(min(_used_sizes))
		vmax = float(max(_used_sizes))
	
		# dynamic base = 1/5 of max bubble value
		base = max(vmax / 5.0, 1e-12)
	
		# pick 3 representative values between vmin and vmax
		raw_ticks = np.linspace(vmin, vmax, 3)
	
		# --- neat rounding: choose granularity to keep ~3 significant digits ---
		exp = int(np.floor(np.log10(base)))         # order of magnitude of base
		gran = 10 ** max(exp - 2, 0)                # e.g. base=17729 -> exp=4 -> gran=10**2=100
	
		# snap to nearest multiple of gran
		tick_vals = np.round(raw_ticks / gran) * gran
		tick_vals = np.array(sorted(set(tick_vals)))
		tick_vals[tick_vals <= 0] = gran  # avoid zero-size markers
	
		# fallback if rounding collapsed distincts
		if tick_vals.size < 3:
			mids = [vmin, (vmin + vmax)/2.0, vmax]
			tick_vals = np.array(sorted(set(np.round(np.array(mids)/gran) * gran)))
			tick_vals[tick_vals <= 0] = gran

	# build legend handles with SAME size mapping (s = value * bubble_scale)
	size_handles = [
		ax.scatter([], [], s=float(val) * bubble_scale, color='black', alpha=0.35, edgecolors='black')
		for val in tick_vals
	]

	# pretty labels: integers with commas when gran >= 1; otherwise sensible decimals
	def _fmt(v):
		if gran >= 1:
			return f"{int(v):,}"
		# decimals: number of places based on gran (e.g., gran=0.01 -> 2 dp)
		places = max(0, int(np.ceil(-np.log10(gran))))
		return f"{v:.{places}f}"
		
	size_labels = [_fmt(val) for val in tick_vals]

	size_legend = ax.legend(
		size_handles, size_labels,
		title=f"{title} scale",
		loc="upper right",
		bbox_to_anchor=(0.99, 0.89),      # same x, lower y (under the category legend)
		bbox_transform=ax.transAxes,
		frameon=True, fancybox=True, shadow=False,
		fontsize=11,
		title_fontsize=12,
		borderpad=1.4,      # ↑ makes the legend box itself roomier
		labelspacing=1.5,
		handlelength=2.2,
		handletextpad=0.8,
		borderaxespad=0.0
)
	# keep both legends
	ax.add_artist(cat_legend)

	# Define the graph directory path
	graph_dir = r'output/figures'

	# Save the combined plot to the specified folder
	graph_path = os.path.join(graph_dir, f'{title} bubble_graph.png')
	plt.savefig(graph_path)

	# Adjust layout and display
	plt.tight_layout()
	plt.show()
	
	
	return fig, ax