"""
Entry point for the Opinion Dynamics Simulation.

Usage:
    python main.py                          # Run with defaults
    python main.py --rounds 20              # Short run
    python main.py --output ./my_results    # Custom output dir
    python main.py --api-key sk-xxx         # Explicit API key
    python main.py --interactive            # Interactive mode to configure options
    python main.py --language no            # Norwegian language
"""

import os
import argparse
from datetime import datetime

from models import SimulationConfig
from simulation import SimulationEngine
from visualization import save_all_visualizations
from amplification import analyze_amplification_bias


def generate_experiment_summary(
    config: SimulationConfig,
    tracker,
    bias_analysis: dict,
    sim_dir: str,
    timestamp: str
) -> str:
    """
    Generate a human-readable experiment summary file.

    Args:
        config: Simulation configuration
        tracker: SimulationTracker with results
        bias_analysis: Amplification bias analysis
        sim_dir: Output directory
        timestamp: Simulation timestamp

    Returns:
        Path to the generated summary file
    """
    # Calculate results
    initial = tracker.round_summaries[0].opinion_distribution if tracker.round_summaries else {}
    final = tracker.round_summaries[-1].opinion_distribution if tracker.round_summaries else {}

    to_contrarian = sum(1 for e in tracker.conversion_events if e.direction == "to_contrarian")
    to_consensus = sum(1 for e in tracker.conversion_events if e.direction == "to_consensus")

    opinion_shift = (
        tracker.round_summaries[-1].average_opinion -
        tracker.round_summaries[0].average_opinion
    ) if tracker.round_summaries else 0

    # Build summary text
    lines = [
        "=" * 70,
        "EXPERIMENT SUMMARY / EKSPERIMENTOPPSUMMERING",
        "=" * 70,
        "",
        f"Timestamp: {timestamp}",
        f"Generated: {datetime.now().isoformat()}",
        "",
        "-" * 70,
        "CONFIGURATION / KONFIGURASJON",
        "-" * 70,
        "",
        "Population / Populasjon:",
        f"  Total agents / Totalt agenter: {config.total_agents}",
        f"  Contrarians / Kontrære: {config.num_contrarians}",
        f"  Consensus advocates / Konsensusadvokater: {config.num_consensus}",
        f"  Neutral observers / Nøytrale observatører: {config.num_neutrals}",
        "",
        "Simulation parameters / Simuleringsparametere:",
        f"  Rounds / Runder: {config.num_rounds}",
        f"  Posts per round / Innlegg per runde: {config.posts_per_round}",
        f"  Memory window / Minnevindu: {config.memory_window}",
        f"  Emotional decay rate / Emosjonell nedbrytningsrate: {config.emotional_decay_rate}",
        "",
        "Model settings / Modellinnstillinger:",
        f"  LLM Model: {config.model}",
        f"  Max tokens per post: {config.max_tokens_per_response}",
        f"  Language / Språk: {'Norwegian / Norsk' if config.language == 'no' else 'English / Engelsk'}",
        "",
        "Amplification weights / Forsterkningsvekter:",
        f"  Emotion weight / Emosjonsvekt: {config.emotion_weight}",
        f"  Provocative weight / Provokasjonsvekt: {config.provocative_weight}",
        f"  Recency weight / Aktualitetsvekt: {config.recency_weight}",
        "",
        "Optional mechanisms / Valgfrie mekanismer:",
        f"  Spiral of Silence / Taushetsspiralen: {'ENABLED / AKTIVERT' if config.enable_spiral_of_silence else 'DISABLED / DEAKTIVERT'}",
        "",
        "Debate topic / Debattema:",
        f"  {config.debate_topic}",
        "",
        "-" * 70,
        "RESULTS / RESULTATER",
        "-" * 70,
        "",
        "Opinion distribution / Meningsfordeling:",
        f"  Initial / Start: Contrarian={initial.get('contrarian', 0)}, Neutral={initial.get('neutral', 0)}, Consensus={initial.get('consensus', 0)}",
        f"  Final / Slutt:   Contrarian={final.get('contrarian', 0)}, Neutral={final.get('neutral', 0)}, Consensus={final.get('consensus', 0)}",
        "",
        f"Opinion shift / Meningsforskyvning: {opinion_shift:+.3f}",
        f"  (negative = shifted toward contrarian / negativ = forskjøvet mot kontrær)",
        "",
        "Conversions / Konverteringer:",
        f"  Total: {len(tracker.conversion_events)}",
        f"  To contrarian / Til kontrær: {to_contrarian}",
        f"  To consensus / Til konsensus: {to_consensus}",
        "",
        "Amplification bias / Forsterkningsskjevhet:",
        f"  Contrarian avg visibility / Kontrær gj.sn. synlighet: {bias_analysis['contrarian_avg_visibility']:.3f}",
        f"  Consensus avg visibility / Konsensus gj.sn. synlighet: {bias_analysis['consensus_avg_visibility']:.3f}",
        f"  Bias ratio / Skjevhetsforhold: {bias_analysis['bias_ratio']:.2f}x",
        f"  Interpretation / Tolkning: {bias_analysis['interpretation']}",
        "",
        "-" * 70,
        "INTERPRETATION / TOLKNING",
        "-" * 70,
        "",
    ]

    # Add interpretation based on results
    if to_contrarian > to_consensus:
        lines.append("The contrarian position gained ground despite being outnumbered.")
        lines.append("Den kontrære posisjonen vant terreng til tross for å være i mindretall.")
    elif to_consensus > to_contrarian:
        lines.append("The consensus position maintained or expanded its majority.")
        lines.append("Konsensusposisjonen opprettholdt eller utvidet sitt flertall.")
    else:
        lines.append("Neither position gained significant advantage.")
        lines.append("Ingen posisjon fikk betydelig fordel.")

    lines.append("")

    if bias_analysis['bias_ratio'] > 2.0:
        lines.append(f"Strong algorithmic amplification bias ({bias_analysis['bias_ratio']:.1f}x) favoring contrarian content.")
        lines.append(f"Sterk algoritmisk forsterkningsskjevhet ({bias_analysis['bias_ratio']:.1f}x) som favoriserer kontrært innhold.")
    elif bias_analysis['bias_ratio'] > 1.5:
        lines.append(f"Moderate amplification bias ({bias_analysis['bias_ratio']:.1f}x) favoring contrarian content.")
        lines.append(f"Moderat forsterkningsskjevhet ({bias_analysis['bias_ratio']:.1f}x) som favoriserer kontrært innhold.")
    else:
        lines.append(f"Low amplification bias ({bias_analysis['bias_ratio']:.1f}x) - relatively balanced visibility.")
        lines.append(f"Lav forsterkningsskjevhet ({bias_analysis['bias_ratio']:.1f}x) - relativt balansert synlighet.")

    lines.extend([
        "",
        "-" * 70,
        "OUTPUT FILES / UTDATAFILER",
        "-" * 70,
        "",
        f"  debate_transcript.txt - Full conversation log / Fullstendig samtalelogg",
        f"  simulation_data.json - Structured data export / Strukturert dataeksport",
        f"  opinion_trajectories.html - Opinion evolution plot / Meningsutvikling",
        f"  emotional_heatmap.html - Emotional intensity over time / Emosjonell intensitet",
        f"  confrontation_trajectories.html - Confrontation levels / Konfrontasjonsnivåer",
        f"  visibility_comparison.html - Amplification analysis / Forsterkningsanalyse",
        f"  conversion_timeline.html - Conversion events / Konverteringshendelser",
        f"  dashboard.html - Combined dashboard / Kombinert dashbord",
        "",
        "=" * 70,
    ])

    # Write summary file
    summary_path = f"{sim_dir}/experiment_summary.txt"
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return summary_path


