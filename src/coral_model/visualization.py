import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from .core import CoralModel

class CoralVisualizations:
    """Helper class for generating interactive plots."""
    
    @staticmethod
    def plot_cover_history(model: CoralModel) -> go.Figure:
        """Plot total coral cover over time."""
        df = model.get_results_df()
        
        fig = go.Figure()
        
        # Total Cover
        fig.add_trace(go.Scatter(
            x=df['year'], y=df['total_cover'],
            mode='lines+markers',
            name='Total Cover',
            line=dict(width=3, color='black')
        ))
        
        # Breakdown
        colors = {'Branching': 'blue', 'Foliose': 'green', 'Other': 'orange'}
        for coral_type, color in colors.items():
            if coral_type in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['year'], y=df[coral_type],
                    mode='lines',
                    name=coral_type,
                    stackgroup='one', # Stacked area
                    line=dict(width=0.5, color=color),
                    fillcolor=color
                ))
                
        fig.update_layout(
            title='Coral Cover Dynamics',
            xaxis_title='Year',
            yaxis_title='Cover (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        return fig

    @staticmethod
    def plot_demographic_heatmap(model: CoralModel, coral_type: str = 'Branching') -> go.Figure:
        """
        Create a heatmap of population distribution over time for a specific coral type.
        X-axis: Year, Y-axis: Size Class (Bin), Color: Count.
        """
        # History population is List[np.ndarray(3, Bins)]
        history = model.history_population
        years = len(history)
        bins = history[0].shape[1]
        
        type_idx = {'Branching': 0, 'Foliose': 1, 'Other': 2}.get(coral_type, 0)
        
        # Prepare data matrix (Bins x Years)
        data = np.zeros((bins, years))
        
        for y, pop in enumerate(history):
            data[:, y] = pop[type_idx, :]
            
        # Bin labels (approx diameter)
        bin_labels = [f"{i*5}-{(i+1)*5}cm" for i in range(bins)]
        
        fig = go.Figure(data=go.Heatmap(
            z=data,
            x=list(range(years)),
            y=bin_labels,
            colorscale='Viridis',
            colorbar=dict(title='Count')
        ))
        
        fig.update_layout(
            title=f'{coral_type} Population Structure Evolution',
            xaxis_title='Year',
            yaxis_title='Size Class',
            template='plotly_white'
        )
        return fig

    @staticmethod
    def compare_scenarios(models: Dict[str, CoralModel]) -> go.Figure:
        """Compare total cover across multiple model runs."""
        fig = go.Figure()
        
        for name, model in models.items():
            df = model.get_results_df()
            fig.add_trace(go.Scatter(
                x=df['year'], y=df['total_cover'],
                mode='lines',
                name=name
            ))
            
        fig.update_layout(
            title='Scenario Comparison',
            xaxis_title='Year',
            yaxis_title='Total Coral Cover (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        return fig

    @staticmethod
    def plot_benthic_stack(model: CoralModel) -> go.Figure:
        """Plot stacked area chart of benthic cover components."""
        df = model.get_benthic_df()
        df['year'] = range(len(df))
        
        fig = go.Figure()
        
        # Add Live Coral Trace
        res_df = model.get_results_df()
        fig.add_trace(go.Scatter(
            x=res_df['year'], y=res_df['total_cover'],
            mode='lines',
            name='Live Coral',
            stackgroup='one',
            line=dict(width=0, color='#FF6B6B'), # Coral Color
            fillcolor='#FF6B6B'
        ))
        
        # Map params keys to colors
        color_map = {
            'CCA': '#E06666',          # Crustose Coralline Algae (Pinkish Red)
            'turfing_algae': '#93C47D', # Green
            'macro_algae': '#38761D',   # Dark Green
            'dead_coral': '#D9D9D9',    # Grey
            'rubble': '#999999',        # Darker Grey
            'hard_substrate': '#CCCCCC',# Light Grey
            'sediment': '#E69138'       # Sandy Orange
        }
        
        # Add others
        for key, color in color_map.items():
            if key in df.columns:
                fig.add_trace(go.Scatter(
                    x=df['year'], y=df[key],
                    mode='lines',
                    name=key.replace('_', ' ').title(),
                    stackgroup='one',
                    line=dict(width=0, color=color),
                    fillcolor=color
                ))
                
        fig.update_layout(
            title='Benthic Community Composition',
            xaxis_title='Year',
            yaxis_title='Cover (%)',
            hovermode='x unified',
            template='plotly_white',
            yaxis=dict(range=[0, 100])
        )
        return fig

    @staticmethod
    def plot_rugosity(model: CoralModel) -> go.Figure:
        """Plot Rugosity Index over time."""
        df = model.get_rugosity_df()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df['year'], y=df['rugosity'],
            mode='lines+markers',
            name='Rugosity',
            line=dict(color='#674EA7', width=3)
        ))
        
        fig.update_layout(
            title='Structural Complexity (Rugosity)',
            xaxis_title='Year',
            yaxis_title='Rugosity Index (RI)',
            template='plotly_white'
        )
        return fig

    @staticmethod
    def plot_ensemble(ensemble_df: pd.DataFrame) -> go.Figure:
        """Plot Mean Total Cover with SD Envelope."""
        fig = go.Figure()
        
        x = ensemble_df['year']
        y_mean = ensemble_df['mean']
        y_std = ensemble_df['std']
        
        y_upper = y_mean + y_std
        y_lower = y_mean - y_std
        # Clip lower at 0
        y_lower = y_lower.clip(0)
        
        # Std Dev Area
        fig.add_trace(go.Scatter(
            x=list(x) + list(x)[::-1],
            y=list(y_upper) + list(y_lower)[::-1],
            fill='toself',
            fillcolor='rgba(0,100,80,0.2)',
            line=dict(color='rgba(255,255,255,0)'),
            hoverinfo="skip",
            showlegend=True,
            name='Standard Deviation'
        ))
        
        # Mean Line
        fig.add_trace(go.Scatter(
            x=x, y=y_mean,
            line=dict(color='rgb(0,100,80)', width=4),
            mode='lines',
            name='Mean Total Cover'
        ))
        
        fig.update_layout(
            title='Ensemble Projection (Total Coral Cover)',
            xaxis_title='Year',
            yaxis_title='Cover (%)',
            hovermode='x unified',
            template='plotly_white'
        )
        return fig

    @staticmethod
    def plot_psd_comparison(model: CoralModel) -> go.Figure:
        """Compare Initial vs Final Population Size Structure."""
        pop_hist = model.history_population
        
        initial = pop_hist[0].sum(axis=0) # Sum across types, shape (20,)
        final = pop_hist[-1].sum(axis=0)
        
        bins = [f"{i*5}-{(i+1)*5}" for i in range(len(initial))]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=bins, y=initial,
            name='Initial (Year 0)',
            marker_color='lightgrey',
            opacity=0.8
        ))
        fig.add_trace(go.Bar(
            x=bins, y=final,
            name=f'Final (Year {model.year})',
            marker_color='teal',
            opacity=0.8
        ))
        
        fig.update_layout(
            title='Population Size Structure Change',
            xaxis_title='Size Class (cm)',
            yaxis_title='Total Colony Count',
            barmode='group',
            template='plotly_white'
        )
        return fig
