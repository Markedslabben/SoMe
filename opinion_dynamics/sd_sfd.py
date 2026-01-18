"""
Stock-Flow Diagram (SFD) Visualization

Creates a Forrester-style Stock-Flow Diagram showing:
- Stocks (rectangles): N, C, S, A, F
- Flows (arrows with valves): conversions, arousal change, frame adoption
- Auxiliaries (circles): visibility, exposure, susceptibility
- Feedback loops marked
"""

import plotly.graph_objects as go
from typing import Tuple, List


def create_sfd() -> go.Figure:
    """
    Create a Stock-Flow Diagram for the Opinion Dynamics model.

    Uses Forrester's notation:
    - Rectangles: Stocks (state variables)
    - Arrows with hourglass: Flows (rates)
    - Circles: Auxiliaries
    - Clouds: Sources/sinks (outside system boundary)
    """
    fig = go.Figure()

    # === STOCKS (Rectangles) ===
    stocks = {
        'N': {'pos': (0.5, 0.7), 'label': 'Neutrals\n(N)', 'color': '#95a5a6'},
        'C': {'pos': (0.15, 0.4), 'label': 'Contrarian\nConverts (C)', 'color': '#e74c3c'},
        'S': {'pos': (0.85, 0.4), 'label': 'Consensus\nConverts (S)', 'color': '#3498db'},
        'A': {'pos': (0.5, 0.25), 'label': 'Arousal\n(A)', 'color': '#e67e22'},
        'F': {'pos': (0.15, 0.1), 'label': 'Frame\nAdoption (F)', 'color': '#9b59b6'},
    }

    # Draw stocks as rectangles
    for name, props in stocks.items():
        x, y = props['pos']
        w, h = 0.12, 0.08

        # Rectangle shape
        fig.add_shape(
            type="rect",
            x0=x-w/2, y0=y-h/2, x1=x+w/2, y1=y+h/2,
            line=dict(color=props['color'], width=3),
            fillcolor='white',
        )

        # Stock label
        fig.add_annotation(
            x=x, y=y,
            text=props['label'],
            showarrow=False,
            font=dict(size=10, color=props['color']),
        )

    # === FLOWS (Arrows with valves) ===
    flows = [
        # (from, to, label, color, curve)
        ('N', 'C', 'conv_to_C', '#e74c3c', -0.1),
        ('N', 'S', 'conv_to_S', '#3498db', 0.1),
        ('cloud_A_in', 'A', 'arousal_up', '#e67e22', 0),
        ('A', 'cloud_A_out', 'arousal_decay', '#e67e22', 0),
        ('cloud_F_in', 'F', 'frame_adopt', '#9b59b6', 0),
        ('F', 'cloud_F_out', 'frame_decay', '#9b59b6', 0),
    ]

    # Cloud positions (sources/sinks)
    clouds = {
        'cloud_A_in': (0.3, 0.25),
        'cloud_A_out': (0.7, 0.25),
        'cloud_F_in': (0.0, 0.1),
        'cloud_F_out': (0.3, 0.1),
    }

    # Draw flows
    for from_node, to_node, label, color, curve in flows:
        if from_node.startswith('cloud'):
            x0, y0 = clouds[from_node]
        else:
            x0, y0 = stocks[from_node]['pos']

        if to_node.startswith('cloud'):
            x1, y1 = clouds[to_node]
        else:
            x1, y1 = stocks[to_node]['pos']

        # Flow arrow
        fig.add_annotation(
            x=x1, y=y1,
            ax=x0, ay=y0,
            xref='x', yref='y',
            axref='x', ayref='y',
            showarrow=True,
            arrowhead=2,
            arrowsize=1.2,
            arrowwidth=2,
            arrowcolor=color,
        )

        # Flow valve (hourglass symbol at midpoint)
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2 + curve
        fig.add_trace(go.Scatter(
            x=[mx], y=[my],
            mode='markers',
            marker=dict(size=12, symbol='hourglass', color=color),
            hoverinfo='text',
            hovertext=label,
            showlegend=False,
        ))

        # Flow label
        fig.add_annotation(
            x=mx, y=my + 0.03,
            text=label.replace('_', ' '),
            showarrow=False,
            font=dict(size=8, color=color),
        )

    # === AUXILIARIES (Circles) ===
    auxiliaries = {
        'vis_C': {'pos': (0.15, 0.7), 'label': 'Visibility_C', 'color': '#e74c3c'},
        'vis_S': {'pos': (0.85, 0.7), 'label': 'Visibility_S', 'color': '#3498db'},
        'exp_C': {'pos': (0.3, 0.55), 'label': 'Exposure_C', 'color': '#c0392b'},
        'exp_S': {'pos': (0.7, 0.55), 'label': 'Exposure_S', 'color': '#2980b9'},
        'sus': {'pos': (0.5, 0.45), 'label': 'Susceptibility', 'color': '#8e44ad'},
    }

    for name, props in auxiliaries.items():
        x, y = props['pos']

        # Circle marker
        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode='markers+text',
            marker=dict(size=30, color='white',
                       line=dict(color=props['color'], width=2)),
            text=[props['label']],
            textposition='middle center',
            textfont=dict(size=7, color=props['color']),
            hoverinfo='text',
            hovertext=props['label'],
            showlegend=False,
        ))

    # === INFORMATION LINKS (dashed arrows) ===
    info_links = [
        # Visibility to Exposure
        ('vis_C', 'exp_C'),
        ('vis_S', 'exp_S'),
        # Population to Exposure
        ('C', 'exp_C'),
        ('S', 'exp_S'),
        # Exposure to Arousal flow
        ('exp_C', (0.4, 0.25)),
        # Arousal to Susceptibility
        ('A', 'sus'),
        # Susceptibility to Conversion flows
        ('sus', (0.3, 0.55)),
        # Exposure to Conversion
        ('exp_C', (0.3, 0.55)),
        ('exp_S', (0.7, 0.55)),
        # Frame to Exposure (secondary propagation)
        ('F', 'exp_C'),
        # Exposure to Frame adoption
        ('exp_C', (0.075, 0.1)),
    ]

    for link in info_links:
        if isinstance(link[0], str) and link[0] in auxiliaries:
            x0, y0 = auxiliaries[link[0]]['pos']
        elif isinstance(link[0], str) and link[0] in stocks:
            x0, y0 = stocks[link[0]]['pos']
        else:
            x0, y0 = link[0]

        if isinstance(link[1], str) and link[1] in auxiliaries:
            x1, y1 = auxiliaries[link[1]]['pos']
        elif isinstance(link[1], str) and link[1] in stocks:
            x1, y1 = stocks[link[1]]['pos']
        else:
            x1, y1 = link[1]

        fig.add_annotation(
            x=x1, y=y1,
            ax=x0, ay=y0,
            xref='x', yref='y',
            axref='x', ayref='y',
            showarrow=True,
            arrowhead=3,
            arrowsize=0.8,
            arrowwidth=1,
            arrowcolor='gray',
            opacity=0.5,
        )

    # === FEEDBACK LOOP MARKERS ===
    loop_markers = [
        {'pos': (0.35, 0.35), 'label': 'R1\nVisibility-Arousal\n-Susceptibility', 'color': 'red'},
        {'pos': (0.15, 0.25), 'label': 'R2\nFraming\nCascade', 'color': 'purple'},
        {'pos': (0.25, 0.55), 'label': 'R3\nPopulation\nShift', 'color': 'orange'},
    ]

    for marker in loop_markers:
        x, y = marker['pos']
        fig.add_annotation(
            x=x, y=y,
            text=marker['label'],
            showarrow=False,
            font=dict(size=8, color=marker['color']),
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor=marker['color'],
            borderwidth=1,
        )

    # === LAYOUT ===
    fig.update_layout(
        title={
            'text': 'Stock-Flow Diagram: Opinion Dynamics under Algorithmic Amplification',
            'x': 0.5,
            'font': dict(size=14)
        },
        xaxis=dict(
            visible=False,
            range=[-0.05, 1.05],
            scaleanchor='y',
            scaleratio=1,
        ),
        yaxis=dict(
            visible=False,
            range=[-0.02, 0.85],
        ),
        template='plotly_white',
        height=700,
        width=900,
        showlegend=False,
        annotations=[
            # Legend
            dict(x=0.95, y=0.02, text="<b>Legend:</b>", showarrow=False, font=dict(size=9)),
            dict(x=0.95, y=-0.01, text="▭ Stock", showarrow=False, font=dict(size=8)),
            dict(x=0.95, y=-0.04, text="⊗ Flow valve", showarrow=False, font=dict(size=8)),
            dict(x=0.95, y=-0.07, text="○ Auxiliary", showarrow=False, font=dict(size=8)),
        ]
    )

    return fig


