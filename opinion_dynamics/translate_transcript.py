"""
Translate debate transcript from English to Norwegian while preserving format.
"""

import re

def translate_transcript(input_path: str, output_path: str):
    """Translate transcript to Norwegian while preserving structure and emojis."""

    # Read input file
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Translation mappings for structure
    translations = {
        # Header
        "ENERGY DEBATE SIMULATION - FULL TRANSCRIPT": "ENERGIDEBATT-SIMULERING - FULLSTENDIG TRANSKRIPSJON",
        "Generated:": "Generert:",
        "Total Rounds:": "Totalt antall runder:",
        "Total Posts:": "Totalt antall innlegg:",
        "Conversion Events:": "Konverteringshendelser:",

        # Round headers
        "ROUND": "RUNDE",
        "Opinion Distribution:": "Meningsfordeling:",
        "Contrarian": "Kontrær",
        "Neutral": "Nøytral",
        "Consensus": "Konsensus",
        "Avg Opinion:": "Gj.sn. standpunkt:",
        "Avg Arousal:": "Gj.sn. emo.mobilisering:",
        "Avg Anger:": "Gj.sn. sinne:",

        # Post metadata
        "arousal": "emo.mobilisering",
        "opinion": "standpunkt",
        "visibility": "synlighet",
        "confrontation": "konfrontasjon",

        # Conversion events
        "CONVERSION": "KONVERTERING",
        "to_contrarian": "til_kontrær",
        "to_consensus": "til_konsensus",
        "trigger:": "utløst av:",

        # Final summary
        "SIMULATION COMPLETE": "SIMULERING FULLFØRT",
        "INITIAL DISTRIBUTION:": "STARTFORDELING:",
        "FINAL DISTRIBUTION:": "SLUTTFORDELING:",
        "CHANGES:": "ENDRINGER:",
        "Total Conversions:": "Totale konverteringer:",
        "To Contrarian:": "Til kontrær:",
        "To Consensus:": "Til konsensus:",
    }

    # Agent role translations
    agent_translations = {
        "Contrarian": "Kontrær",
        "Expert": "Ekspert",
        "Researcher": "Forsker",
        "Analyst": "Analytiker",
        "Pragmatist": "Pragmatiker",
        "Skeptic": "Skeptiker",
        "Engineer": "Ingeniør",
        "Worried": "Bekymret",
        "Frustrated": "Frustrert",
        "Anxious": "Engstelig",
        "Outraged": "Opprørt",
        "Follower": "Følger",
        "Agreeable": "Medgjørlig",
        "Moderate": "Moderat",
        "Mainstream": "Mainstream",
        "Casual": "Tilfeldig",
        "Busy": "Opptatt",
        "Lurker": "Lurker",
        "Passive": "Passiv",
        "Curious": "Nysgjerrig",
        "OpenMinded": "Åpen",
        "Thoughtful": "Ettertenksom",
        "Undecided": "Ubestemt",
    }

    # Apply structure translations
    result = content
    for eng, nor in translations.items():
        result = result.replace(eng, nor)

    # Translate agent names in brackets [X-Name]
    for eng, nor in agent_translations.items():
        # Pattern: [ID-Name] where Name matches
        result = re.sub(
            rf'\[([A-Z]\d+)-{eng}\]',
            rf'[\1-{nor}]',
            result
        )

    # Write output file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"Translated transcript saved to: {output_path}")


if __name__ == "__main__":
    input_file = "results/sim_20260201_145320/debate_transcript.txt"
    output_file = "results/sim_20260201_145320/debate_transcript_norsk.txt"
    translate_transcript(input_file, output_file)
