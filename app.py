from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, Tuple

import pandas as pd
import plotly.express as px
import plotly.io as pio
from flask import Flask, request, render_template_string, send_from_directory

from coral_model import CoralModel, CoralParameters, CoralVisualizations, run_ensemble

app = Flask(__name__)

PLOTLY_CDN = "https://cdn.plot.ly/plotly-2.27.0.min.js"

DEFAULT_DHW = {5: 8, 12: 6, 20: 12, 35: 8}
DEFAULT_CYCLONE = {15: [1, 40], 28: [2, 106], 35: [4, 25], 42: [3, 258]}


def parse_json_field(text: str, fallback: Dict[str, Any]) -> Tuple[Dict[str, Any], str | None]:
    if not text.strip():
        return fallback, None
    try:
        data = json.loads(text)
        if not isinstance(data, dict):
            return fallback, "Expected a JSON object (dictionary)."
        return data, None
    except json.JSONDecodeError as exc:
        return fallback, f"Invalid JSON: {exc.msg}"


def build_params_from_request(form: Dict[str, Any]) -> Tuple[CoralParameters | None, Dict[str, Any]]:
    errors = {}

    def get_float(name: str, default: float) -> float:
        raw = form.get(name, str(default))
        try:
            return float(raw)
        except ValueError:
            errors[name] = f"Invalid number for {name}."
            return default

    def get_int(name: str, default: int) -> int:
        raw = form.get(name, str(default))
        try:
            return int(raw)
        except ValueError:
            errors[name] = f"Invalid integer for {name}."
            return default

    def get_bool(name: str) -> bool:
        return form.get(name) in ["on", "true", "True", True]

    year_start = get_int("year_start", 2000)
    year_end = get_int("year_end", 2050)

    dhw_years_text = form.get("dhw_years", json.dumps(DEFAULT_DHW, indent=2))
    cyclone_years_text = form.get("cyclone_years", json.dumps(DEFAULT_CYCLONE, indent=2))

    dhw_years, dhw_err = parse_json_field(dhw_years_text, DEFAULT_DHW)
    cyclone_years, cyc_err = parse_json_field(cyclone_years_text, DEFAULT_CYCLONE)
    if dhw_err:
        errors["dhw_years"] = dhw_err
    if cyc_err:
        errors["cyclone_years"] = cyc_err

    def normalize_dhw_years(raw: Dict[str, Any]) -> Dict[int, float]:
      normalized = {}
      for key, value in raw.items():
        try:
          year = int(key)
          normalized[year] = float(value)
        except (TypeError, ValueError):
          errors["dhw_years"] = "DHW JSON must map years to numeric values."
          return DEFAULT_DHW
      return normalized

    def normalize_cyclone_years(raw: Dict[str, Any]) -> Dict[int, list]:
      normalized = {}
      for key, value in raw.items():
        try:
          year = int(key)
          if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise ValueError
          normalized[year] = [float(value[0]), float(value[1])]
        except (TypeError, ValueError):
          errors["cyclone_years"] = "Cyclone JSON must map years to [severity, distance]."
          return DEFAULT_CYCLONE
      return normalized

    if not errors:
      dhw_years = normalize_dhw_years(dhw_years)
      cyclone_years = normalize_cyclone_years(cyclone_years)

    params = CoralParameters(
        year_start=year_start,
        year_end=year_end,
        reef_area=get_float("reef_area", 1000.0),
        reef_shape=get_int("reef_shape", 5),
        reef_exposure=form.get("reef_exposure", "protected"),
        macro_algae_cover=get_float("macro_algae_cover", 3.5),
        rubble_cover=get_float("rubble_cover", 1.0),
        sediment_cover=get_float("sediment_cover", 2.9),
        initial_coral_cover={
            "Branching": get_float("cover_branching", 1.8),
            "Foliose": get_float("cover_foliose", 6.9),
            "Other": get_float("cover_other", 11.9),
        },
        initial_brooder_cover=get_float("brooder_cover", 0.9),
        initial_spawner_cover=[
            get_float("spawner_bf_cover", 7.8),
            get_float("spawner_other_cover", 11.9),
        ],
        enable_bleaching=get_bool("enable_bleaching"),
        enable_cyclone=get_bool("enable_cyclone"),
        enable_recruitment=get_bool("enable_recruitment"),
        enable_recruitment_noise=get_bool("enable_recruitment_noise"),
        dhw_years=dhw_years,
        cyclone_years=cyclone_years,
        space_limitation_exponent=get_float("space_limitation_exponent", 1.0),
    )

    if errors:
        return None, errors
        
    return params, {}


