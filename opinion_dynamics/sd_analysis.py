"""
System Dynamics Analysis Module

Provides:
- Sensitivity analysis on key parameters
- Policy experiments (what-if scenarios)
- Comparison with agent-based model results
- Equilibrium and stability analysis
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import json

from sd_model import OpinionDynamicsSD
from sd_parameters import SDParameters
from sd_visualization import create_comparison_chart


@dataclass
class SensitivityResult:
    """Result of sensitivity analysis for one parameter."""
    parameter_name: str
    base_value: float
    test_values: List[float]
    contrarian_converts: List[float]
    consensus_converts: List[float]
    peak_arousal: List[float]
    threshold_times: List[Optional[float]]

    def get_elasticity(self) -> float:
        """
        Calculate elasticity of contrarian converts to parameter change.

        Elasticity = (% change in output) / (% change in input)
        """
        if len(self.test_values) < 3:
            return 0.0

        mid_idx = len(self.test_values) // 2
        low_idx = 0
        high_idx = -1

        # % change in parameter
        param_change = ((self.test_values[high_idx] - self.test_values[low_idx]) /
                        self.base_value * 100)

        # % change in output
        output_change = ((self.contrarian_converts[high_idx] - self.contrarian_converts[low_idx]) /
                         max(0.1, self.contrarian_converts[mid_idx]) * 100)

        if abs(param_change) < 0.01:
            return 0.0

        return output_change / param_change


def sensitivity_analysis(
    param_name: str,
    values: List[float],
    base_params: Optional[SDParameters] = None
) -> SensitivityResult:
    """
    Run sensitivity analysis for a single parameter.

    Args:
        param_name: Name of parameter to vary
        values: List of values to test
        base_params: Base parameters (uses defaults if None)

    Returns:
        SensitivityResult with all outcomes
    """
    base_params = base_params or SDParameters()
    base_value = getattr(base_params, param_name)

    contrarian_converts = []
    consensus_converts = []
    peak_arousal = []
    threshold_times = []

    for value in values:
        # Create modified parameters
        params = SDParameters()
        setattr(params, param_name, value)

        # Run simulation
        model = OpinionDynamicsSD(params)
        model.run()

        final = model.get_final_state()
        contrarian_converts.append(final.contrarian_converts)
        consensus_converts.append(final.consensus_converts)
        peak_arousal.append(max(s.arousal for s in model.state_history))
        threshold_times.append(model.find_threshold_crossing())

    return SensitivityResult(
        parameter_name=param_name,
        base_value=base_value,
        test_values=values,
        contrarian_converts=contrarian_converts,
        consensus_converts=consensus_converts,
        peak_arousal=peak_arousal,
        threshold_times=threshold_times
    )


def full_sensitivity_analysis() -> Dict[str, SensitivityResult]:
    """
    Run sensitivity analysis on all key parameters.

    Returns:
        Dictionary of parameter name -> SensitivityResult
    """
    base = SDParameters()
    results = {}

    # Parameters to analyze with their test ranges
    param_ranges = {
        'arousal_contagion_rate': np.linspace(0.04, 0.24, 5),
        'arousal_decay_rate': np.linspace(0.005, 0.04, 5),
        'threshold_arousal': np.linspace(0.8, 0.99, 5),
        'threshold_multiplier': np.linspace(1.5, 6.0, 5),
        'base_conversion_rate': np.linspace(0.005, 0.04, 5),
        'arousal_amplifier': np.linspace(1.0, 4.0, 5),
        'contrarian_emotion': np.linspace(0.3, 0.8, 5),
        'frame_adoption_rate': np.linspace(0.02, 0.12, 5),
    }

    for param_name, values in param_ranges.items():
        print(f"  Analyzing {param_name}...")
        results[param_name] = sensitivity_analysis(param_name, list(values))

    return results


def create_tornado_chart(sensitivity_results: Dict[str, SensitivityResult]):
    """
    Create tornado chart showing parameter elasticities.

    Parameters are ranked by their impact on contrarian conversions.
    """
    import plotly.graph_objects as go

    # Calculate elasticities
    elasticities = []
    for name, result in sensitivity_results.items():
        e = result.get_elasticity()
        elasticities.append((name, e))

    # Sort by absolute elasticity
    elasticities.sort(key=lambda x: abs(x[1]), reverse=True)

    names = [e[0] for e in elasticities]
    values = [e[1] for e in elasticities]

    colors = ['#e74c3c' if v > 0 else '#3498db' for v in values]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        y=names,
        x=values,
        orientation='h',
        marker_color=colors,
        text=[f'{v:.2f}' for v in values],
        textposition='outside'
    ))

    fig.update_layout(
        title='Parameter Sensitivity: Elasticity of Contrarian Conversions',
        xaxis_title='Elasticity (% change in converts / % change in parameter)',
        template='plotly_white',
        height=400
    )

    return fig


def run_policy_experiment(policy_name: str) -> Tuple[OpinionDynamicsSD, Dict]:
    """
    Run a predefined policy experiment.

    Available policies:
    - 'reduced_bias': Reduce algorithmic visibility bias
    - 'cooling_off': Increase arousal decay (cooling-off periods)
    - 'friction': Add friction to content sharing

    Returns:
        Tuple of (model, summary)
    """
    if policy_name == 'reduced_bias':
        params = SDParameters.policy_reduced_bias()
    elif policy_name == 'cooling_off':
        params = SDParameters.policy_cooling_off()
    elif policy_name == 'friction':
        params = SDParameters.policy_friction()
    else:
        raise ValueError(f"Unknown policy: {policy_name}")

    model = OpinionDynamicsSD(params)
    model.run()

    return model, model.get_summary()


def compare_all_policies() -> Dict[str, Dict]:
    """
    Run all policy experiments and compare results.

    Returns:
        Dictionary with baseline and all policy outcomes
    """
    results = {}

    # Baseline
    baseline = OpinionDynamicsSD()
    baseline.run()
    results['baseline'] = baseline.get_summary()

    # Policies
    for policy in ['reduced_bias', 'cooling_off', 'friction']:
        model, summary = run_policy_experiment(policy)
        results[policy] = summary

    return results


def find_intervention_threshold() -> Dict[str, float]:
    """
    Find parameter values that prevent majority contrarian conversion.

    Tests what parameter changes would keep contrarian converts below 50%.

    Returns:
        Dictionary of parameter -> threshold value
    """
    thresholds = {}
    target_converts = 10  # Less than 50% of 20 neutrals

    # Test arousal decay rate
    for decay in np.linspace(0.01, 0.1, 20):
        params = SDParameters()
        params.arousal_decay_rate = decay
        model = OpinionDynamicsSD(params)
        model.run()
        if model.get_final_state().contrarian_converts < target_converts:
            thresholds['arousal_decay_rate'] = decay
            break

    # Test visibility ratio (via emotion weight)
    for emotion_w in np.linspace(0.4, 0.1, 20):
        params = SDParameters()
        params.emotion_weight = emotion_w
        params.provocative_weight = emotion_w
        model = OpinionDynamicsSD(params)
        model.run()
        if model.get_final_state().contrarian_converts < target_converts:
            thresholds['emotion_weight'] = emotion_w
            break

    # Test contagion rate
    for contagion in np.linspace(0.12, 0.02, 20):
        params = SDParameters()
        params.arousal_contagion_rate = contagion
        model = OpinionDynamicsSD(params)
        model.run()
        if model.get_final_state().contrarian_converts < target_converts:
            thresholds['arousal_contagion_rate'] = contagion
            break

    return thresholds


def equilibrium_analysis(params: Optional[SDParameters] = None) -> Dict:
    """
    Analyze equilibrium behavior of the system.

    Determines if system reaches stable equilibrium or continues drifting.

    Returns:
        Dictionary with equilibrium analysis results
    """
    params = params or SDParameters()

    # Run for extended time
    model = OpinionDynamicsSD(params)
    model.run(t_final=200)

    history = model.state_history

    # Check for convergence in last 20% of simulation
    late_states = history[int(len(history) * 0.8):]

    # Calculate variance in stocks
    n_var = np.var([s.neutrals for s in late_states])
    c_var = np.var([s.contrarian_converts for s in late_states])
    a_var = np.var([s.arousal for s in late_states])

    # System is at equilibrium if variance is very low
    at_equilibrium = (n_var < 0.01 and c_var < 0.01 and a_var < 0.0001)

    return {
        'at_equilibrium': at_equilibrium,
        'final_neutrals': history[-1].neutrals,
        'final_contrarian': history[-1].contrarian_converts,
        'final_arousal': history[-1].arousal,
        'neutrals_variance': n_var,
        'contrarian_variance': c_var,
        'arousal_variance': a_var,
        'extended_simulation_time': 200,
    }


def validate_against_abm(abm_results: Dict) -> Dict:
    """
    Validate SD model against agent-based model results.

    Args:
        abm_results: Dictionary with ABM results:
            - to_contrarian: number of conversions to contrarian
            - to_consensus: number of conversions to consensus
            - peak_arousal: maximum arousal observed
            - threshold_round: round when mass conversion occurred

    Returns:
        Validation results with match scores
    """
    model = OpinionDynamicsSD()
    model.run()
    sd = model.get_summary()

    validation = {
        'contrarian_converts': {
            'SD': sd['final']['contrarian_converts'],
            'ABM': abm_results.get('to_contrarian', 12),
            'error': abs(sd['final']['contrarian_converts'] - abm_results.get('to_contrarian', 12)),
            'match': abs(sd['final']['contrarian_converts'] - abm_results.get('to_contrarian', 12)) < 3,
        },
        'consensus_converts': {
            'SD': sd['final']['consensus_converts'],
            'ABM': abm_results.get('to_consensus', 0),
            'error': abs(sd['final']['consensus_converts'] - abm_results.get('to_consensus', 0)),
            'match': abs(sd['final']['consensus_converts'] - abm_results.get('to_consensus', 0)) < 1,
        },
        'peak_arousal': {
            'SD': sd['dynamics']['peak_arousal'],
            'ABM': abm_results.get('peak_arousal', 0.93),
            'error': abs(sd['dynamics']['peak_arousal'] - abm_results.get('peak_arousal', 0.93)),
            'match': abs(sd['dynamics']['peak_arousal'] - abm_results.get('peak_arousal', 0.93)) < 0.1,
        },
    }

    # Overall match score
    matches = sum(1 for v in validation.values() if v['match'])
    validation['overall_match_score'] = matches / len(validation)

    return validation


if __name__ == "__main__":
    print("System Dynamics Analysis")
    print("=" * 60)

    # Run baseline
    print("\n1. Baseline Simulation")
    baseline = OpinionDynamicsSD()
    baseline.run()
    summary = baseline.get_summary()
    print(f"   Final contrarian converts: {summary['final']['contrarian_converts']:.1f}")
    print(f"   Peak arousal: {summary['dynamics']['peak_arousal']:.3f}")

    # Sensitivity analysis (abbreviated)
    print("\n2. Sensitivity Analysis (key parameters)")
    for param in ['arousal_contagion_rate', 'threshold_arousal']:
        base = SDParameters()
        base_val = getattr(base, param)
        values = [base_val * 0.5, base_val, base_val * 1.5]
        result = sensitivity_analysis(param, values)
        print(f"   {param}:")
        print(f"      Values: {[f'{v:.3f}' for v in values]}")
        print(f"      Converts: {[f'{c:.1f}' for c in result.contrarian_converts]}")

    # Policy experiments
    print("\n3. Policy Experiments")
    for policy in ['reduced_bias', 'cooling_off', 'friction']:
        model, summary = run_policy_experiment(policy)
        print(f"   {policy}:")
        print(f"      Contrarian converts: {summary['final']['contrarian_converts']:.1f}")
        print(f"      Peak arousal: {summary['dynamics']['peak_arousal']:.3f}")

    # Validation against ABM
    print("\n4. Validation Against Agent-Based Model")
    abm_results = {
        'to_contrarian': 12,
        'to_consensus': 0,
        'peak_arousal': 0.93,
    }
    validation = validate_against_abm(abm_results)
    print(f"   Match score: {validation['overall_match_score']*100:.0f}%")
    for metric, data in validation.items():
        if isinstance(data, dict):
            print(f"   {metric}: SD={data['SD']:.2f}, ABM={data['ABM']}, {'MATCH' if data['match'] else 'MISMATCH'}")

    # Intervention thresholds
    print("\n5. Intervention Thresholds (to prevent majority conversion)")
    thresholds = find_intervention_threshold()
    for param, value in thresholds.items():
        base = SDParameters()
        base_val = getattr(base, param)
        print(f"   {param}: {value:.3f} (baseline: {base_val:.3f})")