def create_sfd_text() -> str:
    """
    Create ASCII text representation of the Stock-Flow Diagram.
    """
    sfd = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                    STOCK-FLOW DIAGRAM: OPINION DYNAMICS                       ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║    ┌─────────────┐                                      ┌─────────────┐       ║
║    │ Visibility_C│                                      │ Visibility_S│       ║
║    └──────┬──────┘                                      └──────┬──────┘       ║
║           │                                                    │              ║
║           ▼                                                    ▼              ║
║    ┌─────────────┐         ╔═══════════════╗         ┌─────────────┐         ║
║    │  Exposure_C │◄────────║   NEUTRALS    ║────────►│  Exposure_S │         ║
║    └──────┬──────┘         ║     (N)       ║         └──────┬──────┘         ║
║           │                ║   [20 → 7]    ║                │                ║
║           │                ╚═══════╤═══════╝                │                ║
║           │                   ┌────┴────┐                   │                ║
║           │             conv_to_C  conv_to_S                │                ║
║           │                   ⊗         ⊗                   │                ║
║           │                   │         │                   │                ║
║           │                   ▼         ▼                   │                ║
║           │    ╔═══════════════╗   ╔═══════════════╗        │                ║
║           │    ║  CONTRARIAN   ║   ║   CONSENSUS   ║        │                ║
║           │    ║  CONVERTS (C) ║   ║  CONVERTS (S) ║        │                ║
║           │    ║   [0 → 12.7]  ║   ║   [0 → 0.04]  ║        │                ║
║           │    ╚═══════════════╝   ╚═══════════════╝        │                ║
║           │                                                  │                ║
║           │         ┌─────────────────────┐                 │                ║
║           └────────►│   Susceptibility    │◄────────────────┘                ║
║                     └──────────┬──────────┘                                  ║
║                                │                                              ║
║                                ▼                                              ║
║     ☁ ──arousal_up──⊗──► ╔═══════════════╗ ──⊗──arousal_decay──► ☁          ║
║                          ║    AROUSAL    ║                                    ║
║                          ║      (A)      ║                                    ║
║                          ║ [0.47 → 0.89] ║                                    ║
║                          ╚═══════════════╝                                    ║
║                                 │                                             ║
║     ☁ ──frame_adopt──⊗──► ╔═══════════════╗ ──⊗──frame_decay──► ☁           ║
║                           ║ FRAME ADOPT.  ║                                   ║
║                           ║      (F)      ║                                   ║
║                           ║  [0 → 0.89]   ║                                   ║
║                           ╚═══════════════╝                                   ║
║                                                                               ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  FEEDBACK LOOPS:                                                              ║
║  ┌────────────────────────────────────────────────────────────────────────┐  ║
║  │ R1: Exposure_C → Arousal ↑ → Susceptibility ↑ → conv_to_C ↑ → C ↑     │  ║
║  │     → Exposure_C ↑  [REINFORCING - Visibility-Arousal-Susceptibility] │  ║
║  ├────────────────────────────────────────────────────────────────────────┤  ║
║  │ R2: Exposure_C → Frame Adoption ↑ → Secondary Propagation ↑           │  ║
║  │     → Exposure_C ↑  [REINFORCING - Framing Cascade]                   │  ║
║  ├────────────────────────────────────────────────────────────────────────┤  ║
║  │ R3: conv_to_C → C ↑ → Exposure_C ↑ → conv_to_C ↑                      │  ║
║  │     [REINFORCING - Population Shift]                                   │  ║
║  ├────────────────────────────────────────────────────────────────────────┤  ║
║  │ B1: Arousal ↑ → arousal_decay ↑ → Arousal ↓  [BALANCING]              │  ║
║  │ B2: conv_to_C → N ↓ → conv_to_C ↓  [BALANCING - Pool Depletion]       │  ║
║  └────────────────────────────────────────────────────────────────────────┘  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  LEGEND:  ╔═══╗ Stock    ⊗ Flow valve    ─► Information link    ☁ Cloud     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    return sfd