def figure_to_div(fig) -> str:
  return pio.to_html(fig, include_plotlyjs="cdn", full_html=False)


def build_summary_tables(model: CoralModel) -> Tuple[str, str, str]:
    df = model.get_results_df()
    last = df.tail(1).copy()
    last.index = ["Final Year"]

    cover_table = last[["year", "total_cover", "Branching", "Foliose", "Other"]].rename(
        columns={
            "year": "Year",
            "total_cover": "Total Cover (%)",
            "Branching": "Branching (%)",
            "Foliose": "Foliose (%)",
            "Other": "Other (%)",
        }
    )

    pop_history = model.history_population
    final_pop = pop_history[-1]
    pop_summary = pd.DataFrame(
        {
            "Type": ["Branching", "Foliose", "Other"],
            "Population (count)": final_pop.sum(axis=1).astype(int),
        }
    )

    cover_html = cover_table.to_html(classes="table table-sm table-striped", border=0)
    pop_html = pop_summary.to_html(classes="table table-sm table-striped", border=0, index=False)
    tail_html = df.tail(10).to_html(classes="table table-sm table-striped", border=0, index=False)
    return cover_html, pop_html, tail_html


def build_figures(model: CoralModel) -> Dict[str, str]:
    figs = {}

    cover_fig = CoralVisualizations.plot_cover_history(model)
    figs["cover"] = figure_to_div(cover_fig)

    heat_branch = CoralVisualizations.plot_demographic_heatmap(model, "Branching")
    heat_foliose = CoralVisualizations.plot_demographic_heatmap(model, "Foliose")
    heat_other = CoralVisualizations.plot_demographic_heatmap(model, "Other")

    figs["heat_branch"] = figure_to_div(heat_branch)
    figs["heat_foliose"] = figure_to_div(heat_foliose)
    figs["heat_other"] = figure_to_div(heat_other)

    df = model.get_results_df()
    long_df = df.melt(id_vars="year", value_vars=["Branching", "Foliose", "Other"], var_name="Type", value_name="Cover")
    try:
        # Use relative (100%) normalization to show community shifts
        bar = px.area(
            long_df, 
            x="year", 
            y="Cover", 
            color="Type", 
            groupnorm='percent',
            title="Relative Community Structure (Proportional Abundance)", 
            template="plotly_white",
            color_discrete_map={'Branching': 'blue', 'Foliose': 'green', 'Other': 'orange'}
        )
        bar.update_layout(yaxis_title="Rel. Abundance (%)", hovermode="x unified")
        figs["composition"] = figure_to_div(bar)
    except Exception:
        # Handle cases where data might be empty
        figs["composition"] = ""

    totals = df[["Branching", "Foliose", "Other"]].iloc[-1]
    try:
        pie = px.pie(values=totals, names=totals.index, title="Final Cover Composition", hole=0.4)
        figs["final_pie"] = figure_to_div(pie)
    except Exception:
        figs["final_pie"] = ""
        
    # NEW Visualizations
    benthic = CoralVisualizations.plot_benthic_stack(model)
    figs["benthic"] = figure_to_div(benthic)
    
    rugosity = CoralVisualizations.plot_rugosity(model)
    figs["rugosity"] = figure_to_div(rugosity)
    
    psd_comp = CoralVisualizations.plot_psd_comparison(model)
    figs["psd_comp"] = figure_to_div(psd_comp)

    return figs


