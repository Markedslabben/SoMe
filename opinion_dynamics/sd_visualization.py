"""
System Dynamics Visualization Module

Creates visualizations for the Opinion Dynamics SD model:
- Stock behavior over time
- Causal loop diagrams
- Phase portraits
- Sensitivity analysis charts
"""

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict, Optional
import os

from sd_model import OpinionDynamicsSD, SDState
from sd_parameters import SDParameters


def create_stock_trajectories(model: OpinionDynamicsSD) -> go.Figure:
    """
    Create line chart showing all stocks over time.

    Shows:
    - Neutral population (decreasing)
    - Contrarian converts (increasing)
    - Consensus converts (minimal)
    - Arousal (rising to threshold)
    - Frame adoption (increasing)
    """
    if not model.state_history:
        raise RuntimeError("Run simulation first")

    times = [s.time for s in model.state_history]
    neutrals = [s.neutrals for s in model.state_history]
    contrarian = [s.contrarian_converts for s in model.state_history]
    consensus = [s.consensus_converts for s in model.state_history]
    arousal = [s.arousal for s in model.state_history]
    frame = [s.frame_adoption for s in model.state_history]

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Population Stocks',
            'Arousal Dynamics',
            'Frame Adoption',
            'Conversion Rates'
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )

    # Population stocks
    fig.add_trace(go.Scatter(
        x=times, y=neutrals,
        name='Neutrals (N)',
        line=dict(color='#95a5a6', width=2),
        hovertemplate='t=%{x:.1f}<br>N=%{y:.1f}<extra></extra>'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=times, y=contrarian,
        name='Contrarian Converts (C)',
        line=dict(color='#e74c3c', width=2),
        hovertemplate='t=%{x:.1f}<br>C=%{y:.1f}<extra></extra>'
    ), row=1, col=1)

    fig.add_trace(go.Scatter(
        x=times, y=consensus,
        name='Consensus Converts (S)',
        line=dict(color='#3498db', width=2),
        hovertemplate='t=%{x:.1f}<br>S=%{y:.2f}<extra></extra>'
    ), row=1, col=1)

    # Arousal dynamics
    fig.add_trace(go.Scatter(
        x=times, y=arousal,
        name='Arousal (A)',
        line=dict(color='#e67e22', width=2),
        fill='tozeroy',
        fillcolor='rgba(230, 126, 34, 0.2)',
        hovertemplate='t=%{x:.1f}<br>A=%{y:.3f}<extra></extra>'
    ), row=1, col=2)

    # Threshold line
    threshold_time = model.find_threshold_crossing()
    fig.add_hline(
        y=model.params.threshold_arousal,
        line_dash="dot",
        line_color="red",
        annotation_text=f"Threshold ({model.params.threshold_arousal})",
        row=1, col=2
    )

    if threshold_time:
        fig.add_vline(
            x=threshold_time,
            line_dash="dash",
            line_color="purple",
            annotation_text=f"t={threshold_time:.1f}",
            row=1, col=2
        )

    # Frame adoption
    fig.add_trace(go.Scatter(
        x=times, y=frame,
        name='Frame Adoption (F)',
        line=dict(color='#9b59b6', width=2),
        fill='tozeroy',
        fillcolor='rgba(155, 89, 182, 0.2)',
        hovertemplate='t=%{x:.1f}<br>F=%{y:.3f}<extra></extra>'
    ), row=2, col=1)

    # Conversion rates
    conv_c = [s.conversion_rate_c for s in model.state_history]
    conv_s = [s.conversion_rate_s for s in model.state_history]

    fig.add_trace(go.Scatter(
        x=times, y=conv_c,
        name='Conversion rate to C',
        line=dict(color='#e74c3c', width=1.5, dash='dot'),
        hovertemplate='t=%{x:.1f}<br>rate=%{y:.4f}<extra></extra>'
    ), row=2, col=2)

    fig.add_trace(go.Scatter(
        x=times, y=conv_s,
        name='Conversion rate to S',
        line=dict(color='#3498db', width=1.5, dash='dot'),
        hovertemplate='t=%{x:.1f}<br>rate=%{y:.4f}<extra></extra>'
    ), row=2, col=2)

    fig.update_layout(
        title='System Dynamics: Opinion Formation Under Algorithmic Amplification',
        height=700,
        template='plotly_white',
        showlegend=True,
        legend=dict(x=1.02, y=1, xanchor='left')
    )

    fig.update_xaxes(title_text='Time (rounds)', row=2, col=1)
    fig.update_xaxes(title_text='Time (rounds)', row=2, col=2)
    fig.update_yaxes(title_text='Population', row=1, col=1)
    fig.update_yaxes(title_text='Arousal (0-1)', row=1, col=2)
    fig.update_yaxes(title_text='Fraction (0-1)', row=2, col=1)
    fig.update_yaxes(title_text='Rate (agents/t)', row=2, col=2)

    return fig


