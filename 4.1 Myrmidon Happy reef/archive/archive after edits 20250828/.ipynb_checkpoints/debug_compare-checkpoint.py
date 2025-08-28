import numpy as np
import pandas as pd
import random
from copy import deepcopy

# Import old and new configs
import config_old as old_cfg
import config as new_cfg
import utils as new_utils

# Import your old utils if they exist (otherwise, mock old run_yearly_change)
import utils_old  # <-- If you have a separate old utils.py, import it here

# === Set deterministic randomness so results are reproducible ===
random.seed(42)
np.random.seed(42)

# === Run only 1 year ===
YEARS = 1

# Make deep copies so we don't modify the originals accidentally
old_opts = deepcopy(old_cfg.opts)
new_opts = deepcopy(new_cfg.opts)

# Prepare the initial PSD dataframe for both models
PSD_T0_old = deepcopy(new_utils.PSD_T0)  # assuming same initial state
PSD_T0_new = deepcopy(new_utils.PSD_T0)

# Run ONE step of both models manually to compare internals
print("🔍 Starting side-by-side debug for 1 year...\n")

# ----- OLD MODEL -----
old_utils.opts = old_opts
old_result = old_utils.run_yearly_change(PSD_T0_old, YEARS)

# ----- NEW MODEL -----
new_utils.opts = new_opts
new_result = new_utils.run_yearly_change(PSD_T0_new, YEARS)

print("\n=== Comparing year 1 results ===\n")

# Pick key variables to compare step-by-step
def compare_arrays(name, old_val, new_val):
    old_arr = np.array(old_val)
    new_arr = np.array(new_val)
    if not np.allclose(old_arr, new_arr, atol=1e-6):
        print(f"⚠️ MISMATCH in {name}!")
        print(f"   OLD: {old_arr[:10]}")  # show first 10 values only
        print(f"   NEW: {new_arr[:10]}")
        return False
    return True

# Compare growth rate
compare_arrays("growth_rate", old_utils.growth_rate, new_utils.growth_rate)

# Compare PCM and WCM rates
compare_arrays("PCM_rates", old_utils.PCM_rates, new_utils.PCM_rates)
compare_arrays("WCM_rates", old_utils.WCM_rates, new_utils.WCM_rates)

# Compare population after 1 year
compare_arrays("Population Branching", 
              old_utils.opts.current_population_df['Branching'],
              new_utils.opts.current_population_df['Branching'])

compare_arrays("Population Foliose", 
              old_utils.opts.current_population_df['Foliose'],
              new_utils.opts.current_population_df['Foliose'])

compare_arrays("Population Other", 
              old_utils.opts.current_population_df['Other'],
              new_utils.opts.current_population_df['Other'])

# Compare surface area after 1 year
compare_arrays("Surface Area Branching", 
              old_utils.opts.current_surface_area_df['Branching'],
              new_utils.opts.current_surface_area_df['Branching'])

# Compare total coral cover
if not np.isclose(old_utils.opts.current_total_coral_cover, new_utils.opts.current_total_coral_cover, atol=1e-6):
    print(f"⚠️ MISMATCH in total coral cover!")
    print(f"   OLD: {old_utils.opts.current_total_coral_cover}")
    print(f"   NEW: {new_utils.opts.current_total_coral_cover}")

print("\n✅ Debug comparison complete!")
