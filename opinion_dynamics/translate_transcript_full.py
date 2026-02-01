"""
Fully translate debate transcript from English to Norwegian using Claude API.
Preserves format, emojis, and metadata structure.
"""

import re
import os
import anthropic
from dotenv import load_dotenv

load_dotenv()


def extract_posts(content: str) -> list:
    """Extract all posts with their metadata from transcript."""
    # Pattern to match posts: [AgentID-Name] (metadata): "content"
    pattern = r'(\[[^\]]+\] \([^)]+\):\s*\n)"([^"]+)"(\s*\n>> [^\n]+)'

    matches = []
    for match in re.finditer(pattern, content, re.DOTALL):
        matches.append({
            'full_match': match.group(0),
            'prefix': match.group(1),
            'content': match.group(2),
            'suffix': match.group(3),
            'start': match.start(),
            'end': match.end()
        })
    return matches


def translate_batch(client, texts: list[str], batch_size: int = 10) -> list[str]:
    """Translate a batch of texts to Norwegian."""

    # Format texts for translation
    numbered_texts = "\n\n".join([f"[{i+1}] {text}" for i, text in enumerate(texts)])

    prompt = f"""Translate the following social media posts from English to Norwegian.
Keep ALL emojis exactly as they are. Maintain the same tone and style.
Return ONLY the translations, numbered to match the input.

{numbered_texts}

Return format:
[1] <Norwegian translation>
[2] <Norwegian translation>
...etc"""

    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = response.content[0].text

    # Parse numbered translations
    translations = []
    for i in range(len(texts)):
        pattern = rf'\[{i+1}\]\s*(.+?)(?=\n\[{i+2}\]|\Z)'
        match = re.search(pattern, response_text, re.DOTALL)
        if match:
            translations.append(match.group(1).strip())
        else:
            # Fallback: keep original if parsing fails
            translations.append(texts[i])

    return translations


def translate_transcript(input_path: str, output_path: str, batch_size: int = 15):
    """Translate entire transcript to Norwegian."""

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not found in environment")

    client = anthropic.Anthropic(api_key=api_key)

    # Read input
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Translate structure first
    structure_translations = {
        "ENERGY DEBATE SIMULATION - FULL TRANSCRIPT": "ENERGIDEBATT-SIMULERING - FULLSTENDIG TRANSKRIPSJON",
        "Generated:": "Generert:",
        "Total Rounds:": "Totalt antall runder:",
        "Total Posts:": "Totalt antall innlegg:",
        "Conversion Events:": "Konverteringshendelser:",
        "ROUND": "RUNDE",
        "Opinion Distribution:": "Meningsfordeling:",
        "Contrarian": "Kontrær",
        "Neutral": "Nøytral",
        "Consensus": "Konsensus",
        "Avg Opinion:": "Gj.sn. standpunkt:",
        "Avg Arousal:": "Gj.sn. emo.mobilisering:",
        "Avg Anger:": "Gj.sn. sinne:",
        "arousal": "emo.mobilisering",
        "opinion": "standpunkt",
        "visibility": "synlighet",
        "confrontation": "konfrontasjon",
        "SIMULATION COMPLETE": "SIMULERING FULLFØRT",
        "INITIAL DISTRIBUTION:": "STARTFORDELING:",
        "FINAL DISTRIBUTION:": "SLUTTFORDELING:",
        "CHANGES:": "ENDRINGER:",
        "Total Conversions:": "Totale konverteringer:",
        "To Contrarian:": "Til kontrær:",
        "To Consensus:": "Til konsensus:",
    }

    result = content
    for eng, nor in structure_translations.items():
        result = result.replace(eng, nor)

    # Agent name translations
    agent_translations = {
        "Expert": "Ekspert", "Researcher": "Forsker", "Analyst": "Analytiker",
        "Pragmatist": "Pragmatiker", "Skeptic": "Skeptiker", "Engineer": "Ingeniør",
        "Worried": "Bekymret", "Frustrated": "Frustrert", "Anxious": "Engstelig",
        "Outraged": "Opprørt", "Follower": "Følger", "Agreeable": "Medgjørlig",
        "Moderate": "Moderat", "Mainstream": "Mainstream", "Casual": "Tilfeldig",
        "Busy": "Opptatt", "Lurker": "Lurker", "Passive": "Passiv",
        "Curious": "Nysgjerrig", "OpenMinded": "Åpen", "Thoughtful": "Ettertenksom",
        "Undecided": "Ubestemt",
    }

    for eng, nor in agent_translations.items():
        result = re.sub(rf'\[([A-Z]\d+)-{eng}\]', rf'[\1-{nor}]', result)

    # Extract posts for content translation
    posts = extract_posts(result)
    print(f"Found {len(posts)} posts to translate")

    # Translate in batches
    all_contents = [p['content'] for p in posts]
    translated_contents = []

    for i in range(0, len(all_contents), batch_size):
        batch = all_contents[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(all_contents) + batch_size - 1) // batch_size
        print(f"Translating batch {batch_num}/{total_batches} ({len(batch)} posts)...")

        translated = translate_batch(client, batch, batch_size)
        translated_contents.extend(translated)

    # Replace content in reverse order to preserve positions
    for i, post in enumerate(reversed(posts)):
        idx = len(posts) - 1 - i
        old_text = f'"{post["content"]}"'
        new_text = f'"{translated_contents[idx]}"'
        result = result[:post['start']] + result[post['start']:post['end']].replace(old_text, new_text, 1) + result[post['end']:]

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"\nTranslated transcript saved to: {output_path}")
    print(f"Total posts translated: {len(posts)}")


if __name__ == "__main__":
    input_file = "results/sim_20260201_145320/debate_transcript.txt"
    output_file = "results/sim_20260201_145320/debate_transcript_norsk.txt"
    translate_transcript(input_file, output_file)