def create_phase_portrait(model: OpinionDynamicsSD) -> go.Figure:
    """
    Create phase portrait showing arousal vs contrarian converts.

    This reveals the feedback loop dynamics and threshold behavior.
    """
    if not model.state_history:
        raise RuntimeError("Run simulation first")

    arousal = [s.arousal for s in model.state_history]
    contrarian = [s.contrarian_converts for s in model.state_history]
    times = [s.time for s in model.state_history]

    fig = go.Figure()

    # Main trajectory with color gradient for time
    fig.add_trace(go.Scatter(
        x=arousal,
        y=contrarian,
        mode='lines+markers',
        marker=dict(
            size=4,
            color=times,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='Time')
        ),
        line=dict(color='rgba(100, 100, 100, 0.3)', width=1),
        hovertemplate='Arousal=%{x:.3f}<br>Converts=%{y:.1f}<br>t=%{marker.color:.1f}<extra></extra>'
    ))

    # Mark start and end points
    fig.add_trace(go.Scatter(
        x=[arousal[0]], y=[contrarian[0]],
        mode='markers',
        marker=dict(size=15, color='green', symbol='circle'),
        name='Start',
        hovertemplate='START<br>A=%{x:.3f}<br>C=%{y:.1f}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=[arousal[-1]], y=[contrarian[-1]],
        mode='markers',
        marker=dict(size=15, color='red', symbol='star'),
        name='End',
        hovertemplate='END<br>A=%{x:.3f}<br>C=%{y:.1f}<extra></extra>'
    ))

    # Threshold line
    fig.add_vline(
        x=model.params.threshold_arousal,
        line_dash="dash",
        line_color="orange",
        annotation_text="Threshold"
    )

    fig.update_layout(
        title='Phase Portrait: Arousal vs Contrarian Conversions',
        xaxis_title='Aggregate Arousal (A)',
        yaxis_title='Contrarian Converts (C)',
        template='plotly_white',
        height=500,
        showlegend=True
    )

    return fig


def create_feedback_loop_strengths(model: OpinionDynamicsSD) -> go.Figure:
    """
    Visualize the relative strength of feedback loops over time.

    Shows how R1 (visibility-arousal), R2 (framing), and R3 (population shift)
    contribute to system dynamics.
    """
    if not model.state_history:
        raise RuntimeError("Run simulation first")

    times = [s.time for s in model.state_history]

    # Approximate loop strengths
    # R1: Exposure → Arousal → Susceptibility
    r1_strength = [s.exposure_c * s.susceptibility for s in model.state_history]

    # R2: Frame adoption cascade
    r2_strength = [s.frame_adoption * s.exposure_c for s in model.state_history]

    # R3: Population shift
    r3_strength = [s.contrarian_converts / max(0.1, s.neutrals + s.contrarian_converts)
                   for s in model.state_history]

    # Normalize for comparison
    max_r1 = max(r1_strength) or 1
    max_r2 = max(r2_strength) or 1
    max_r3 = max(r3_strength) or 1

    r1_norm = [x / max_r1 for x in r1_strength]
    r2_norm = [x / max_r2 for x in r2_strength]
    r3_norm = [x / max_r3 for x in r3_strength]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=times, y=r1_norm,
        name='R1: Visibility-Arousal-Susceptibility',
        line=dict(color='#e74c3c', width=2),
        fill='tozeroy',
        fillcolor='rgba(231, 76, 60, 0.2)'
    ))

    fig.add_trace(go.Scatter(
        x=times, y=r2_norm,
        name='R2: Framing Cascade',
        line=dict(color='#9b59b6', width=2),
        fill='tozeroy',
        fillcolor='rgba(155, 89, 182, 0.2)'
    ))

    fig.add_trace(go.Scatter(
        x=times, y=r3_norm,
        name='R3: Population Shift',
        line=dict(color='#f39c12', width=2),
        fill='tozeroy',
        fillcolor='rgba(243, 156, 18, 0.2)'
    ))

    # Mark threshold crossing
    threshold_time = model.find_threshold_crossing()
    if threshold_time:
        fig.add_vline(
            x=threshold_time,
            line_dash="dash",
            line_color="red",
            annotation_text="Threshold"
        )

    fig.update_layout(
        title='Feedback Loop Strengths Over Time (Normalized)',
        xaxis_title='Time (rounds)',
        yaxis_title='Relative Strength (0-1)',
        template='plotly_white',
        height=400,
        legend=dict(x=0.02, y=0.98)
    )

    return fig


