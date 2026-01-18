import pytest
import numpy as np
from coral_model.core import CoralModel
from coral_model.parameters import CoralParameters

def test_model_initialization():
    model = CoralModel()
    assert model.year == 0
    assert model.total_cover > 0
    assert model.population.sum() > 0

def test_run_simulation():
    params = CoralParameters(year_start=2000, year_end=2010)
    model = CoralModel(params=params)
    model.run()
    
    assert model.year == 10
    assert len(model.history_cover) == 11 # 0 to 10
    
    # Check logic
    df = model.get_results_df()
    assert not df.empty
    assert 'total_cover' in df.columns

def test_bleaching_impact():
    """Test that huge bleaching event reduces cover."""
    params = CoralParameters(
        year_end=2002, 
        dhw_years={1: 20}, # Huge bleaching in year 1
        enable_recruitment=False, # Isolate mortality
        growth_coefficient_branching=0.0,
        growth_coefficient_foliose=0.0,
        growth_coefficient_other=0.0
    )
    model = CoralModel(params=params)
    
    # Run step 0 (init)
    init_cover = model.total_cover
    
    # Run step 1 (year 1)
    model.step()
    
    # Expect drop (no growth, only shrinkage/mortality)
    assert model.total_cover < init_cover
