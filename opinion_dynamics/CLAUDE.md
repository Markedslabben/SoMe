# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LLM-based agent simulation studying how algorithmic amplification affects opinion formation in social media debates about energy policy. The simulation demonstrates how engagement-optimized visibility algorithms structurally advantage emotional/provocative content, creating feedback loops that can convert majorities toward minority positions.

**Core finding**: A single contrarian achieved 8.7x visibility advantage and converted 60% of neutrals despite being outnumbered 4:1 by consensus advocates.

## Running Simulations

```bash
# Agent-Based Model (main simulation, requires API key)
python main.py                              # Default: 50 rounds
python main.py --rounds 20                  # Short run
python main.py --output ./my_results        # Custom output dir

# Tit-for-Tat Experiment (Norwegian, tests counter-strategy)
python experiment_tit_for_tat.py            # Default: 60% reply probability
python experiment_tit_for_tat.py --rounds 30 --reply-prob 0.8

# System Dynamics Model (no API calls, differential equations)
python sd_main.py                           # Baseline simulation
python sd_main.py --policy reduced_bias     # Policy experiment
python sd_main.py --sensitivity             # Sensitivity analysis
python sd_main.py --validate                # Compare to ABM results
```

**Environment**: Set `ANTHROPIC_API_KEY` for LLM simulations.

**Dependencies**: `anthropic`, `plotly`, `python-dotenv` (optional)

## Architecture

### Two Modeling Approaches

| Model | Entry Point | Purpose |
|-------|-------------|---------|
| Agent-Based (ABM) | `main.py` | LLM agents generate posts, emergent dynamics |
| System Dynamics (SD) | `sd_main.py` | Continuous-time differential equations, policy testing |

### ABM Component Flow

```
main.py
  └─ SimulationEngine (simulation.py)
       ├─ LLMAgent (agents.py) → Claude API calls → Post generation
       ├─ ContentAnalyzer (agents.py) → Lexical analysis of posts
       ├─ AmplificationAlgorithm (amplification.py) → Feed ranking
       ├─ EmotionalEngine (emotions.py) → Arousal/anger updates
       └─ SimulationTracker (tracking.py) → Conversion detection
```

### Key Domain Models (models.py)

- `Agent`: Role (contrarian/consensus/neutral), opinion position, emotional state, memory
- `Opinion`: Position (-1 to +1), confidence, stability, position history
- `EmotionalState`: Arousal, valence, engagement, anger, anxiety
- `Post`: Content + analyzed metrics (emotional_intensity, provocativeness, visibility_score)

### Visibility Formula (The Core Mechanism)

```python
visibility = (emotion*0.4 + provocativeness*0.4 + recency*0.2) * (1 + engagement²*0.6)
```

The squared engagement multiplier creates superlinear returns for provocative content.

### Opinion Space

```
-1.0 ←──────────── 0 ────────────→ +1.0
CONTRARIAN      NEUTRAL        CONSENSUS
```
Conversion thresholds: ±0.3 (crossing these triggers a conversion event)

## Experiments

### Baseline (main.py)
- 1 contrarian, 4 consensus, 20 neutrals
- 50 rounds, 5 posts per round
- Tests algorithmic amplification without intervention

### Tit-for-Tat (experiment_tit_for_tat.py)
**Hypothesis**: Consensus advocates using confrontational replies ONLY when responding to contrarians can counteract amplification bias.
- Norwegian language prompts (`prompts_norwegian_tft.py`)
- Consensus agents switch to `CONSENSUS_CONFRONTATIONAL_REPLY_PROMPT` when replying to contrarians
- Results in `results/tit_for_tat_norwegian/`

### System Dynamics Policies (sd_analysis.py)
- `reduced_bias`: Lower visibility ratio
- `cooling_off`: Emotional decay periods
- `friction`: Response delay for high-arousal content

## Output Files

All results saved to `results/` (or custom output dir):
- `debate_transcript_TIMESTAMP.txt` - Full conversation log
- `simulation_data_TIMESTAMP.json` - Structured data export
- `dashboard_TIMESTAMP.html` - Interactive Plotly visualizations
- `sd_summary_TIMESTAMP.json` - System dynamics results

## Key Files by Purpose

| Category | Files |
|----------|-------|
| Entry points | `main.py`, `sd_main.py`, `experiment_tit_for_tat.py` |
| Core engine | `simulation.py`, `agents.py`, `amplification.py` |
| Domain models | `models.py`, `emotions.py` |
| Agent prompts | `prompts.py`, `prompts_norwegian_tft.py` |
| System dynamics | `sd_model.py`, `sd_equations.py`, `sd_parameters.py`, `sd_analysis.py` |
| Visualization | `visualization.py`, `sd_visualization.py`, `sfd_diagram.py` |
| Tracking | `tracking.py` |

## Validity Considerations

LLM agents are valid for **system-level dynamics** (visibility ratios, feedback loops) but not for **individual psychological processes** (exact conversion thresholds, emotional experience). Interpret findings as mechanisms, not magnitudes.

## Model Configuration

Default settings in `SimulationConfig` (models.py):
- Model: `claude-sonnet-4-20250514`
- Max tokens per post: 120
- Memory window: 15 posts
- Emotional decay rate: 0.12 per round

## Key References

- `algorithmic_amplification_analysis.md` - Full Pyramid Principle analysis
- Elaboration Likelihood Model (Petty & Cacioppo)
- Spiral of Silence (Noelle-Neumann)
- System 1/System 2 (Kahneman)
