"""
System Dynamics Model Entry Point

CLI interface for the Opinion Dynamics System Dynamics model.

Usage:
    python sd_main.py                     # Run baseline simulation
    python sd_main.py --policy reduced_bias  # Run policy experiment
    python sd_main.py --sensitivity       # Run sensitivity analysis
    python sd_main.py --validate          # Validate against ABM results
"""

import argparse
import os
from datetime import datetime
import json

from sd_parameters import SDParameters
from sd_model import OpinionDynamicsSD
from sd_visualization import (
    save_all_visualizations,
    create_stock_trajectories,
    create_comparison_chart,
)
from sd_analysis import (
    full_sensitivity_analysis,
    create_tornado_chart,
    run_policy_experiment,
    compare_all_policies,
    validate_against_abm,
    equilibrium_analysis,
)


def run_baseline(output_dir: str, verbose: bool = True) -> dict:
    """Run baseline simulation and generate outputs."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if verbose:
        print("=" * 60)
        print("SYSTEM DYNAMICS MODEL: Opinion Dynamics")
        print("=" * 60)
        print("Based on Forrester's System Dynamics methodology")
        print()

    # Create and run model
    params = SDParameters()
    model = OpinionDynamicsSD(params)

    if verbose:
        print("Parameters:")
        print(f"  Initial neutrals: {params.initial_neutrals}")
        print(f"  Fixed contrarians: {params.fixed_contrarians}")
        print(f"  Fixed consensus: {params.fixed_consensus}")
        print(f"  Visibility ratio: {params.visibility_ratio:.2f}x")
        print(f"  Threshold arousal: {params.threshold_arousal}")
        print()
        print("Running simulation...")

    model.run()

    if verbose:
        print("Simulation complete.")
        print()

    # Get summary
    summary = model.get_summary()

    if verbose:
        print("RESULTS:")
        print("-" * 40)
        print(f"Final State (t={params.t_final}):")
        print(f"  Neutrals: {summary['final']['neutrals']:.1f}")
        print(f"  Contrarian converts: {summary['final']['contrarian_converts']:.1f}")
        print(f"  Consensus converts: {summary['final']['consensus_converts']:.2f}")
        print(f"  Arousal: {summary['final']['arousal']:.3f}")
        print(f"  Frame adoption: {summary['final']['frame_adoption']:.3f}")
        print()
        print("Dynamics:")
        print(f"  Threshold crossing: t={summary['dynamics']['threshold_crossing_time']}")
        print(f"  Peak arousal: {summary['dynamics']['peak_arousal']:.3f}")
        print()
        print("Conversion Rates:")
        print(f"  To contrarian: {summary['conversion_rates']['to_contrarian_pct']:.1f}%")
        print(f"  To consensus: {summary['conversion_rates']['to_consensus_pct']:.1f}%")
        print()

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Save visualizations
    viz_files = save_all_visualizations(model, output_dir, timestamp)

    if verbose:
        print("Visualizations saved:")
        for f in viz_files:
            print(f"  - {f}")

    # Save summary
    summary_path = f"{output_dir}/sd_summary_{timestamp}.json"
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2, default=str)

    if verbose:
        print(f"\nSummary saved: {summary_path}")
        print("=" * 60)

    return summary


def run_policy_comparison(output_dir: str, verbose: bool = True) -> dict:
    """Run all policy experiments and compare."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if verbose:
        print("=" * 60)
        print("POLICY EXPERIMENT COMPARISON")
        print("=" * 60)
        print()

    results = compare_all_policies()

    if verbose:
        print("Results:")
        print("-" * 40)
        print(f"{'Scenario':<20} {'C-Converts':<12} {'Peak Arousal':<12}")
        print("-" * 40)
        for name, summary in results.items():
            print(f"{name:<20} {summary['final']['contrarian_converts']:<12.1f} "
                  f"{summary['dynamics']['peak_arousal']:<12.3f}")
        print()

    # Create comparison visualization
    baseline = OpinionDynamicsSD()
    baseline.run()

    policy_models = {}
    for policy in ['reduced_bias', 'cooling_off', 'friction']:
        model, _ = run_policy_experiment(policy)
        policy_models[policy] = model

    fig = create_comparison_chart(baseline, policy_models)
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/sd_policy_comparison_{timestamp}.html"
    fig.write_html(path)

    if verbose:
        print(f"Comparison chart saved: {path}")
        print("=" * 60)

    return results


