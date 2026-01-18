"""
Create a proper Stock-Flow Diagram using Graphviz.
Forrester notation: Stocks (boxes), Flows (arrows with valves), Auxiliaries (circles), Clouds
"""

import graphviz

def create_sfd():
    """Create a proper Forrester-style Stock-Flow Diagram."""

    dot = graphviz.Digraph(
        'SFD',
        comment='Opinion Dynamics Stock-Flow Diagram',
        format='svg',
        engine='dot'
    )

    # Graph attributes
    dot.attr(
        rankdir='TB',
        splines='ortho',
        nodesep='0.8',
        ranksep='1.0',
        fontname='Arial',
        bgcolor='white',
        label='Stock-Flow Diagram: Opinion Dynamics under Algorithmic Amplification\n\n',
        labelloc='t',
        fontsize='16'
    )

    # === STOCKS (rectangles with double border) ===
    with dot.subgraph(name='stocks') as s:
        s.attr(rank='same')

        # Stock style
        stock_style = {
            'shape': 'box',
            'style': 'filled,bold',
            'fillcolor': 'white',
            'penwidth': '3',
            'fontname': 'Arial',
            'fontsize': '11',
            'width': '1.5',
            'height': '0.8'
        }

        dot.node('N', 'NEUTRALS\n(N)\n━━━━━━━\n20 → 7',
                 color='#7f8c8d', **stock_style)
        dot.node('C', 'CONTRARIAN\nCONVERTS (C)\n━━━━━━━\n0 → 12.7',
                 color='#e74c3c', **stock_style)
        dot.node('S', 'CONSENSUS\nCONVERTS (S)\n━━━━━━━\n0 → 0.04',
                 color='#3498db', **stock_style)
        dot.node('A', 'AROUSAL\n(A)\n━━━━━━━\n0.47 → 0.89',
                 color='#e67e22', **stock_style)
        dot.node('F', 'FRAME\nADOPTION (F)\n━━━━━━━\n0 → 0.89',
                 color='#9b59b6', **stock_style)

    # === AUXILIARIES (circles/ellipses) ===
    aux_style = {
        'shape': 'ellipse',
        'style': 'filled',
        'fillcolor': '#f9f9f9',
        'fontname': 'Arial',
        'fontsize': '9',
        'width': '1.2',
        'height': '0.6'
    }

    dot.node('vis_C', 'Visibility_C\n(8.7x higher)', color='#c0392b', **aux_style)
    dot.node('vis_S', 'Visibility_S\n(baseline)', color='#2980b9', **aux_style)
    dot.node('exp_C', 'Exposure_C', color='#e74c3c', **aux_style)
    dot.node('exp_S', 'Exposure_S', color='#3498db', **aux_style)
    dot.node('sus', 'Susceptibility\n(arousal-dependent)', color='#8e44ad', **aux_style)
    dot.node('eng_sq', 'Engagement²\n(squared boost)', color='#d35400', **aux_style)

    # === CLOUDS (sources/sinks) ===
    cloud_style = {
        'shape': 'tripleoctagon',
        'style': 'filled',
        'fillcolor': '#ecf0f1',
        'fontname': 'Arial',
        'fontsize': '8',
        'width': '0.5',
        'height': '0.3'
    }

    dot.node('cloud1', '☁', **cloud_style)
    dot.node('cloud2', '☁', **cloud_style)
    dot.node('cloud3', '☁', **cloud_style)
    dot.node('cloud4', '☁', **cloud_style)

    # === FLOW VALVES (diamonds) ===
    valve_style = {
        'shape': 'diamond',
        'style': 'filled',
        'fillcolor': 'white',
        'fontname': 'Arial',
        'fontsize': '8',
        'width': '0.4',
        'height': '0.4'
    }

    dot.node('v_conv_C', '⊗\nconv_to_C', color='#e74c3c', **valve_style)
    dot.node('v_conv_S', '⊗\nconv_to_S', color='#3498db', **valve_style)
    dot.node('v_arousal_up', '⊗\narousal↑', color='#e67e22', **valve_style)
    dot.node('v_arousal_dn', '⊗\ndecay', color='#e67e22', **valve_style)
    dot.node('v_frame_up', '⊗\nadopt', color='#9b59b6', **valve_style)
    dot.node('v_frame_dn', '⊗\ndecay', color='#9b59b6', **valve_style)

    # === FEEDBACK LOOP MARKERS ===
    loop_style = {
        'shape': 'note',
        'style': 'filled',
        'fontname': 'Arial Bold',
        'fontsize': '9',
        'width': '1.8'
    }

    dot.node('R1', 'R1: Visibility-Arousal\n-Susceptibility Loop\n(REINFORCING)',
             fillcolor='#fadbd8', color='#e74c3c', **loop_style)
    dot.node('R2', 'R2: Framing\nCascade Loop\n(REINFORCING)',
             fillcolor='#e8daef', color='#9b59b6', **loop_style)
    dot.node('R3', 'R3: Population\nShift Loop\n(REINFORCING)',
             fillcolor='#fdebd0', color='#e67e22', **loop_style)
    dot.node('B1', 'B1: Pool Depletion\n(BALANCING)',
             fillcolor='#d5f5e3', color='#27ae60', **loop_style)

    # === MATERIAL FLOWS (thick solid arrows) ===
    flow_style = {'penwidth': '2.5', 'color': '#2c3e50'}

    # Neutrals to conversions
    dot.edge('N', 'v_conv_C', **flow_style)
    dot.edge('v_conv_C', 'C', **flow_style)
    dot.edge('N', 'v_conv_S', **flow_style)
    dot.edge('v_conv_S', 'S', **flow_style)

    # Arousal flows
    dot.edge('cloud1', 'v_arousal_up', penwidth='2', color='#e67e22')
    dot.edge('v_arousal_up', 'A', penwidth='2', color='#e67e22')
    dot.edge('A', 'v_arousal_dn', penwidth='2', color='#e67e22')
    dot.edge('v_arousal_dn', 'cloud2', penwidth='2', color='#e67e22')

    # Frame flows
    dot.edge('cloud3', 'v_frame_up', penwidth='2', color='#9b59b6')
    dot.edge('v_frame_up', 'F', penwidth='2', color='#9b59b6')
    dot.edge('F', 'v_frame_dn', penwidth='2', color='#9b59b6')
    dot.edge('v_frame_dn', 'cloud4', penwidth='2', color='#9b59b6')

    # === INFORMATION LINKS (thin dashed arrows) ===
    info_style = {'style': 'dashed', 'penwidth': '1', 'color': '#7f8c8d', 'arrowsize': '0.7'}

    # Algorithm creates visibility
    dot.edge('eng_sq', 'vis_C', label='  amplifies', **info_style)
    dot.edge('eng_sq', 'vis_S', **info_style)

    # Visibility creates exposure
    dot.edge('vis_C', 'exp_C', **info_style)
    dot.edge('vis_S', 'exp_S', **info_style)

    # Population affects exposure
    dot.edge('C', 'exp_C', label='  more sources', **info_style)
    dot.edge('S', 'exp_S', **info_style)

    # Exposure drives conversions
    dot.edge('exp_C', 'v_conv_C', **info_style)
    dot.edge('exp_S', 'v_conv_S', **info_style)

    # Exposure drives arousal
    dot.edge('exp_C', 'v_arousal_up', label='provokes', **info_style)

    # Arousal affects susceptibility
    dot.edge('A', 'sus', label='increases', **info_style)

    # Susceptibility affects conversion rate
    dot.edge('sus', 'v_conv_C', label='enables', **info_style)
    dot.edge('sus', 'v_conv_S', label='blocks\n(requires\nrational\nprocessing)',
             style='dashed', penwidth='1', color='#e74c3c', arrowsize='0.7')

    # Exposure drives frame adoption
    dot.edge('exp_C', 'v_frame_up', **info_style)

    # Frame adoption increases contrarian exposure (secondary propagation)
    dot.edge('F', 'exp_C', label='secondary\npropagation', **info_style)

    # === LAYOUT HINTS ===
    # Force certain nodes to same rank for cleaner layout
    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('vis_C')
        s.node('vis_S')
        s.node('eng_sq')

    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('exp_C')
        s.node('N')
        s.node('exp_S')

    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('C')
        s.node('sus')
        s.node('S')

    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('A')
        s.node('F')

    with dot.subgraph() as s:
        s.attr(rank='same')
        s.node('R1')
        s.node('R2')
        s.node('R3')
        s.node('B1')

    return dot


