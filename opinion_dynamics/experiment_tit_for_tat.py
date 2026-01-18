"""
Tit-for-Tat Experiment: Norwegian Energy Debate

Tests the hypothesis that consensus advocates using confrontational replies
ONLY when responding to contrarians can counteract algorithmic amplification bias.

Key differences from baseline:
1. All discourse in Norwegian
2. Consensus advocates use CONSENSUS_CONFRONTATIONAL_REPLY_PROMPT_NO when replying to contrarians
3. Results saved to separate folder: results/tit_for_tat_norwegian/
"""

import os
import random
from datetime import datetime
from typing import List, Optional, Tuple

# Load .env file if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on environment

import anthropic

from models import (
    Agent, AgentRole, Opinion, EmotionalState, Post,
    SimulationConfig, ConversionEvent, BehaviorMetrics
)
from agents import ContentAnalyzer
from emotions import EmotionalEngine, calculate_response_probability
from amplification import AmplificationAlgorithm, compute_opinion_influence
from tracking import SimulationTracker, detect_conversion, RoundSummary
from visualization import save_all_visualizations

from prompts_norwegian_tft import (
    get_system_prompt_no,
    format_prompt_no,
    CONSENSUS_CONFRONTATIONAL_REPLY_PROMPT_NO
)


# =============================================================================
# EXPERIMENT CONFIGURATION
# =============================================================================

EXPERIMENT_NAME = "tit_for_tat_norwegian"
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results", EXPERIMENT_NAME)


from dataclasses import dataclass, field


@dataclass
class TitForTatConfig:
    """Config for the tit-for-tat experiment."""

    # Population distribution
    num_contrarians: int = 1
    num_consensus: int = 4
    num_neutrals: int = 20

    # Simulation parameters
    num_rounds: int = 50
    posts_per_round: int = 5

    # Amplification weights
    emotion_weight: float = 0.4
    provocative_weight: float = 0.4
    recency_weight: float = 0.2

    # Agent behavior
    memory_window: int = 15
    emotional_decay_rate: float = 0.12

    # API settings
    model: str = "claude-sonnet-4-20250514"
    max_tokens_per_response: int = 120

    # Tit-for-tat specific
    reply_to_contrarian_probability: float = 0.6

    # Norwegian debate topic
    debate_topic: str = (
        "Energiomstillingen i Norge: Fornybar energi, kjernekraft, strømmarkedet, "
        "utenlandskabler, forbrukerpriser og avgifter. "
        "Er utenlandskablene til UK og Tyskland bra eller dårlig for norske forbrukere? "
        "Burde vi satse mer på kjernekraft? Er strømprisene rettferdige?"
    )

    @property
    def total_agents(self) -> int:
        return self.num_contrarians + self.num_consensus + self.num_neutrals


# =============================================================================
# MODIFIED LLM AGENT WITH TIT-FOR-TAT SUPPORT
# =============================================================================