def create_causal_loop_diagram() -> go.Figure:
    """
    Create a visual representation of the causal loop diagram.

    Note: This is a stylized visualization, not a formal CLD tool output.
    """
    fig = go.Figure()

    # Node positions (circular layout)
    nodes = {
        'Provocative\nContent': (0.5, 0.95),
        'Visibility': (0.85, 0.75),
        'Exposure': (0.95, 0.45),
        'Arousal': (0.75, 0.15),
        'Susceptibility': (0.35, 0.15),
        'Conversions': (0.05, 0.45),
        'Frame\nAdoption': (0.25, 0.75),
    }

    # Draw nodes
    for name, (x, y) in nodes.items():
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=40, color='lightblue', line=dict(width=2, color='navy')),
            text=[name],
            textposition='middle center',
            textfont=dict(size=10),
            hoverinfo='text',
            hovertext=name,
            showlegend=False
        ))

    # Draw edges (simplified - showing main R1 loop)
    edges = [
        ('Provocative\nContent', 'Visibility', '+'),
        ('Visibility', 'Exposure', '+'),
        ('Exposure', 'Arousal', '+'),
        ('Arousal', 'Susceptibility', '+'),
        ('Susceptibility', 'Conversions', '+'),
        ('Conversions', 'Provocative\nContent', '+'),
        ('Exposure', 'Frame\nAdoption', '+'),
        ('Frame\nAdoption', 'Provocative\nContent', '+'),
    ]

    for start, end, polarity in edges:
        x0, y0 = nodes[start]
        x1, y1 = nodes[end]

        # Draw arrow
        fig.add_annotation(
            x=x1, y=y1,
            ax=x0, ay=y0,
            xref='x', yref='y',
            axref='x', ayref='y',
            showarrow=True,
            arrowhead=2,
            arrowsize=1.5,
            arrowwidth=2,
            arrowcolor='gray'
        )

        # Add polarity label
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        fig.add_annotation(
            x=mx, y=my,
            text=polarity,
            showarrow=False,
            font=dict(size=14, color='red' if polarity == '+' else 'blue')
        )

    # Add loop label
    fig.add_annotation(
        x=0.5, y=0.5,
        text='R1\n(Reinforcing)',
        showarrow=False,
        font=dict(size=16, color='red'),
        bgcolor='rgba(255,255,255,0.8)'
    )

    fig.update_layout(
        title='Causal Loop Diagram: Algorithmic Amplification Feedback',
        xaxis=dict(visible=False, range=[-0.1, 1.1]),
        yaxis=dict(visible=False, range=[-0.1, 1.1]),
        template='plotly_white',
        height=500,
        width=600
    )

    return fig


def create_comparison_chart(
    baseline_model: OpinionDynamicsSD,
    policy_models: Dict[str, OpinionDynamicsSD]
) -> go.Figure:
    """
    Create comparison chart between baseline and policy scenarios.

    Args:
        baseline_model: Model run with default parameters
        policy_models: Dict of {name: model} for policy scenarios
    """
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Contrarian Conversions', 'Peak Arousal')
    )

    # Extract data
    scenarios = ['Baseline'] + list(policy_models.keys())
    converts = [baseline_model.get_final_state().contrarian_converts]
    arousal_peaks = [max(s.arousal for s in baseline_model.state_history)]

    for name, model in policy_models.items():
        converts.append(model.get_final_state().contrarian_converts)
        arousal_peaks.append(max(s.arousal for s in model.state_history))

    colors = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12']

    # Conversions bar chart
    fig.add_trace(go.Bar(
        x=scenarios,
        y=converts,
        marker_color=colors[:len(scenarios)],
        text=[f'{c:.1f}' for c in converts],
        textposition='outside',
        name='Conversions'
    ), row=1, col=1)

    # Arousal bar chart
    fig.add_trace(go.Bar(
        x=scenarios,
        y=arousal_peaks,
        marker_color=colors[:len(scenarios)],
        text=[f'{a:.3f}' for a in arousal_peaks],
        textposition='outside',
        name='Peak Arousal'
    ), row=1, col=2)

    fig.update_layout(
        title='Policy Scenario Comparison',
        template='plotly_white',
        height=400,
        showlegend=False
    )

    fig.update_yaxes(title_text='Conversions', row=1, col=1)
    fig.update_yaxes(title_text='Arousal', row=1, col=2)

    return fig


