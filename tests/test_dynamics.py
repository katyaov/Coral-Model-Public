import pytest
import numpy as np
from coral_model.parameters import CoralParameters, CoralConstants
from coral_model.dynamics import CoralDynamics

@pytest.fixture
def params():
    return CoralParameters()

@pytest.fixture
def constants():
    return CoralConstants()

def test_growth_no_mortality(params, constants):
    """Test that population grows (moves to larger bins) without mortality."""
    # Setup single bin population
    pop = np.zeros((3, constants.MAX_BIN_ID), dtype=int)
    pop[0, 5] = 1000 # 1000 branching in bin 5 (25-30cm)
    
    growth_rates = np.ones((3, constants.MAX_BIN_ID)) * 5.0 # 5cm growth
    pcm = np.zeros((3, constants.MAX_BIN_ID))
    wcm = np.zeros((3, constants.MAX_BIN_ID))
    
    # 5cm growth = 1 bin size
    # Should move to bin 6 (mostly) and some to bin 7 due to spread at edge
    
    new_pop = CoralDynamics.grow_population(
        pop, growth_rates, pcm, wcm, 
        current_total_cover=0.0, 
        params=params, constants=constants
    )
    
    # Check conservation
    assert new_pop.sum() == 1000
    
    # Check shift (Peak should be in bin 6)
    assert new_pop[0, 6] > 900
    assert new_pop[0, 5] == 0
    # Allow some leakage to bin 7 due to particle edge (35.0cm -> bin 7 start)
    assert new_pop[0, 7] + new_pop[0, 6] == 1000

def test_wcm_mortality(params, constants):
    """Test whole colony mortality reduces population."""
    pop = np.zeros((3, constants.MAX_BIN_ID), dtype=int)
    pop[0, 5] = 1000
    
    growth_rates = np.zeros((3, constants.MAX_BIN_ID)) # No growth
    pcm = np.zeros((3, constants.MAX_BIN_ID))
    wcm = np.ones((3, constants.MAX_BIN_ID)) * 50.0 # 50% mortality (Code expects percentage)
    
    new_pop = CoralDynamics.grow_population(
        pop, growth_rates, pcm, wcm, 
        current_total_cover=0.0, 
        params=params, constants=constants
    )
    
    # Check conservation of survivors (500)
    assert abs(new_pop.sum() - 500) < 5 # Allow rounding errors if any
    
    # Check location (Bin 5 mostly, maybe edge to bin 6)
    assert new_pop[0, 5] + new_pop[0, 6] == new_pop.sum()

def test_pcm_shrinkage(params, constants):
    """Test partial mortality shrinks colonies."""
    pop = np.zeros((3, constants.MAX_BIN_ID), dtype=int)
    pop[0, 5] = 1000 # Bin 5: 25-30cm
    
    growth_rates = np.zeros((3, constants.MAX_BIN_ID))
    pcm = np.ones((3, constants.MAX_BIN_ID)) * 75.0 # 75% surface loss
    wcm = np.zeros((3, constants.MAX_BIN_ID))
    
    # Diameter * sqrt(1 - 0.75) = Diameter * sqrt(0.25) = Diameter * 0.5
    # [25, 30] -> [12.5, 15]
    # Bin size 5. Bin 0: 0-5, 1: 5-10, 2: 10-15.
    # Should land in Bin 2 (10-15) and maybe Bin 3 edge.
    
    new_pop = CoralDynamics.grow_population(
        pop, growth_rates, pcm, wcm, 
        current_total_cover=0.0, 
        params=params, constants=constants
    )
    
    # Check bin distribution
    assert new_pop[0, 2] > 0
    assert new_pop[0, 5] == 0
    assert new_pop.sum() == 1000 # Mass conserved (count)