class TitForTatLLMAgent:
    """
    LLM Agent that supports tit-for-tat replies for consensus advocates.

    When a consensus advocate is selected to speak and there's a recent
    contrarian post, they have a chance to reply directly with a
    confrontational tone.
    """

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        self.analyzer = ContentAnalyzer()

    def generate_post(
        self,
        agent: Agent,
        topic: str,
        max_tokens: int = 120,
        reply_to_post: Optional[Post] = None,
        is_tit_for_tat: bool = False
    ) -> Post:
        """
        Generate a post, optionally as a tit-for-tat reply.

        Args:
            agent: The agent generating the post
            topic: Debate topic (not used directly, topic is in prompts)
            max_tokens: Max tokens for response
            reply_to_post: If set, this is a reply to that post
            is_tit_for_tat: If True, use confrontational reply prompt

        Returns:
            Post object with content and metrics
        """
        # Determine which prompt to use
        is_reply_to_contrarian = (
            is_tit_for_tat and
            agent.role == AgentRole.CONSENSUS_ADVOCATE and
            reply_to_post is not None
        )

        template = get_system_prompt_no(agent.role.name, is_reply_to_contrarian)

        # Format with current state
        emotion_desc = agent.emotional_state.to_description()
        opinion_desc = (
            agent.opinion.to_description()
            if agent.role == AgentRole.NEUTRAL_OBSERVER
            else ""
        )

        # For tit-for-tat replies, include the contrarian post content
        reply_content = reply_to_post.content if reply_to_post else ""

        system_prompt = format_prompt_no(
            template,
            emotion_description=emotion_desc,
            memory=agent.memory,
            opinion_description=opinion_desc,
            reply_to_content=reply_content
        )

        # Call Claude API
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": "Skriv ditt innlegg nå."}]
            )
            content = response.content[0].text.strip()
            content = content.strip('"\'')

        except Exception as e:
            content = f"[API Error: {str(e)[:50]}]"
            print(f"Warning: API call failed for agent {agent.id}: {e}")

        # Analyze content
        metrics = self.analyzer.analyze(content)

        # Create post
        post = Post(
            author_id=agent.id,
            author_name=agent.name,
            content=content,
            emotional_intensity=metrics['emotional_intensity'],
            provocativeness=metrics['provocativeness'],
            logical_coherence=metrics['logical_coherence'],
            consensus_orientation=metrics['consensus_orientation'],
            author_arousal=agent.emotional_state.arousal,
            author_opinion=agent.opinion.position,
            reply_to=reply_to_post.id if reply_to_post else None
        )

        # Record behavioral metrics
        agent.behavior_metrics.record_post(
            confrontation=metrics['provocativeness'],
            consensus_orient=metrics['consensus_orientation'],
            is_reply=(reply_to_post is not None)
        )

        return post


# =============================================================================
# MODIFIED SIMULATION ENGINE
# =============================================================================