def create_dashboard(model: OpinionDynamicsSD) -> go.Figure:
    """
    Create comprehensive dashboard with all key visualizations.
    """
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=(
            'Population Dynamics',
            'Arousal & Threshold',
            'Phase Portrait',
            'Frame Adoption',
            'Feedback Loop Strengths',
            'Summary Statistics'
        ),
        specs=[
            [{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}],
            [{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'table'}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )

    times = [s.time for s in model.state_history]

    # 1. Population dynamics
    fig.add_trace(go.Scatter(
        x=times, y=[s.neutrals for s in model.state_history],
        name='Neutrals', line=dict(color='#95a5a6')
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=times, y=[s.contrarian_converts for s in model.state_history],
        name='C-Converts', line=dict(color='#e74c3c')
    ), row=1, col=1)

    # 2. Arousal
    fig.add_trace(go.Scatter(
        x=times, y=[s.arousal for s in model.state_history],
        name='Arousal', line=dict(color='#e67e22'),
        fill='tozeroy', fillcolor='rgba(230, 126, 34, 0.2)'
    ), row=1, col=2)
    fig.add_hline(y=model.params.threshold_arousal, line_dash="dot",
                  line_color="red", row=1, col=2)

    # 3. Phase portrait
    fig.add_trace(go.Scatter(
        x=[s.arousal for s in model.state_history],
        y=[s.contrarian_converts for s in model.state_history],
        mode='lines', name='Trajectory', line=dict(color='purple')
    ), row=1, col=3)

    # 4. Frame adoption
    fig.add_trace(go.Scatter(
        x=times, y=[s.frame_adoption for s in model.state_history],
        name='Frame Adoption', line=dict(color='#9b59b6'),
        fill='tozeroy', fillcolor='rgba(155, 89, 182, 0.2)'
    ), row=2, col=1)

    # 5. Loop strengths
    r1 = [s.exposure_c * s.susceptibility for s in model.state_history]
    max_r1 = max(r1) or 1
    fig.add_trace(go.Scatter(
        x=times, y=[x/max_r1 for x in r1],
        name='R1 Strength', line=dict(color='#e74c3c')
    ), row=2, col=2)

    # 6. Summary table
    summary = model.get_summary()
    fig.add_trace(go.Table(
        header=dict(
            values=['Metric', 'Value'],
            fill_color='#34495e',
            font_color='white',
            align='left'
        ),
        cells=dict(
            values=[
                ['Final Neutrals', 'C-Converts', 'S-Converts',
                 'Peak Arousal', 'Threshold Time', 'Frame Adoption'],
                [f"{summary['final']['neutrals']:.1f}",
                 f"{summary['final']['contrarian_converts']:.1f}",
                 f"{summary['final']['consensus_converts']:.2f}",
                 f"{summary['dynamics']['peak_arousal']:.3f}",
                 f"{summary['dynamics']['threshold_crossing_time']}" if summary['dynamics']['threshold_crossing_time'] else 'Never',
                 f"{summary['final']['frame_adoption']:.3f}"]
            ],
            align='left'
        )
    ), row=2, col=3)

    fig.update_layout(
        title='Opinion Dynamics System Dynamics Dashboard',
        height=800,
        template='plotly_white',
        showlegend=False
    )

    return fig


def save_all_visualizations(
    model: OpinionDynamicsSD,
    output_dir: str,
    timestamp: str
) -> List[str]:
    """
    Generate and save all visualizations.

    Returns:
        List of saved file paths
    """
    os.makedirs(output_dir, exist_ok=True)
    saved = []

    # Stock trajectories
    fig = create_stock_trajectories(model)
    path = f"{output_dir}/sd_stock_trajectories_{timestamp}.html"
    fig.write_html(path)
    saved.append(path)

    # Phase portrait
    fig = create_phase_portrait(model)
    path = f"{output_dir}/sd_phase_portrait_{timestamp}.html"
    fig.write_html(path)
    saved.append(path)

    # Feedback loops
    fig = create_feedback_loop_strengths(model)
    path = f"{output_dir}/sd_feedback_loops_{timestamp}.html"
    fig.write_html(path)
    saved.append(path)

    # CLD
    fig = create_causal_loop_diagram()
    path = f"{output_dir}/sd_causal_loop_diagram_{timestamp}.html"
    fig.write_html(path)
    saved.append(path)

    # Dashboard
    fig = create_dashboard(model)
    path = f"{output_dir}/sd_dashboard_{timestamp}.html"
    fig.write_html(path)
    saved.append(path)

    return saved


if __name__ == "__main__":
    # Test visualizations
    from sd_model import OpinionDynamicsSD

    print("Generating visualizations...")
    model = OpinionDynamicsSD()
    model.run()

    fig = create_stock_trajectories(model)
    fig.show()