def create_equations_summary() -> str:
    """
    Create summary of stock-flow equations.
    """
    equations = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                         STOCK-FLOW EQUATIONS                                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║  STOCKS (Integrals):                                                          ║
║  ───────────────────                                                          ║
║  N(t) = N(0) + ∫[-conv_to_C - conv_to_S] dt                                  ║
║  C(t) = C(0) + ∫[conv_to_C] dt                                               ║
║  S(t) = S(0) + ∫[conv_to_S] dt                                               ║
║  A(t) = A(0) + ∫[arousal_up - arousal_decay] dt                              ║
║  F(t) = F(0) + ∫[frame_adopt - frame_decay] dt                               ║
║                                                                               ║
║  FLOWS (Rates):                                                               ║
║  ──────────────                                                               ║
║  conv_to_C = base_rate × susceptibility × exposure_C × N                     ║
║  conv_to_S = base_rate × (1/(1 + arousal_amp × A)) × exposure_S × N          ║
║  arousal_up = contagion_rate × exposure_C × provoc_C × (1 - A)               ║
║  arousal_decay = decay_rate × A                                               ║
║  frame_adopt = adopt_rate × effective_exposure × (1 - F)                     ║
║  frame_decay = decay_rate × F                                                 ║
║                                                                               ║
║  AUXILIARIES:                                                                 ║
║  ────────────                                                                 ║
║  visibility_C = (emo_w × emo_C + prov_w × prov_C) × engagement²              ║
║  visibility_S = (emo_w × emo_S + prov_w × prov_S) × engagement²              ║
║  exposure_C = vis_C × (fixed_C + C) × (1 + secondary × F) / total_vis        ║
║  exposure_S = vis_S × (fixed_S + S) / total_vis                              ║
║  susceptibility = base_sus × (1 + amp × A) × threshold_effect(A)             ║
║                                                                               ║
║  THRESHOLD FUNCTION:                                                          ║
║  ──────────────────                                                           ║
║  threshold_effect(A) = 1 + (multiplier - 1) × sigmoid((A - 0.93) / 0.05)     ║
║                                                                               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
    return equations


if __name__ == "__main__":
    # Print text SFD
    print(create_sfd_text())
    print(create_equations_summary())

    # Create and save interactive SFD
    fig = create_sfd()
    fig.write_html("./results/sd_stock_flow_diagram.html")
    print("\nInteractive SFD saved to: ./results/sd_stock_flow_diagram.html")

    # Also show it
    fig.show()