def prompt_for_options() -> dict:
    """
    Interactive prompt for simulation options.

    Returns:
        dict with user-selected options
    """
    print()
    print("=" * 60)
    print("SIMULATION OPTIONS")
    print("=" * 60)
    print()

    # Language selection
    print("Language / Språk:")
    print("  1. English (default)")
    print("  2. Norsk")
    print()
    lang_choice = input("Select [1/2]: ").strip()
    language = "no" if lang_choice == "2" else "en"

    print()

    # Spiral of Silence
    print("Spiral of Silence mechanism:")
    print("  (Agents may withdraw when perceiving minority status)")
    print("  1. Disabled (default)")
    print("  2. Enabled")
    print()
    sos_choice = input("Select [1/2]: ").strip()
    enable_spiral_of_silence = sos_choice == "2"

    print()
    print("-" * 60)
    print(f"Selected: Language={'Norwegian' if language == 'no' else 'English'}, "
          f"Spiral of Silence={'Enabled' if enable_spiral_of_silence else 'Disabled'}")
    print("-" * 60)
    print()

    return {
        "language": language,
        "enable_spiral_of_silence": enable_spiral_of_silence
    }


def run_experiment(
    api_key: str,
    num_rounds: int = 100,
    output_dir: str = "./results",
    verbose: bool = True,
    enable_spiral_of_silence: bool = False,
    language: str = "en"
) -> dict:
    """
    Run the complete opinion dynamics experiment.

    Args:
        api_key: Anthropic API key
        num_rounds: Number of debate rounds
        output_dir: Directory to save results
        verbose: Print progress
        enable_spiral_of_silence: Enable Spiral of Silence mechanism
        language: Language code - "en" for English, "no" for Norwegian

    Returns:
        Summary statistics dictionary
    """
    # Select debate topic based on language
    if language == "no":
        debate_topic = (
            "Energiomstillingen: Bør vi primært satse på fornybar energi, kjernekraft, "
            "eller en kombinasjon? Hvordan bør strømmarkedet være strukturert? "
            "Er dagens strømpriser og energiavgifter for forbrukere rettferdige?"
        )
    else:
        debate_topic = (
            "The Energy Transition: Should we rely primarily on renewables, nuclear, "
            "or a mix? How should the electricity market be structured? "
            "Are current consumer electricity prices and energy taxes justified?"
        )

    # Configuration
    config = SimulationConfig(
        num_contrarians=1,
        num_consensus=4,
        num_neutrals=20,
        num_rounds=num_rounds,
        posts_per_round=6,
        debate_topic=debate_topic,
        model="claude-sonnet-4-20250514",
        max_tokens_per_response=80,  # ~280 characters, tweet-length
        enable_spiral_of_silence=enable_spiral_of_silence,
        language=language
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
        print(f"Language: {'Norwegian' if config.language == 'no' else 'English'}")
        if config.enable_spiral_of_silence:
            print("Spiral of Silence: ENABLED")
        print("=" * 60)
        print()

    engine = SimulationEngine(config, api_key)
    tracker = engine.run_simulation(verbose=verbose)

    # Generate timestamp and create simulation-specific folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    sim_dir = f"{output_dir}/sim_{timestamp}"
    os.makedirs(sim_dir, exist_ok=True)

    # Save transcript
    transcript_path = f"{sim_dir}/debate_transcript.txt"
    tracker.save_transcript(transcript_path)
    if verbose:
        print(f"\nTranscript saved: {transcript_path}")

    # Save data export
    data_path = f"{sim_dir}/simulation_data.json"
    tracker.save_data(data_path)
    if verbose:
        print(f"Data export saved: {data_path}")

    # Generate visualizations (no timestamp in filenames since folder is unique)
    viz_files = save_all_visualizations(tracker, sim_dir, "")
    if verbose:
        print(f"Visualizations saved: {len(viz_files)} files")
        for f in viz_files:
            print(f"  - {f}")

    # Analyze amplification bias
    bias_analysis = engine.get_amplification_analysis()

    # Generate experiment summary file
    summary_file_path = generate_experiment_summary(
        config, tracker, bias_analysis, sim_dir, timestamp
    )
    if verbose:
        print(f"Experiment summary saved: {summary_file_path}")

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
            "debate_topic": config.debate_topic,
            "language": config.language,
            "spiral_of_silence": config.enable_spiral_of_silence
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
            "summary": summary_file_path,
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
        print(f"All results saved to: {sim_dir}/")
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
        default=100,
        help="Number of debate rounds (default: 100)"
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
    parser.add_argument(
        "--spiral-of-silence",
        action="store_true",
        help="Enable Spiral of Silence mechanism (agents withdraw when perceiving minority status)"
    )
    parser.add_argument(
        "--language",
        type=str,
        choices=["en", "no"],
        default="en",
        help="Language for simulation: 'en' (English) or 'no' (Norwegian). Default: en"
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Interactive mode: prompt for options before starting"
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: No API key provided.")
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key")
        return 1

    # Get options - either from interactive prompt or CLI args
    if args.interactive:
        options = prompt_for_options()
        language = options["language"]
        enable_spiral_of_silence = options["enable_spiral_of_silence"]
    else:
        language = args.language
        enable_spiral_of_silence = args.spiral_of_silence

    try:
        summary = run_experiment(
            api_key=args.api_key,
            num_rounds=args.rounds,
            output_dir=args.output,
            verbose=not args.quiet,
            enable_spiral_of_silence=enable_spiral_of_silence,
            language=language
        )
        return 0
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