def run_sensitivity(output_dir: str, verbose: bool = True) -> dict:
    """Run full sensitivity analysis."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if verbose:
        print("=" * 60)
        print("SENSITIVITY ANALYSIS")
        print("=" * 60)
        print()
        print("Analyzing parameter sensitivity...")

    results = full_sensitivity_analysis()

    if verbose:
        print("\nElasticity Rankings (impact on contrarian converts):")
        print("-" * 50)
        elasticities = [(name, r.get_elasticity()) for name, r in results.items()]
        elasticities.sort(key=lambda x: abs(x[1]), reverse=True)
        for name, e in elasticities:
            direction = "+" if e > 0 else ""
            print(f"  {name:<30} {direction}{e:.3f}")
        print()

    # Create tornado chart
    fig = create_tornado_chart(results)
    os.makedirs(output_dir, exist_ok=True)
    path = f"{output_dir}/sd_sensitivity_tornado_{timestamp}.html"
    fig.write_html(path)

    if verbose:
        print(f"Tornado chart saved: {path}")
        print("=" * 60)

    return {name: r.__dict__ for name, r in results.items()}


def run_validation(verbose: bool = True) -> dict:
    """Validate SD model against ABM results."""
    if verbose:
        print("=" * 60)
        print("VALIDATION AGAINST AGENT-BASED MODEL")
        print("=" * 60)
        print()

    # ABM results from simulation
    abm_results = {
        'to_contrarian': 12,
        'to_consensus': 0,
        'peak_arousal': 0.93,
        'threshold_round': 46,
    }

    validation = validate_against_abm(abm_results)

    if verbose:
        print("Comparison:")
        print("-" * 50)
        print(f"{'Metric':<25} {'SD Model':<12} {'ABM':<12} {'Status'}")
        print("-" * 50)
        for metric, data in validation.items():
            if isinstance(data, dict):
                status = "MATCH" if data['match'] else "MISMATCH"
                print(f"{metric:<25} {data['SD']:<12.2f} {data['ABM']:<12} {status}")
        print("-" * 50)
        print(f"Overall match score: {validation['overall_match_score']*100:.0f}%")
        print()

        # Equilibrium analysis
        print("Equilibrium Analysis:")
        eq = equilibrium_analysis()
        print(f"  At equilibrium: {'Yes' if eq['at_equilibrium'] else 'No'}")
        print(f"  Final neutrals: {eq['final_neutrals']:.2f}")
        print(f"  Final contrarian: {eq['final_contrarian']:.2f}")
        print("=" * 60)

    return validation


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="System Dynamics Model for Opinion Dynamics"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./results",
        help="Output directory (default: ./results)"
    )
    parser.add_argument(
        "--policy",
        type=str,
        choices=['reduced_bias', 'cooling_off', 'friction', 'all'],
        help="Run specific policy experiment or 'all' for comparison"
    )
    parser.add_argument(
        "--sensitivity",
        action="store_true",
        help="Run sensitivity analysis"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate against ABM results"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Suppress verbose output"
    )

    args = parser.parse_args()
    verbose = not args.quiet

    try:
        if args.sensitivity:
            run_sensitivity(args.output, verbose)
        elif args.validate:
            run_validation(verbose)
        elif args.policy:
            if args.policy == 'all':
                run_policy_comparison(args.output, verbose)
            else:
                model, summary = run_policy_experiment(args.policy)
                if verbose:
                    print(f"Policy: {args.policy}")
                    print(f"  Contrarian converts: {summary['final']['contrarian_converts']:.1f}")
                    print(f"  Peak arousal: {summary['dynamics']['peak_arousal']:.3f}")
        else:
            # Default: run baseline
            run_baseline(args.output, verbose)

        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