TEMPLATE = """
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Coral Model Dashboard</title>
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" />
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"></script>
  <style>
    body { background: #f8f9fb; }
    .hero { background: linear-gradient(135deg, #0ea5e9, #22c55e); color: white; border-radius: 16px; margin-bottom: 20px; }
    .card { border-radius: 14px; box-shadow: 0 4px 15px rgba(2, 6, 23, 0.05); border: none; margin-bottom: 20px; }
    .card h5 { border-bottom: 1px solid #eee; padding-bottom: 15px; margin-bottom: 20px; color: #1e293b; font-weight: 600; }
    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; font-size: 0.85rem; }
    textarea { min-height: 150px; }
    .nav-tabs .nav-link { color: #64748b; }
    .nav-tabs .nav-link.active { color: #0ea5e9; font-weight: 600; border-bottom: 3px solid #0ea5e9; }
    .badge-soft { background-color: #e0f2fe; color: #0284c7; padding: 5px 10px; border-radius: 6px; font-weight: 500;}
  </style>
</head>
<body>
<div class="container-fluid py-4 px-4">
  <div class="hero p-4">
    <div class="d-flex justify-content-between align-items-center">
      <div>
        <h1 class="h3 fw-bold">ReefSim: Coral Dynamics Dashboard</h1>
        <p class="mb-0 opacity-75">Advanced visualization for coral demographic modelling and stressor analysis.</p>
      </div>
      <div>
        <a href="/docs" target="_blank" class="btn btn-sm btn-light text-primary fw-bold me-2 shadow-sm">Documentation</a>
        <span class="badge bg-white text-dark shadow-sm">{{ 'Ensemble Mode' if form.mode == 'ensemble' else 'Single Run' }}</span>
      </div>
    </div>
  </div>

  <div class="row">
    <!-- Sidebar Controls -->
    <div class="col-lg-3">
      <form method="post">
        <div class="accordion mb-3" id="controlsAccordion">
          
          <!-- Simulation Settings -->
          <div class="accordion-item card mb-2">
            <h2 class="accordion-header">
              <button class="accordion-button" type="button" data-bs-toggle="collapse" data-bs-target="#collapseSim" aria-expanded="true">
                Simulation Settings
              </button>
            </h2>
            <div id="collapseSim" class="accordion-collapse collapse show">
              <div class="accordion-body">
                <div class="mb-2">
                  <label class="form-label small fw-bold">Mode</label>
                  <select class="form-select form-select-sm" name="mode">
                    <option value="single" {% if form.mode == 'single' %}selected{% endif %}>Single Run</option>
                    <option value="ensemble" {% if form.mode == 'ensemble' %}selected{% endif %}>Ensemble (Multiple Iterations)</option>
                  </select>
                </div>
                <div class="mb-2">
                  <label class="form-label small text-muted">Iterations (Ensemble only)</label>
                  <input type="number" class="form-control form-control-sm" name="n_iterations" value="{{ form.n_iterations }}" />
                </div>
                <div class="row g-2">
                    <div class="col-6">
                        <label class="form-label small text-muted">Start Year</label>
                        <input class="form-control form-control-sm" name="year_start" value="{{ form.year_start }}" />
                    </div>
                    <div class="col-6">
                        <label class="form-label small text-muted">End Year</label>
                        <input class="form-control form-control-sm" name="year_end" value="{{ form.year_end }}" />
                    </div>
                </div>
              </div>
            </div>
          </div>
          
          <!-- Ecology -->
          <div class="accordion-item card mb-2">
            <h2 class="accordion-header">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseEco">
                Reef Ecology
              </button>
            </h2>
            <div id="collapseEco" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <div class="mb-2">
                        <label class="form-label small text-muted">Reef Area (m²)</label>
                        <input class="form-control form-control-sm" name="reef_area" value="{{ form.reef_area }}" />
                    </div>
                    <div class="form-check form-switch mb-1">
                        <input class="form-check-input" type="checkbox" name="enable_recruitment" {{ 'checked' if form.enable_recruitment else '' }} />
                        <label class="form-check-label small">Recruitment</label>
                    </div>
                    <div class="form-check form-switch mb-1">
                        <input class="form-check-input" type="checkbox" name="enable_recruitment_noise" {{ 'checked' if form.enable_recruitment_noise else '' }} />
                        <label class="form-check-label small">Noise</label>
                    </div>
                </div>
            </div>
          </div>

          <!-- Initial State -->
          <div class="accordion-item card mb-2">
             <h2 class="accordion-header">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseInit">
                Initial State (%)
              </button>
            </h2>
            <div id="collapseInit" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <label class="form-label small fw-bold">Coral Cover</label>
                    <div class="input-group input-group-sm mb-1">
                        <span class="input-group-text">Br</span>
                        <input class="form-control" name="cover_branching" value="{{ form.cover_branching }}">
                    </div>
                    <div class="input-group input-group-sm mb-1">
                        <span class="input-group-text">Fol</span>
                        <input class="form-control" name="cover_foliose" value="{{ form.cover_foliose }}">
                    </div>
                     <div class="input-group input-group-sm mb-2">
                        <span class="input-group-text">Oth</span>
                        <input class="form-control" name="cover_other" value="{{ form.cover_other }}">
                    </div>
                    
                    <label class="form-label small fw-bold">Benthos</label>
                    <div class="input-group input-group-sm mb-1">
                        <span class="input-group-text">Alg</span>
                        <input class="form-control" name="macro_algae_cover" value="{{ form.macro_algae_cover }}">
                    </div>
                    <div class="input-group input-group-sm mb-1">
                        <span class="input-group-text">Rub</span>
                        <input class="form-control" name="rubble_cover" value="{{ form.rubble_cover }}">
                    </div>
                </div>
            </div>
          </div>
          
          <!-- Stressors -->
          <div class="accordion-item card mb-2">
             <h2 class="accordion-header">
              <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#collapseStress">
                Stressors Config
              </button>
            </h2>
            <div id="collapseStress" class="accordion-collapse collapse">
                <div class="accordion-body">
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="enable_bleaching" {{ 'checked' if form.enable_bleaching else '' }} />
                        <label class="form-check-label small">Bleaching (DHW)</label>
                    </div>
                    <textarea class="form-control mono mb-2" name="dhw_years" rows="3">{{ form.dhw_years }}</textarea>
                    
                    <div class="form-check form-switch mb-2">
                        <input class="form-check-input" type="checkbox" name="enable_cyclone" {{ 'checked' if form.enable_cyclone else '' }} />
                        <label class="form-check-label small">Cyclones</label>
                    </div>
                    <textarea class="form-control mono" name="cyclone_years" rows="3">{{ form.cyclone_years }}</textarea>
                </div>
            </div>
          </div>

        </div>
        
        <button class="btn btn-primary w-100 fw-bold shadow-sm">Run Simulation</button>
        {% if errors %}
        <div class="alert alert-danger mt-3 small">
            <ul class="mb-0 ps-3">
            {% for key, val in errors.items() %}
                <li>{{ val }}</li>
            {% endfor %}
            </ul>
        </div>
        {% endif %}
      </form>
    </div>

    <!-- Main Content -->
    <div class="col-lg-9">
      {% if model_ready %}
      
      <!-- Key Metrics Row -->
      <div class="row g-3 mb-4">
        <div class="col-md-3">
             <div class="card p-3 h-100 d-flex flex-column justify-content-center border-start border-4 border-primary">
                <h6 class="text-uppercase text-muted small mb-1">Final Coral Cover</h6>
                <div class="d-flex align-items-baseline">
                    <h2 class="mb-0 fw-bold">{{ "%.1f"|format(metrics.final_cover) }}%</h2>
                    {% if metrics.final_cover_std is defined %}
                    <small class="text-muted ms-2">±{{ "%.1f"|format(metrics.final_cover_std) }}</small>
                    {% endif %}
                </div>
                <small class="text-{{ 'success' if metrics.final_cover > 30 else 'warning' if metrics.final_cover > 10 else 'danger' }}">
                    {{ "Healthy" if metrics.final_cover > 30 else "Critical" if metrics.final_cover < 10 else "Degraded" }}
                </small>
             </div>
        </div>
        <div class="col-md-3">
             <div class="card p-3 h-100 d-flex flex-column justify-content-center border-start border-4 border-success">
                <h6 class="text-uppercase text-muted small mb-1">Final Rugosity</h6>
                <div class="d-flex align-items-baseline">
                    <h2 class="mb-0 fw-bold">{{ "%.2f"|format(metrics.final_rugosity) }}</h2>
                    {% if metrics.final_rugosity_std is defined %}
                    <small class="text-muted ms-2">±{{ "%.2f"|format(metrics.final_rugosity_std) }}</small>
                    {% endif %}
                </div>
                <small class="text-muted">Complexity Index</small>
             </div>
        </div>
        <div class="col-md-3">
             <div class="card p-3 h-100 d-flex flex-column justify-content-center border-start border-4 border-info">
                 <h6 class="text-uppercase text-muted small mb-1">Dominant Taxa</h6>
                 <h2 class="mb-0 fw-bold">{{ metrics.dominant_taxa }}</h2>
                 <small class="text-muted">By % Cover</small>
             </div>
        </div>
         <div class="col-md-3">
             <div class="card p-3 h-100 d-flex flex-column justify-content-center border-start border-4 border-warning">
                 <h6 class="text-uppercase text-muted small mb-1">Population Count</h6>
                 <div class="d-flex align-items-baseline">
                    <h2 class="mb-0 fw-bold">{{ metrics.total_pop }}</h2>
                    {% if metrics.total_pop_std is defined %}
                    <small class="text-muted ms-2">±{{ metrics.total_pop_std }}</small>
                    {% endif %}
                 </div>
                 <small class="text-muted">Colonies</small>
             </div>
        </div>
      </div>

      <!-- Main Visualizations Tabs -->
      <div class="card">
        <div class="card-header bg-white">
            <ul class="nav nav-tabs card-header-tabs" role="tablist">
                <li class="nav-item">
                    <a class="nav-link active" data-bs-toggle="tab" href="#tab-overview">Overview</a>
                </li>
                {% if form.mode == 'single' %}
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#tab-benthos">Benthos & Rugosity</a>
                </li>
                <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#tab-demographics">Demographics</a>
                </li>
                 <li class="nav-item">
                    <a class="nav-link" data-bs-toggle="tab" href="#tab-data">Raw Data</a>
                </li>
                {% endif %}
            </ul>
        </div>
        
        <div class="card-body">
            <div class="tab-content">
                <!-- Overview Tab -->
                <div class="tab-pane fade show active" id="tab-overview">
                    {% if form.mode == 'ensemble' %}
                        <div class="mb-4">
                            {{ figs.ensemble_cover | safe }}
                        </div>
                        <div class="mb-4">
                            {{ figs.ensemble_rugosity | safe }}
                        </div>
                        <div class="alert alert-info small">
                            Running ensemble analysis with {{ form.n_iterations }} iterations.
                            Shaded area represents standard deviation.
                        </div>
                    {% else %}
                        <div class="row">
                            <div class="col-lg-8">
                                {{ figs.cover | safe }}
                            </div>
                            <div class="col-lg-4">
                                {{ figs.final_pie | safe }}
                            </div>
                        </div>
                        <div class="row mt-3">
                             <div class="col-12">
                                {{ figs.composition | safe }}
                             </div>
                        </div>
                    {% endif %}
                </div>
                
                {% if form.mode == 'single' %}
                <!-- Benthos Tab -->
                <div class="tab-pane fade" id="tab-benthos">
                    <div class="row">
                        <div class="col-lg-6">
                            {{ figs.benthic | safe }}
                        </div>
                        <div class="col-lg-6">
                            {{ figs.rugosity | safe }}
                        </div>
                    </div>
                </div>
                
                <!-- Demographics Tab -->
                <div class="tab-pane fade" id="tab-demographics">
                    <div class="mb-4">
                        {{ figs.psd_comp | safe }}
                    </div>
                    <h5 class="mt-4 mb-3 border-bottom pb-2">Population Heatmaps</h5>
                    <div class="row g-3">
                        <div class="col-lg-4">
                           <div class="border rounded p-1">{{ figs.heat_branch | safe }}</div>
                        </div>
                        <div class="col-lg-4">
                           <div class="border rounded p-1">{{ figs.heat_foliose | safe }}</div>
                        </div>
                        <div class="col-lg-4">
                           <div class="border rounded p-1">{{ figs.heat_other | safe }}</div>
                        </div>
                    </div>
                </div>
                
                 <!-- Data Tab -->
                <div class="tab-pane fade" id="tab-data">
                    <div class="row">
                        <div class="col-md-6">{{ cover_table | safe }}</div>
                        <div class="col-md-6">{{ pop_table | safe }}</div>
                    </div>
                    <div class="mt-3">
                        <h6>Recent History</h6>
                        {{ tail_table | safe }}
                    </div>
                </div>
                {% endif %}
            </div>
        </div>
      </div>
      
      {% endif %}
    </div>
  </div>
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
    defaults = asdict(CoralParameters())
    form = {
        "mode": "single",
        "n_iterations": 20,
        "year_start": defaults["year_start"],
        "year_end": defaults["year_end"],
        "reef_area": defaults["reef_area"],
        "reef_shape": defaults["reef_shape"],
        "reef_exposure": defaults["reef_exposure"],
        "macro_algae_cover": defaults["macro_algae_cover"],
        "rubble_cover": defaults["rubble_cover"],
        "sediment_cover": defaults["sediment_cover"],
        "cover_branching": defaults["initial_coral_cover"]["Branching"],
        "cover_foliose": defaults["initial_coral_cover"]["Foliose"],
        "cover_other": defaults["initial_coral_cover"]["Other"],
        "brooder_cover": defaults["initial_brooder_cover"],
        "spawner_bf_cover": defaults["initial_spawner_cover"][0],
        "spawner_other_cover": defaults["initial_spawner_cover"][1],
        "enable_bleaching": defaults["enable_bleaching"],
        "enable_cyclone": defaults["enable_cyclone"],
        "enable_recruitment": defaults["enable_recruitment"],
        "enable_recruitment_noise": defaults["enable_recruitment_noise"],
        "dhw_years": json.dumps(defaults["dhw_years"], indent=2),
        "cyclone_years": json.dumps(defaults["cyclone_years"], indent=2),
        "space_limitation_exponent": defaults["space_limitation_exponent"],
    }

    errors = {}
    model_ready = False
    figs = {}
    metrics = {}
    cover_table = pop_table = tail_table = ""

    if request.method == "POST":
      form.update(request.form.to_dict())
      # Checkbox handling: if not in form, it's False
      for bool_field in ["enable_recruitment", "enable_recruitment_noise", "enable_bleaching", "enable_cyclone"]:
          form[bool_field] = request.form.get(bool_field)
      
      params, errors = build_params_from_request(form)
      
      if not errors and params:
        mode = form.get("mode", "single")
        
        if mode == "ensemble":
            n_iter = int(form.get("n_iterations", 20))
            ensemble_res = run_ensemble(n_iter, params)
            
            # Plot Cover Ensemble
            fig_ensemble_cov = CoralVisualizations.plot_ensemble(ensemble_res['cover'])
            figs["ensemble_cover"] = figure_to_div(fig_ensemble_cov)
            
            # Plot Rugosity Ensemble (reuse generic plotter with different title)
            fig_ensemble_rug = CoralVisualizations.plot_ensemble(ensemble_res['rugosity'])
            fig_ensemble_rug.update_layout(title='Ensemble Projection (Rugosity Index)', yaxis_title='Rugosity Index')
            figs["ensemble_rugosity"] = figure_to_div(fig_ensemble_rug)
            
            # Metrics from aggregated structure using std deviation
            m = ensemble_res['metrics']
            metrics = {
                "final_cover": m['cover_mean'],
                "final_cover_std": m['cover_std'],
                "final_rugosity": m['rugosity_mean'],
                "final_rugosity_std": m['rugosity_std'],
                "dominant_taxa": m['dominant_taxa'],
                "total_pop": int(m['pop_mean']),
                "total_pop_std": int(m['pop_std'])
            }
            model_ready = True
            
        else:
            # Single Mode
            model = CoralModel(params=params)
            model.run()
            model_ready = True
            
            cover_table, pop_table, tail_table = build_summary_tables(model)
            figs = build_figures(model)
            
            # KPI Metrics
            df = model.get_results_df()
            final = df.iloc[-1]
            taxa = ["Branching", "Foliose", "Other"]
            dom = max(taxa, key=lambda t: final[t])
            
            metrics = {
                "final_cover": final["total_cover"],
                "final_rugosity": model.rugosity,
                "dominant_taxa": dom,
                "total_pop": int(model.population.sum())
            }

    return render_template_string(
        TEMPLATE,
        form=form,
        errors=errors,
        model_ready=model_ready,
        figs=figs,
        metrics=metrics,
        cover_table=cover_table,
        pop_table=pop_table,
        tail_table=tail_table,
    )


@app.route("/docs")
def serve_docs():
    return send_from_directory("docs", "model_documentation.html")


if __name__ == "__main__":
    app.run(debug=True, port=8050)
