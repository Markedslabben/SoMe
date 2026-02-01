"""
Visualization module for the Opinion Dynamics Simulation.

Creates interactive Plotly charts showing:
- Individual agent opinion trajectories
- Behavioral heatmaps (confrontation over time)
- Population emotional climate
- Amplification bias analysis
- Combined dashboard
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import List, Dict
from tracking import SimulationTracker, RoundSummary
from models import OpinionType


def create_opinion_trajectories(tracker: SimulationTracker) -> go.Figure:
    """
    Create line chart showing each agent's opinion position over time.

    - X-axis: Round (0-50)
    - Y-axis: Opinion position (-1 to +1)
    - Lines colored by initial agent type
    - Conversion points highlighted
    """
    fig = go.Figure()

    trajectories = tracker.get_opinion_trajectories()

    # Color scheme by agent type
    colors = {
        'C': '#e74c3c',   # Contrarian - red
        'S': '#3498db',   # Consensus - blue
        'N': '#95a5a6'    # Neutral - gray
    }

    for agent_id, positions in trajectories.items():
        agent_type = agent_id[0]  # C, S, or N
        color = colors.get(agent_type, '#95a5a6')

        # Determine line style
        if agent_type == 'C':
            width = 3
            dash = None
            name = f"Contrarian ({agent_id})"
        elif agent_type == 'S':
            width = 2
            dash = None
            name = f"Consensus ({agent_id})"
        else:
            width = 1
            dash = None
            name = f"Neutral ({agent_id})"

        rounds = list(range(len(positions)))

        fig.add_trace(go.Scatter(
            x=rounds,
            y=positions,
            mode='lines',
            name=name,
            line=dict(color=color, width=width, dash=dash),
            hovertemplate=f"{name}<br>Round: %{{x}}<br>Position: %{{y:.3f}}<extra></extra>"
        ))

    # Add threshold lines
    fig.add_hline(y=0.3, line_dash="dot", line_color="blue",
                  annotation_text="Consensus threshold", annotation_position="right")
    fig.add_hline(y=-0.3, line_dash="dot", line_color="red",
                  annotation_text="Contrarian threshold", annotation_position="right")
    fig.add_hline(y=0, line_dash="dash", line_color="gray")

    # Mark conversion events
    for event in tracker.conversion_events:
        color = '#e74c3c' if event.direction == "to_contrarian" else '#3498db'
        fig.add_trace(go.Scatter(
            x=[event.round_num],
            y=[event.new_position],
            mode='markers',
            marker=dict(size=12, color=color, symbol='star'),
            name=f"Conversion: {event.agent_name}",
            hovertemplate=(
                f"CONVERSION<br>"
                f"Agent: {event.agent_name}<br>"
                f"Round: {event.round_num}<br>"
                f"Direction: {event.direction}<br>"
                f"New position: {event.new_position:.3f}<extra></extra>"
            ),
            showlegend=False
        ))

    fig.update_layout(
        title='Opinion Trajectories Over 50 Rounds',
        xaxis_title='Round',
        yaxis_title='Opinion Position (-1 Contrarian, +1 Consensus)',
        yaxis=dict(range=[-1.1, 1.1]),
        hovermode='closest',
        template='plotly_white',
        height=600
    )

    return fig


def create_behavioral_heatmap(tracker: SimulationTracker) -> go.Figure:
    """
    Create heatmap showing confrontation level per agent over time.

    - Rows: Agents (sorted by final opinion)
    - Columns: Rounds
    - Color: Confrontation index (red=high, blue=low)
    """
    trajectories = tracker.get_confrontation_trajectories()

    if not trajectories:
        fig = go.Figure()
        fig.add_annotation(text="No data available", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    # Sort agents by final opinion position
    final_opinions = {}
    for agent_id, snapshots in tracker.agent_histories.items():
        if snapshots:
            final_opinions[agent_id] = snapshots[-1].opinion_position

    sorted_agents = sorted(final_opinions.keys(), key=lambda x: final_opinions[x])

    # Build heatmap data
    z_data = []
    agent_labels = []

    for agent_id in sorted_agents:
        if agent_id in trajectories:
            z_data.append(trajectories[agent_id])
            final_pos = final_opinions[agent_id]
            agent_labels.append(f"{agent_id} ({final_pos:+.2f})")

    if not z_data:
        fig = go.Figure()
        fig.add_annotation(text="No confrontation data", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    rounds = list(range(len(z_data[0]))) if z_data else []

    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=rounds,
        y=agent_labels,
        colorscale='RdBu_r',  # Red = high confrontation, Blue = low
        colorbar=dict(title='Confrontation<br>Index'),
        hovertemplate='Agent: %{y}<br>Round: %{x}<br>Confrontation: %{z:.3f}<extra></extra>'
    ))

    fig.update_layout(
        title='Behavioral Heatmap: Confrontation Level Over Time',
        xaxis_title='Round',
        yaxis_title='Agent (sorted by final opinion)',
        template='plotly_white',
        height=600
    )

    return fig


def create_emotional_climate_chart(tracker: SimulationTracker) -> go.Figure:
    """
    Create chart showing population emotional state over time.

    Shows average arousal and anger across all agents.
    """
    if not tracker.round_summaries:
        fig = go.Figure()
        fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    rounds = [s.round_num for s in tracker.round_summaries]
    arousal = [s.average_arousal for s in tracker.round_summaries]
    anger = [s.average_anger for s in tracker.round_summaries]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rounds, y=arousal,
        mode='lines',
        name='Average Arousal',
        line=dict(color='#e67e22', width=2),
        fill='tozeroy',
        fillcolor='rgba(230, 126, 34, 0.2)'
    ))

    fig.add_trace(go.Scatter(
        x=rounds, y=anger,
        mode='lines',
        name='Average Anger',
        line=dict(color='#c0392b', width=2),
        fill='tozeroy',
        fillcolor='rgba(192, 57, 43, 0.2)'
    ))

    # Mark conversion events
    for event in tracker.conversion_events:
        fig.add_vline(
            x=event.round_num,
            line_dash="dot",
            line_color="purple",
            opacity=0.5
        )

    fig.update_layout(
        title='Emotional Climate Over Time (with Conversion Events)',
        xaxis_title='Round',
        yaxis_title='Average Emotional Intensity',
        yaxis=dict(range=[0, 1]),
        template='plotly_white',
        height=400
    )

    return fig


def create_opinion_distribution_chart(tracker: SimulationTracker) -> go.Figure:
    """
    Create stacked area chart showing opinion distribution over time.
    """
    if not tracker.round_summaries:
        fig = go.Figure()
        fig.add_annotation(text="No data", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    rounds = [s.round_num for s in tracker.round_summaries]
    contrarian = [s.opinion_distribution['contrarian'] for s in tracker.round_summaries]
    neutral = [s.opinion_distribution['neutral'] for s in tracker.round_summaries]
    consensus = [s.opinion_distribution['consensus'] for s in tracker.round_summaries]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=rounds, y=contrarian,
        fill='tozeroy',
        name='Contrarian',
        line=dict(color='#e74c3c'),
        fillcolor='rgba(231, 76, 60, 0.6)',
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=rounds, y=neutral,
        fill='tonexty',
        name='Neutral',
        line=dict(color='#95a5a6'),
        fillcolor='rgba(149, 165, 166, 0.6)',
        stackgroup='one'
    ))

    fig.add_trace(go.Scatter(
        x=rounds, y=consensus,
        fill='tonexty',
        name='Consensus',
        line=dict(color='#3498db'),
        fillcolor='rgba(52, 152, 219, 0.6)',
        stackgroup='one'
    ))

    fig.update_layout(
        title='Opinion Distribution Evolution',
        xaxis_title='Round',
        yaxis_title='Number of Agents',
        hovermode='x unified',
        template='plotly_white',
        height=400
    )

    return fig


def create_dashboard(tracker: SimulationTracker) -> go.Figure:
    """
    Create combined dashboard with key metrics.

    4-panel layout:
    - Opinion distribution over time
    - Average opinion position
    - Emotional climate
    - Summary statistics table
    """
    if not tracker.round_summaries:
        fig = go.Figure()
        fig.add_annotation(text="No simulation data", xref="paper", yref="paper", x=0.5, y=0.5)
        return fig

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            'Opinion Distribution',
            'Average Opinion Position',
            'Emotional Climate',
            'Summary Statistics'
        ),
        specs=[
            [{"type": "scatter"}, {"type": "scatter"}],
            [{"type": "scatter"}, {"type": "table"}]
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.08
    )

    rounds = [s.round_num for s in tracker.round_summaries]

    # 1. Opinion distribution
    contrarian = [s.opinion_distribution['contrarian'] for s in tracker.round_summaries]
    neutral = [s.opinion_distribution['neutral'] for s in tracker.round_summaries]
    consensus = [s.opinion_distribution['consensus'] for s in tracker.round_summaries]

    fig.add_trace(go.Scatter(x=rounds, y=contrarian, name='Contrarian',
                             line=dict(color='#e74c3c')), row=1, col=1)
    fig.add_trace(go.Scatter(x=rounds, y=neutral, name='Neutral',
                             line=dict(color='#95a5a6')), row=1, col=1)
    fig.add_trace(go.Scatter(x=rounds, y=consensus, name='Consensus',
                             line=dict(color='#3498db')), row=1, col=1)

    # 2. Average opinion
    avg_opinions = [s.average_opinion for s in tracker.round_summaries]
    fig.add_trace(go.Scatter(x=rounds, y=avg_opinions, name='Avg Opinion',
                             line=dict(color='#9b59b6', width=2)), row=1, col=2)
    # Reference lines
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)

    # 3. Emotional climate
    arousal = [s.average_arousal for s in tracker.round_summaries]
    anger = [s.average_anger for s in tracker.round_summaries]
    fig.add_trace(go.Scatter(x=rounds, y=arousal, name='Arousal',
                             line=dict(color='#e67e22')), row=2, col=1)
    fig.add_trace(go.Scatter(x=rounds, y=anger, name='Anger',
                             line=dict(color='#c0392b')), row=2, col=1)

    # 4. Statistics table
    initial = tracker.round_summaries[0].opinion_distribution
    final = tracker.round_summaries[-1].opinion_distribution

    to_contrarian = sum(1 for e in tracker.conversion_events if e.direction == "to_contrarian")
    to_consensus = sum(1 for e in tracker.conversion_events if e.direction == "to_consensus")

    fig.add_trace(go.Table(
        header=dict(
            values=['Metric', 'Initial', 'Final', 'Change'],
            fill_color='#34495e',
            font_color='white',
            align='left'
        ),
        cells=dict(
            values=[
                ['Contrarian', 'Neutral', 'Consensus', 'Avg Opinion', 'To Contrarian', 'To Consensus'],
                [initial['contrarian'], initial['neutral'], initial['consensus'],
                 f"{tracker.round_summaries[0].average_opinion:.2f}", '-', '-'],
                [final['contrarian'], final['neutral'], final['consensus'],
                 f"{tracker.round_summaries[-1].average_opinion:.2f}",
                 str(to_contrarian), str(to_consensus)],
                [f"{final['contrarian'] - initial['contrarian']:+d}",
                 f"{final['neutral'] - initial['neutral']:+d}",
                 f"{final['consensus'] - initial['consensus']:+d}",
                 f"{tracker.round_summaries[-1].average_opinion - tracker.round_summaries[0].average_opinion:+.2f}",
                 '-', '-']
            ],
            align='left'
        )
    ), row=2, col=2)

    fig.update_layout(
        height=800,
        title_text='Opinion Dynamics Simulation Dashboard',
        template='plotly_white',
        showlegend=True
    )

    return fig


def save_all_visualizations(tracker: SimulationTracker, output_dir: str, timestamp: str = "") -> List[str]:
    """
    Generate and save all visualizations.

    Args:
        tracker: SimulationTracker with data
        output_dir: Directory to save files
        timestamp: Optional timestamp suffix for filenames (empty = no suffix)

    Returns:
        List of saved file paths
    """
    import os
    os.makedirs(output_dir, exist_ok=True)

    saved_files = []

    # Build suffix (empty or _timestamp)
    suffix = f"_{timestamp}" if timestamp else ""

    # 1. Opinion trajectories
    fig = create_opinion_trajectories(tracker)
    path = f"{output_dir}/opinion_trajectories{suffix}.html"
    fig.write_html(path)
    saved_files.append(path)

    # 2. Behavioral heatmap
    fig = create_behavioral_heatmap(tracker)
    path = f"{output_dir}/behavioral_heatmap{suffix}.html"
    fig.write_html(path)
    saved_files.append(path)

    # 3. Emotional climate
    fig = create_emotional_climate_chart(tracker)
    path = f"{output_dir}/emotional_climate{suffix}.html"
    fig.write_html(path)
    saved_files.append(path)

    # 4. Opinion distribution
    fig = create_opinion_distribution_chart(tracker)
    path = f"{output_dir}/opinion_distribution{suffix}.html"
    fig.write_html(path)
    saved_files.append(path)

    # 5. Combined dashboard
    fig = create_dashboard(tracker)
    path = f"{output_dir}/dashboard{suffix}.html"
    fig.write_html(path)
    saved_files.append(path)

    return saved_files
