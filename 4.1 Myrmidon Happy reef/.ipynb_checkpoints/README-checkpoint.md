# Coral Growth and Decline Model in Python

This Jupyter Notebook features a Python implementation of a model for coral growth and decline. The model effectively simulates the growth and mortality dynamics of three distinct types of corals (Branching, Foliose, and Others) across various coral reef scenarios. These scenarios include: (i) an undisturbed condition devoid of external stressors, (ii) a bleaching scenario, and (iii) a cyclone event.

**Key Functionalities:**
- `CoralOptions` class: initializes parameters such as reef area and shape, distribution of brooder and spawner coral cover, egg density, and growth rates. Additionally, it sets up the initial coral cover for each type, crucial for computing the initial surface area.
- `initialize_coral()`: prepares the initial coral cover and surface area for each coral type and initializes several dataframes for storing simulation data.
- `run_yearly_change()`: executes annual changes in coral populations based on input parameters and scenarios. Calculates new populations and surface areas for each coral type, factoring in growth rates, bleaching, cyclone events, mortality, and other variables. This function is essential for driving the yearly changes in coral populations.
- `run_coral_model()`: serves as the primary function to execute the coral model. It first sets up the coral environment using `initialize_coral()`, then calls `run_yearly_change()` to perform the simulation. Finally, it returns a DataFrame containing the results of the coral model after running for a specified number of years.
- `run_multiple_model_iterations()`: runs multiple coral models using the provided inputs.
- `export_to_excel()`: facilitates the export of dataframes into an Excel file.

Additionally, the notebook contains several other supporting functions for counting the new population, calculating the population change, estimating surface areas based on population data, executing yearly growth simulations under varied scenarios, and generating plots.

**Output files:**
Besides the different plots, the simulation generates Excel files as an output. These include:
- Yearly Benthic Cover Distribution: A comprehensive report detailing how benthic cover changes each year.
- Total Coral Cover Over Time: A timeline showing the overall coral cover throughout the simulation years.
- Yearly Coral Population Distribution: A yearly breakdown of the population distribution across different coral types.
- Yearly Coral Surface Area Distribution: A yearly summary of how the surface area is distributed among different coral types.
- Rugosity: An analysis of the habitat's complexity.

The model flowchart is given below
![Model Flowchart](illustrations/model_flowchart.png)

For calculating the initial coral population, we used an algorithm shown below
![Initial coral population estimation algorithm](illustrations/population_estimation_flowchart.png)

## Usage
To use the notebook, users can run the `run_coral_model()` function, specifying their initial parameter data and the desired number of years for the simulation. The Jupyter notebook will then simulate the coral growth and mortality, visualizing the results and generating detailed Excel files for further analysis. Users can adjust the input parameters in the `user_input.py`, such as different initial coral cover percentages or benthic cover.


# Configuration

1. Install anaconda navigator or miniconda to manage the necessary packages. Check the installation guide [here](https://docs.conda.io/en/latest/miniconda.html) for the anaconda navigator or [here](https://docs.conda.io/en/latest/miniconda.html) for miniconda.
2. To setup the environment, create a local clone of the repository. In Terminal, navigate to the folder where you saved the code and run the following command to create a new environment and install the required packages:
    
    $ conda env create -n coral --file environment_windows.yml

Change the 'environment_windows.yml' name to the one that corresponds to your operating system: 'environment_macos.yml' or 'environment_linux.yml'.
    
4. Activate the environment by running:
    
    $ conda activate coral
    
5. To run the program on Jupyter Notebook, type:

    $ jupyter-lab Coral_model_1D.ipynb

6. To deactivate the environment, type:

    $ conda deactivate

# Contributors:
- [Curtin Institute for Data Science (CIDS)](https://computation.curtin.edu.au/)
    - Dagmawi Tadesse (dagmawi.tadesse@curtin.edu.au)
- [Curtin School of Molecular and Life Science](https://www.curtin.edu.au/about/learning-teaching/science-engineering/school-of-molecular-life-sciences/)    
    - Nicola Browne (n.browne@.uq.edu.au)


