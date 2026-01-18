"""
Entry point for the Opinion Dynamics Simulation.

Usage:
    python main.py                          # Run with defaults
    python main.py --rounds 20              # Short run
    python main.py --output ./my_results    # Custom output dir
    python main.py --api-key sk-xxx         # Explicit API key
"""

import os
import argparse
from datetime import datetime

from models import SimulationConfig
from simulation import SimulationEngine
from visualization import save_all_visualizations
from amplification import analyze_amplification_bias


def run_experiment(
    api_key: str,
    num_rounds: int = 50,
    output_dir: str = "./results",
    verbose: bool = True
) -> dict:
    """
    Run the complete opinion dynamics experiment.

    Args:
        api_key: Anthropic API key
        num_rounds: Number of debate rounds
        output_dir: Directory to save results
        verbose: Print progress

    Returns:
        Summary statistics dictionary
    """
    # Configuration
    config = SimulationConfig(
        num_contrarians=1,
        num_consensus=4,
        num_neutrals=20,
        num_rounds=num_rounds,
        posts_per_round=5,
        debate_topic=(
            "The Energy Transition: Should we rely primarily on renewables, nuclear, "
            "or a mix? How should the electricity market be structured? "
            "Are current consumer electricity prices and energy taxes justified?"
        ),
        model="claude-sonnet-4-20250514",
        max_tokens_per_response=120
    )

    # Initialize and run
    if verbose:
        print("=" * 60)
        print("OPINION DYNAMICS SIMULATION")
        print("=" * 60)
        print(f"Topic: {config.debate_topic[:70]}...")
        print(f"Population: {config.total_agents} agents")
        print(f"  - Contrarians: {config.num_contrarians}")
        print(f"  - Consensus: {config.num_consensus}")
        print(f"  - Neutrals: {config.num_neutrals}")
        print(f"Duration: {config.num_rounds} rounds")
        print(f"Model: {config.model}")
        print("=" * 60)
        print()

    engine = SimulationEngine(config, api_key)
    tracker = engine.run_simulation(verbose=verbose)

    # Generate timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Save transcript
    transcript_path = f"{output_dir}/debate_transcript_{timestamp}.txt"
    tracker.save_transcript(transcript_path)
    if verbose:
        print(f"\nTranscript saved: {transcript_path}")

    # Save data export
    data_path = f"{output_dir}/simulation_data_{timestamp}.json"
    tracker.save_data(data_path)
    if verbose:
        print(f"Data export saved: {data_path}")

    # Generate visualizations
    viz_files = save_all_visualizations(tracker, output_dir, timestamp)
    if verbose:
        print(f"Visualizations saved: {len(viz_files)} files")
        for f in viz_files:
            print(f"  - {f}")

    # Analyze amplification bias
    bias_analysis = engine.get_amplification_analysis()

    # Build summary
    initial = tracker.round_summaries[0].opinion_distribution if tracker.round_summaries else {}
    final = tracker.round_summaries[-1].opinion_distribution if tracker.round_summaries else {}

    to_contrarian = sum(1 for e in tracker.conversion_events if e.direction == "to_contrarian")
    to_consensus = sum(1 for e in tracker.conversion_events if e.direction == "to_consensus")

    summary = {
        "timestamp": timestamp,
        "config": {
            "num_agents": config.total_agents,
            "num_rounds": config.num_rounds,
            "debate_topic": config.debate_topic
        },
        "results": {
            "initial_distribution": initial,
            "final_distribution": final,
            "conversions": {
                "total": len(tracker.conversion_events),
                "to_contrarian": to_contrarian,
                "to_consensus": to_consensus
            },
            "opinion_shift": (
                tracker.round_summaries[-1].average_opinion -
                tracker.round_summaries[0].average_opinion
            ) if tracker.round_summaries else 0
        },
        "amplification_bias": bias_analysis,
        "output_files": {
            "transcript": transcript_path,
            "data": data_path,
            "visualizations": viz_files
        }
    }

    # Print final summary
    if verbose:
        print()
        print("=" * 60)
        print("EXPERIMENT COMPLETE")
        print("=" * 60)
        print()
        print("RESULTS:")
        print(f"  Initial: {initial}")
        print(f"  Final:   {final}")
        print()
        print(f"  Opinion shift: {summary['results']['opinion_shift']:+.3f}")
        print(f"  (negative = shifted toward contrarian)")
        print()
        print(f"  Conversions:")
        print(f"    Total: {len(tracker.conversion_events)}")
        print(f"    To contrarian: {to_contrarian}")
        print(f"    To consensus: {to_consensus}")
        print()
        print(f"  Amplification bias:")
        print(f"    Contrarian avg visibility: {bias_analysis['contrarian_avg_visibility']:.3f}")
        print(f"    Consensus avg visibility: {bias_analysis['consensus_avg_visibility']:.3f}")
        print(f"    Bias ratio: {bias_analysis['bias_ratio']:.2f}")
        print(f"    Interpretation: {bias_analysis['interpretation']}")
        print()
        print("=" * 60)
        print(f"All results saved to: {output_dir}/")
        print("=" * 60)

    return summary


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Opinion Dynamics Simulation - Energy Debate"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("ANTHROPIC_API_KEY"),
        help="Anthropic API key (or set ANTHROPIC_API_KEY env var)"
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=50,
        help="Number of debate rounds (default: 50)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./results",
        help="Output directory (default: ./results)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output"
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: No API key provided.")
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key")
        return 1

    try:
        summary = run_experiment(
            api_key=args.api_key,
            num_rounds=args.rounds,
            output_dir=args.output,
            verbose=not args.quiet
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
