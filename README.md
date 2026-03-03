# Coral Growth and Decline Model in Python 
# 03 March 2026

This Jupyter Notebook features a Python implementation of a model for coral growth and decline. The model effectively simulates the growth and mortality dynamics of three distinct types of corals (Branching, Foliose, and Others) across various coral reef scenarios. These scenarios include: (i) an undisturbed condition devoid of external stressors, (ii) a bleaching scenario, and (iii) a cyclone event.

## Usage
The model runs in Python using Jupyter Notebook (or any other software that works with Python code). Below, we provide the instructions for Jupyter only. 

# Step by step guide to use the model:
1. Install Python (https://www.python.org/downloads/) 
2. Through Terminal (installed by default on your computer), install and configure anaconda (or miniconda) distribution to set up the environment and manage necessary packages. Check the installation guide [here](https://docs.conda.io/en/latest/miniconda.html) for the anaconda or [here](https://docs.conda.io/en/latest/miniconda.html) for miniconda.
3. To set up the environment, create a local clone of the GitHub repository. In Terminal, navigate to the folder where you saved the repository clone and run the following command to create a new environment and install the required packages:
    
    $ conda env create -n coral --file environment.yml
    
4. Activate the environment by running:
    
    $ conda activate coral
   
    You should see `(coral)` appear before your username in the command line instead of `(base)`.
    
5. To run the program on Jupyter Notebook, type:

    $ jupyter-lab Coral_model_1D.ipynb

    This will open a browser window with Jupyter Notebook, and you should see your working directory. 

6. To deactivate the environment, type in Terminal:

    $ conda deactivate

    Note that you can operate Terminal through Jupyter Notebook.
   
8. You will see a list of the following files:
   `user_inputs.py`: file with parameters that the user needs to change to match their requirements.  Some are obvious (such as first and last year for the model to run), some are optional such as different initial coral cover percentages or benthic cover (if the user does not have the data, it is possible to use default parameters), some are a choice of `True` or `False` (such as if the user wishes to turn on and off `Bleaching` or `Cyclone` functionalities.
   
   `coral_data_and_custom_parameters.xlsx`: this is a spreadsheet that the user needs to open outside of Jupyter (in any suitable software) to fill in data for real coral cover data (if it exists) or customise some of the parameters that were selected as `True` or `False` in the user_input file. 
   
   `config.py`: file containing configurations and class definitions for the model. It is suggested that users shouldn't try to modify it unless they are experienced in Python, as it can disrupt the model's operation. 
   
   `utils.py`: main model functions file. It is suggested that users shouldn't try to modify it unless they are experienced in Python, as it can disrupt the model's operation. 
   
   `environment.yml`: the environment file that was used to set up the packages.
   
   `Coral_model.ipynb`: the main running file. It contains the execution of functions and produces outputs in the form of Excel spreadsheets and PNG figures in the `outputs` folder. This is the main file that the user needs to operate from. Please note that some of the plots will require the user to enter the exact years they wish to be plotted, it is done directly in this file rather than in the user_input. 

The simplest use of the model is to run the `run_coral_model()` function, specifying their initial parameter data and the desired number of years for the simulation. The Jupyter Notebook will then simulate the coral growth and mortality, visualizing the results and generating detailed Excel files for further analysis. Users can adjust the input parameters in the `user_input.py` and `coral_data_and_custom_parameters.xlsx` spreadsheet to see how different scenarios will affect their reef. 
<b>It is recommended to restart Kernel from the Kernel menu in Jupyter every time before running the model to ensure all functions and any changes to user input files are pulled in correctly.<b> 

**Key Functionalities:**
- `CoralOptions` class: initializes parameters such as reef area and shape, distribution of brooder and spawner coral cover, egg density, and growth rates. Additionally, it sets up the initial coral cover for each type, crucial for computing the initial surface area.
- `initialize_coral()`: prepares the initial coral cover and surface area for each coral type and initializes several dataframes for storing simulation data.
- `run_yearly_change()`: executes annual changes in coral populations based on input parameters and scenarios. Calculates new populations and surface areas for each coral type, factoring in growth rates, bleaching, cyclone events, mortality, and other variables. This function is essential for driving the yearly changes in coral populations.
- `run_coral_model()`: serves as the primary function to execute the coral model. It first sets up the coral environment using `initialize_coral()`, then calls `run_yearly_change()` to perform the simulation. Finally, it returns a DataFrame containing the results of the coral model after running for a specified number of years.
- `run_multiple_model_iterations_total_cover()`: runs multiple coral models using the provided inputs to output total coral cover under different conditions.
- `run_model_iterations_all_parameters()`: runs multiple iterations of the model to produce a range of parameters for coral population size distribution by morphology group.
- `export_to_excel()`: facilitates the export of dataframes into an Excel file.

Additionally, the notebook contains several other supporting functions for counting the new population, calculating the population change, estimating surface areas based on population data, executing yearly growth simulations under varied scenarios, and generating plots.

**Output files:**
Besides the different plots, the simulation generates Excel files as an output. These include:
- Yearly Benthic Cover Distribution: A comprehensive report detailing how benthic cover changes each year.
- Total Coral Cover Over Time: A timeline showing the overall coral cover throughout the simulation years.
- Yearly Coral Population Distribution: A yearly breakdown of the population distribution across different coral types.
- Yearly Coral Surface Area Distribution: A yearly summary of how the surface area is distributed among different coral types.
- Rugosity: An analysis of the habitat's complexity.

  
## Contributors:
- [Curtin Institute for Data Science (CIDS)](https://computation.curtin.edu.au/)
    - Dagmawi Tadesse (dagmawi.tadesse@curtin.edu.au)
- [Curtin School of Molecular and Life Science](https://www.curtin.edu.au/about/learning-teaching/science-engineering/school-of-molecular-life-sciences/)  
    - Nicola Browne (n.browne@.uq.edu.au)