def create_simplified_sfd():
    """Create a cleaner, simplified SFD focusing on the key dynamics."""

    dot = graphviz.Digraph(
        'SFD_Simple',
        comment='Simplified Opinion Dynamics SFD',
        format='svg',
        engine='neato'  # neato gives better control over positioning
    )

    dot.attr(
        overlap='false',
        splines='true',
        fontname='Arial',
        bgcolor='white',
        label='\nSimplified Stock-Flow Diagram\nOpinion Dynamics under Algorithmic Amplification\n',
        labelloc='t',
        fontsize='14'
    )

    # Positions (using pos attribute with neato)
    # === STOCKS ===
    dot.node('N', 'NEUTRALS\n(N)\n20→7',
             shape='box', style='filled,bold', fillcolor='white',
             color='#7f8c8d', penwidth='3', fontsize='10',
             pos='3,4!')

    dot.node('C', 'CONTRARIAN\n(C)\n0→12.7',
             shape='box', style='filled,bold', fillcolor='white',
             color='#e74c3c', penwidth='3', fontsize='10',
             pos='1,2!')

    dot.node('S', 'CONSENSUS\n(S)\n0→0.04',
             shape='box', style='filled,bold', fillcolor='white',
             color='#3498db', penwidth='3', fontsize='10',
             pos='5,2!')

    dot.node('A', 'AROUSAL\n(A)\n0.47→0.89',
             shape='box', style='filled,bold', fillcolor='white',
             color='#e67e22', penwidth='3', fontsize='10',
             pos='3,0!')

    # === KEY AUXILIARIES ===
    dot.node('VIS', 'ALGORITHM\n(engagement²)',
             shape='ellipse', style='filled', fillcolor='#fef9e7',
             color='#f39c12', fontsize='9',
             pos='3,6!')

    dot.node('SUS', 'SUSCEPTIBILITY',
             shape='ellipse', style='filled', fillcolor='#fdedec',
             color='#e74c3c', fontsize='9',
             pos='3,2!')

    # === FLOWS ===
    # Main conversion flows (thick)
    dot.edge('N', 'C', label='  60%\n  convert',
             penwidth='4', color='#e74c3c')
    dot.edge('N', 'S', label='0%\nconvert  ',
             penwidth='1', color='#3498db', style='dashed')

    # === INFORMATION LINKS ===
    # Algorithm creates visibility asymmetry
    dot.edge('VIS', 'C', label='8.7x\nvisibility',
             style='dashed', color='#e74c3c', penwidth='2')
    dot.edge('VIS', 'S', label='1x',
             style='dashed', color='#3498db', penwidth='1')

    # Exposure creates arousal
    dot.edge('C', 'A', label='provokes',
             style='dashed', color='#e67e22')

    # Arousal increases susceptibility
    dot.edge('A', 'SUS', label='peripheral\nprocessing',
             style='dashed', color='#e67e22')

    # Susceptibility enables contrarian conversion
    dot.edge('SUS', 'C', label='enables',
             style='dashed', color='#c0392b', dir='back',
             constraint='false')

    # === FEEDBACK LOOPS ===
    dot.node('R1', 'R1: REINFORCING\nMore C → More Arousal\n→ More Susceptibility\n→ More C',
             shape='note', style='filled', fillcolor='#fadbd8',
             color='#e74c3c', fontsize='8',
             pos='0,0!')

    dot.node('B1', 'B1: BALANCING\nN depletes\n(but too slow)',
             shape='note', style='filled', fillcolor='#d5f5e3',
             color='#27ae60', fontsize='8',
             pos='6,0!')

    return dot


if __name__ == "__main__":
    # Create both versions
    sfd = create_sfd()
    sfd_simple = create_simplified_sfd()

    # Save as SVG and PNG
    output_dir = './results'

    sfd.render(f'{output_dir}/sfd_full', view=False, cleanup=True)
    sfd_simple.render(f'{output_dir}/sfd_simple', view=False, cleanup=True)

    print(f"Created: {output_dir}/sfd_full.svg")
    print(f"Created: {output_dir}/sfd_simple.svg")

    # Also create PDF versions
    sfd.format = 'pdf'
    sfd.render(f'{output_dir}/sfd_full', view=False, cleanup=True)

    sfd_simple.format = 'pdf'
    sfd_simple.render(f'{output_dir}/sfd_simple', view=False, cleanup=True)

    print(f"Created: {output_dir}/sfd_full.pdf")
    print(f"Created: {output_dir}/sfd_simple.pdf")
