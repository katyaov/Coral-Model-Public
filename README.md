# Coral Growth/Decline Model

A demographic model simulating coral reef dynamics under various environmental stressors including bleaching events and cyclones. The model tracks three coral types (Branching, Foliose, and Other) through size-structured populations, accounting for recruitment, growth, mortality, and competition dynamics.

## Quick Start

### Windows Users
1. **Install dependencies** (one-time setup):
   - Double-click `install_deps.bat`
   - This installs `uv` (package manager) and all required dependencies

2. **Launch dashboard**:
   - Double-click `launch_dashboard.bat`
   - Browser opens automatically to `http://127.0.0.1:8050`

### Manual Installation (Linux/Mac)
```bash
# Install uv package manager
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies from pyproject.toml
uv sync

# Launch dashboard
uv run app.py
```

## What It Does

The model simulates coral population dynamics using a size-structured approach. Key features:
- **Size-based demographics**: Tracks coral colonies across 200 size classes (1-200 cm diameter)
- **Recruitment**: Simulates larval settlement influenced by available substrate and brooder/spawner dynamics
- **Growth & mortality**: Applies annual growth rates and background mortality
- **Stressor impacts**: Models bleaching (degree heating weeks) and cyclone disturbances
- **Interactive dashboard**: Web-based interface for parameter adjustment and real-time visualization

## Model Outputs
- Coral cover trajectories by type
- Size-frequency distributions over time  
- Benthic composition (coral, algae, rubble, sand)
- Rugosity index (habitat complexity)
- Population size-structure heatmaps


# Contributors:
- [Curtin Institute for Data Science (CIDS)](https://computation.curtin.edu.au/)
    - Dagmawi Tadesse (dagmawi.tadesse@curtin.edu.au)
- [Curtin School of Molecular and Life Science](https://www.curtin.edu.au/about/learning-teaching/science-engineering/school-of-molecular-life-sciences/)    
    - Nicola Browne (nicola.browne@curtin.edu.au)