class TitForTatSimulation:
    """
    Simulation engine with tit-for-tat reply mechanics.

    When consensus advocates speak, they check if there's a recent
    contrarian post to reply to. If so, they use the confrontational
    reply prompt.
    """

    def __init__(self, config: TitForTatConfig, api_key: str):
        self.config = config
        self.llm = TitForTatLLMAgent(api_key, config.model)
        self.amplifier = AmplificationAlgorithm(config)
        self.emotion_engine = EmotionalEngine()
        self.tracker = SimulationTracker()

        self.agents: List[Agent] = []
        self.all_posts: List[Post] = []

        # Track contrarian posts for reply targeting
        self.recent_contrarian_posts: List[Post] = []

    def initialize_population(self) -> None:
        """Create the agent population with Norwegian names."""
        agent_id = 0

        # Contrarian (1)
        for i in range(self.config.num_contrarians):
            self.agents.append(Agent(
                id=f"K{agent_id}",  # K for Kontrær
                role=AgentRole.CONTRARIAN_PROVOCATEUR,
                name="Skeptiker",
                opinion=Opinion(position=-0.85, confidence=0.9, stability=0.8),
                emotional_state=EmotionalState(
                    arousal=0.7, valence=-0.2, engagement=0.85, anger=0.3, anxiety=0.1
                ),
                behavior_metrics=BehaviorMetrics()
            ))
            agent_id += 1

        # Consensus advocates (4) with Norwegian names
        consensus_names = ["Forsker", "Analytiker", "Rådgiver", "Fagekspert"]
        for i in range(self.config.num_consensus):
            name = consensus_names[i] if i < len(consensus_names) else f"Ekspert_{i}"
            self.agents.append(Agent(
                id=f"E{agent_id}",  # E for Ekspert
                role=AgentRole.CONSENSUS_ADVOCATE,
                name=name,
                opinion=Opinion(
                    position=0.7 + random.uniform(-0.1, 0.1),
                    confidence=0.7,
                    stability=0.6
                ),
                emotional_state=EmotionalState(
                    arousal=0.5, valence=0.1, engagement=0.6, anger=0.1, anxiety=0.2
                ),
                behavior_metrics=BehaviorMetrics()
            ))
            agent_id += 1

        # Neutral observers (20) with Norwegian names
        neutral_names = [
            "Borger", "Velger", "Forbruker", "Forelder", "Arbeider",
            "Student", "Pensjonist", "Huseier", "Leietaker", "Bilist",
            "Pendler", "Skatteyter", "Tvileren", "Nysgjerrig", "Observatør",
            "Lytter", "Leser", "Spørrer", "Usikker", "Nykommer"
        ]
        for i in range(self.config.num_neutrals):
            name = neutral_names[i] if i < len(neutral_names) else f"Nøytral_{i}"
            self.agents.append(Agent(
                id=f"N{agent_id}",
                role=AgentRole.NEUTRAL_OBSERVER,
                name=name,
                opinion=Opinion(
                    position=random.uniform(-0.2, 0.2),
                    confidence=0.3,
                    stability=0.2
                ),
                emotional_state=EmotionalState(
                    arousal=0.4, valence=0.0, engagement=0.4, anger=0.0, anxiety=0.4
                ),
                behavior_metrics=BehaviorMetrics()
            ))
            agent_id += 1

        # Initialize trust scores
        for agent in self.agents:
            for other in self.agents:
                if other.id != agent.id:
                    base_trust = 0.5
                    if agent.role == other.role:
                        base_trust = 0.6
                    if (agent.role == AgentRole.CONSENSUS_ADVOCATE and
                        other.role == AgentRole.CONTRARIAN_PROVOCATEUR):
                        base_trust = 0.35
                    if agent.role == AgentRole.NEUTRAL_OBSERVER:
                        base_trust = 0.5
                    agent.trust_scores[other.id] = base_trust

        # Record initial positions
        for agent in self.agents:
            agent.opinion.position_history.append(agent.opinion.position)

        print(f"Initialized {len(self.agents)} agents (Norwegian):")
        print(f"  - {self.config.num_contrarians} Kontrær(e)")
        print(f"  - {self.config.num_consensus} Konsensus-forkjempere (TIT-FOR-TAT enabled)")
        print(f"  - {self.config.num_neutrals} Nøytrale observatører")

    def get_recent_contrarian_post(self) -> Optional[Post]:
        """Get most recent contrarian post for reply targeting."""
        if not self.recent_contrarian_posts:
            return None
        return self.recent_contrarian_posts[-1]

    def select_speakers(self, round_num: int) -> List[Tuple[Agent, Optional[Post], bool]]:
        """
        Select speakers and determine if they should do tit-for-tat replies.

        Returns:
            List of (agent, reply_to_post, is_tit_for_tat) tuples
        """
        # Calculate posting probabilities
        probabilities = []
        for agent in self.agents:
            prob = calculate_response_probability(agent, base_rate=0.2)
            probabilities.append(prob)

        total = sum(probabilities)
        weights = [p / total for p in probabilities]

        # Select speakers
        speakers = random.choices(self.agents, weights=weights, k=self.config.posts_per_round)

        # Ensure contrarian speaks regularly
        contrarians = [a for a in self.agents if a.role == AgentRole.CONTRARIAN_PROVOCATEUR]
        if contrarians and round_num % 3 == 0:
            if contrarians[0] not in speakers:
                speakers[0] = contrarians[0]

        # Remove duplicates
        seen = set()
        unique_speakers = []
        for speaker in speakers:
            if speaker.id not in seen:
                seen.add(speaker.id)
                unique_speakers.append(speaker)

        # Determine reply context for each speaker
        result = []
        recent_contrarian = self.get_recent_contrarian_post()

        for speaker in unique_speakers:
            if (speaker.role == AgentRole.CONSENSUS_ADVOCATE and
                recent_contrarian is not None and
                random.random() < self.config.reply_to_contrarian_probability):
                # Tit-for-tat reply
                result.append((speaker, recent_contrarian, True))
            else:
                # Normal post
                result.append((speaker, None, False))

        return result

    def run_round(self, round_num: int) -> RoundSummary:
        """Execute a single round with tit-for-tat mechanics."""

        # Select speakers with reply context
        speaker_configs = self.select_speakers(round_num)

        # Generate posts
        round_posts = []
        for agent, reply_to, is_tft in speaker_configs:
            post = self.llm.generate_post(
                agent,
                self.config.debate_topic,
                self.config.max_tokens_per_response,
                reply_to_post=reply_to,
                is_tit_for_tat=is_tft
            )
            post.round_num = round_num
            round_posts.append(post)
            agent.posts_made.append(post.id)

            # Track contrarian posts for future replies
            if agent.role == AgentRole.CONTRARIAN_PROVOCATEUR:
                self.recent_contrarian_posts.append(post)
                # Keep only last 5 for reply targeting
                if len(self.recent_contrarian_posts) > 5:
                    self.recent_contrarian_posts.pop(0)

            # Log tit-for-tat replies
            if is_tft:
                print(f"  [TIT-FOR-TAT] {agent.name} replies to contrarian")

        self.all_posts.extend(round_posts)

        # Rank and sample visible posts
        visible_posts = self.amplifier.sample_visible_posts(
            self.all_posts, round_num, sample_size=10
        )

        # Distribute to agents and update states
        round_conversions: List[ConversionEvent] = []
        last_influential_post: Optional[Post] = None

        for agent in self.agents:
            for post in visible_posts:
                if post.author_id == agent.id:
                    continue

                agent.remember_post(post, self.config.memory_window)

                impact, _ = self.emotion_engine.process_post_for_reader(post, agent)
                self.emotion_engine.apply_impact(agent, impact, post.author_id)

                if agent.role == AgentRole.NEUTRAL_OBSERVER:
                    influence_dir, influence_str, is_contrarian = compute_opinion_influence(
                        post, agent.opinion.position, agent.get_trust(post.author_id)
                    )
                    delta = agent.opinion.update(
                        influence=influence_dir * influence_str,
                        source_trust=agent.get_trust(post.author_id),
                        emotional_impact=post.emotional_intensity,
                        is_contrarian_source=is_contrarian
                    )
                    if abs(delta) > 0.05:
                        last_influential_post = post

                    conversion = detect_conversion(agent, round_num, last_influential_post)
                    if conversion:
                        round_conversions.append(conversion)
                        print(f"  KONVERTERING: {agent.name} -> {conversion.direction}")

        # Decay emotions
        for agent in self.agents:
            agent.emotional_state.decay(self.config.emotional_decay_rate)

        # Record round
        summary = self.tracker.record_round(
            round_num, round_posts, self.agents, round_conversions
        )

        return summary

    def run_simulation(self, verbose: bool = True) -> SimulationTracker:
        """Run the complete tit-for-tat experiment."""

        # Ensure results directory exists
        os.makedirs(RESULTS_DIR, exist_ok=True)

        self.initialize_population()

        if verbose:
            print(f"\n{'='*60}")
            print(f"TIT-FOR-TAT EXPERIMENT: Norwegian Energy Debate")
            print(f"{'='*60}")
            print(f"Hypotese: Konfronterende svar på kontrære innlegg kan motvirke")
            print(f"          algoritmisk forsterkning av minoritetsposisjoner.")
            print(f"\nKonfigurasjon:")
            print(f"  - Svar-til-kontrær sannsynlighet: {self.config.reply_to_contrarian_probability}")
            print(f"  - Runder: {self.config.num_rounds}")
            print(f"  - Innlegg per runde: {self.config.posts_per_round}")
            print(f"\nResultater lagres i: {RESULTS_DIR}")
            print(f"{'='*60}\n")

        # Record initial state
        initial_dist = self._count_opinions()
        if verbose:
            print(f"Startfordeling: {initial_dist}")
            print("-" * 50)

        # Run rounds
        for round_num in range(1, self.config.num_rounds + 1):
            summary = self.run_round(round_num)

            if verbose and round_num % 10 == 0:
                print(f"Runde {round_num}: {summary.opinion_distribution}")
                print(f"  Gj.snitt mening: {summary.average_opinion:+.3f}, "
                      f"Gj.snitt arousal: {summary.average_arousal:.3f}")

        # Final summary
        if verbose:
            print("-" * 50)
            final_dist = self._count_opinions()
            print(f"Sluttfordeling: {final_dist}")
            print(f"Totale konverteringer: {len(self.tracker.conversion_events)}")

            to_contrarian = sum(
                1 for e in self.tracker.conversion_events
                if e.direction == "to_contrarian"
            )
            to_consensus = sum(
                1 for e in self.tracker.conversion_events
                if e.direction == "to_consensus"
            )
            print(f"  Til kontrær: {to_contrarian}")
            print(f"  Til konsensus: {to_consensus}")

        return self.tracker

    def _count_opinions(self) -> dict:
        """Count agents by opinion type."""
        from models import OpinionType
        counts = {t.value: 0 for t in OpinionType}
        for agent in self.agents:
            counts[agent.opinion.classify().value] += 1
        return counts

    def get_amplification_analysis(self) -> dict:
        """Analyze algorithmic amplification bias."""
        from amplification import analyze_amplification_bias
        return analyze_amplification_bias(self.all_posts)

    def save_results(self, timestamp: str) -> dict:
        """Save all results to the experiment folder."""
        # Save transcript
        transcript_path = os.path.join(RESULTS_DIR, f"debate_transcript_{timestamp}.txt")
        with open(transcript_path, 'w', encoding='utf-8') as f:
            f.write(f"TIT-FOR-TAT EXPERIMENT: {timestamp}\n")
            f.write(f"{'='*60}\n\n")
            for post in self.all_posts:
                f.write(post.to_transcript_line())
                f.write("\n")

        # Save simulation data
        import json
        data_path = os.path.join(RESULTS_DIR, f"simulation_data_{timestamp}.json")

        data = {
            "experiment": EXPERIMENT_NAME,
            "config": {
                "num_contrarians": self.config.num_contrarians,
                "num_consensus": self.config.num_consensus,
                "num_neutrals": self.config.num_neutrals,
                "num_rounds": self.config.num_rounds,
                "reply_to_contrarian_probability": self.config.reply_to_contrarian_probability,
            },
            "results": {
                "total_posts": len(self.all_posts),
                "total_conversions": len(self.tracker.conversion_events),
                "to_contrarian": sum(1 for e in self.tracker.conversion_events if e.direction == "to_contrarian"),
                "to_consensus": sum(1 for e in self.tracker.conversion_events if e.direction == "to_consensus"),
                "final_distribution": self._count_opinions(),
            },
            "amplification_analysis": self.get_amplification_analysis(),
            "round_summaries": [
                {
                    "round": s.round_num,
                    "opinion_distribution": s.opinion_distribution,
                    "average_opinion": s.average_opinion,
                    "average_arousal": s.average_arousal,
                }
                for s in self.tracker.round_summaries
            ]
        }

        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Generate visualizations
        viz_paths = save_all_visualizations(
            self.tracker, RESULTS_DIR, timestamp
        )

        return {
            "transcript": transcript_path,
            "data": data_path,
            "visualizations": viz_paths
        }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def run_experiment(
    num_rounds: int = 50,
    reply_probability: float = 0.6,
    verbose: bool = True
) -> dict:
    """
    Run the tit-for-tat experiment.

    Args:
        num_rounds: Number of debate rounds
        reply_probability: Probability that consensus advocates reply to contrarians
        verbose: Print progress

    Returns:
        Dict with paths to all result files
    """
    # Get API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable required")

    # Create config
    config = TitForTatConfig(
        num_rounds=num_rounds,
        reply_to_contrarian_probability=reply_probability
    )

    # Run simulation
    sim = TitForTatSimulation(config, api_key)
    sim.run_simulation(verbose=verbose)

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_paths = sim.save_results(timestamp)

    if verbose:
        print(f"\n{'='*60}")
        print("EKSPERIMENT FULLFØRT")
        print(f"{'='*60}")
        print(f"Resultater lagret i: {RESULTS_DIR}")
        for name, path in result_paths.items():
            if isinstance(path, list):
                for p in path:
                    print(f"  - {os.path.basename(p)}")
            elif isinstance(path, dict):
                for vname, vpath in path.items():
                    print(f"  - {vname}: {os.path.basename(vpath)}")
            else:
                print(f"  - {name}: {os.path.basename(path)}")

    return result_paths


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Tit-for-Tat Experiment: Norwegian Energy Debate"
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
        "--reply-prob",
        type=float,
        default=0.6,
        help="Probability consensus replies to contrarian (default: 0.6)"
    )

    args = parser.parse_args()

    if not args.api_key:
        print("Error: No API key provided.")
        print("Set ANTHROPIC_API_KEY environment variable or use --api-key")
        exit(1)

    # Override env var with explicit arg
    os.environ["ANTHROPIC_API_KEY"] = args.api_key

    run_experiment(
        num_rounds=args.rounds,
        reply_probability=args.reply_prob
    )
