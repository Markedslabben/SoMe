"""
Main simulation engine for the Opinion Dynamics experiment.

Orchestrates the 50-round debate between 25 agents, handling:
- Agent initialization
- Speaker selection
- Post generation (LLM calls)
- Feed distribution
- Opinion and emotional updates
- Conversion detection
- Full tracking
"""

import random
from typing import List, Optional
from models import (
    Agent, AgentRole, Opinion, EmotionalState, Post,
    SimulationConfig, ConversionEvent, BehaviorMetrics,
    PersonalityType, PersonalityTraits
)
from agents import LLMAgent
from emotions import EmotionalEngine, calculate_response_probability
from amplification import AmplificationAlgorithm, compute_opinion_influence
from tracking import SimulationTracker, detect_conversion, RoundSummary


class SimulationEngine:
    """
    Main orchestrator for the opinion dynamics simulation.

    Manages the complete lifecycle:
    1. Initialize 25 agents (1 contrarian, 4 consensus, 20 neutral)
    2. Run 50 debate rounds
    3. Track all state changes and conversions
    4. Output final analysis
    """

    def __init__(self, config: SimulationConfig, api_key: str):
        """
        Initialize simulation with configuration.

        Args:
            config: Simulation parameters
            api_key: Anthropic API key for LLM calls
        """
        self.config = config
        self.llm = LLMAgent(api_key, config.model)
        self.amplifier = AmplificationAlgorithm(config)
        self.emotion_engine = EmotionalEngine()
        self.tracker = SimulationTracker()

        self.agents: List[Agent] = []
        self.all_posts: List[Post] = []

    def initialize_population(self) -> None:
        """
        Create the 25-agent population.

        Distribution:
        - 1 Contrarian (provocative, high confidence)
        - 4 Consensus (mainstream, moderate confidence)
        - 20 Neutral (undecided, low confidence, persuadable)
        """
        agent_id = 0

        # === CONTRARIAN AGENTS (1) ===
        for i in range(self.config.num_contrarians):
            self.agents.append(Agent(
                id=f"C{agent_id}",
                role=AgentRole.CONTRARIAN_PROVOCATEUR,
                name="Contrarian",
                opinion=Opinion(
                    position=-0.85,      # Strongly contrarian
                    confidence=0.9,      # Very confident
                    stability=0.8        # Won't change easily
                ),
                emotional_state=EmotionalState(
                    arousal=0.7,         # Already activated
                    valence=-0.2,        # Slightly negative mood
                    engagement=0.85,     # Highly engaged
                    anger=0.3,           # Some baseline frustration
                    anxiety=0.1          # Low anxiety (confident)
                ),
                behavior_metrics=BehaviorMetrics()
            ))
            agent_id += 1

        # === CONSENSUS AGENTS (4) ===
        consensus_names = ["Expert", "Researcher", "Analyst", "Pragmatist"]
        for i in range(self.config.num_consensus):
            name = consensus_names[i] if i < len(consensus_names) else f"Consensus_{i}"
            self.agents.append(Agent(
                id=f"S{agent_id}",
                role=AgentRole.CONSENSUS_ADVOCATE,
                name=name,
                opinion=Opinion(
                    position=0.7 + random.uniform(-0.1, 0.1),  # Mainstream with slight variation
                    confidence=0.7,
                    stability=0.6
                ),
                emotional_state=EmotionalState(
                    arousal=0.5,
                    valence=0.1,
                    engagement=0.6,
                    anger=0.1,
                    anxiety=0.2
                ),
                behavior_metrics=BehaviorMetrics()
            ))
            agent_id += 1

        # === NEUTRAL AGENTS (20) ===
        # Names now reflect personality types for clarity
        neutral_configs = [
            # Analytical types (20%) - demand evidence, resist emotion
            ("Skeptic", PersonalityType.ANALYTICAL),
            ("Engineer", PersonalityType.ANALYTICAL),
            ("Analyst", PersonalityType.ANALYTICAL),
            ("Researcher", PersonalityType.ANALYTICAL),
            # Reactive types (20%) - highly swayed by emotion
            ("Worried", PersonalityType.REACTIVE),
            ("Frustrated", PersonalityType.REACTIVE),
            ("Anxious", PersonalityType.REACTIVE),
            ("Outraged", PersonalityType.REACTIVE),
            # Conformist types (20%) - follow perceived majority
            ("Follower", PersonalityType.CONFORMIST),
            ("Agreeable", PersonalityType.CONFORMIST),
            ("Moderate", PersonalityType.CONFORMIST),
            ("Mainstream", PersonalityType.CONFORMIST),
            # Disengaged types (20%) - slow to change, low attention
            ("Casual", PersonalityType.DISENGAGED),
            ("Busy", PersonalityType.DISENGAGED),
            ("Lurker", PersonalityType.DISENGAGED),
            ("Passive", PersonalityType.DISENGAGED),
            # Balanced types (20%) - weighs both sides
            ("Curious", PersonalityType.BALANCED),
            ("OpenMinded", PersonalityType.BALANCED),
            ("Thoughtful", PersonalityType.BALANCED),
            ("Undecided", PersonalityType.BALANCED),
        ]

        for i in range(self.config.num_neutrals):
            if i < len(neutral_configs):
                name, personality = neutral_configs[i]
            else:
                # Extra neutrals get random personality
                name = f"Neutral_{i}"
                personality = random.choice(list(PersonalityType))

            # Slight random variation in starting position
            start_pos = random.uniform(-0.2, 0.2)

            self.agents.append(Agent(
                id=f"N{agent_id}",
                role=AgentRole.NEUTRAL_OBSERVER,
                name=name,
                opinion=Opinion(
                    position=start_pos,
                    confidence=0.3,      # Uncertain
                    stability=0.2        # Easily persuaded
                ),
                emotional_state=EmotionalState(
                    arousal=0.4,
                    valence=0.0,
                    engagement=0.4,
                    anger=0.0,
                    anxiety=0.4          # Uncertain = anxious
                ),
                behavior_metrics=BehaviorMetrics(),
                personality=personality,
                personality_traits=PersonalityTraits.from_personality(personality)
            ))
            agent_id += 1

        # Initialize trust scores (slight in-group bias)
        for agent in self.agents:
            for other in self.agents:
                if other.id != agent.id:
                    # Base trust
                    base_trust = 0.5

                    # In-group trust bonus
                    if agent.role == other.role:
                        base_trust = 0.6

                    # Contrarians are initially distrusted by consensus
                    if agent.role == AgentRole.CONSENSUS_ADVOCATE and other.role == AgentRole.CONTRARIAN_PROVOCATEUR:
                        base_trust = 0.35

                    # Neutrals start with moderate trust in everyone
                    if agent.role == AgentRole.NEUTRAL_OBSERVER:
                        base_trust = 0.5

                    agent.trust_scores[other.id] = base_trust

        # Record initial opinion positions
        for agent in self.agents:
            agent.opinion.position_history.append(agent.opinion.position)

        print(f"Initialized {len(self.agents)} agents:")
        print(f"  - {self.config.num_contrarians} Contrarian(s)")
        print(f"  - {self.config.num_consensus} Consensus advocates")
        print(f"  - {self.config.num_neutrals} Neutral observers")

    def select_speakers(self, round_num: int) -> List[Agent]:
        """
        Select which agents post this round.

        Selection is weighted by:
        - Emotional urgency (aroused/angry agents post more)
        - Role (contrarians are naturally more vocal)

        Args:
            round_num: Current round number

        Returns:
            List of agents who will post this round
        """
        # Calculate posting probability for each agent
        probabilities = []
        for agent in self.agents:
            prob = calculate_response_probability(agent, base_rate=0.2)
            probabilities.append(prob)

        # Normalize to get weights
        total = sum(probabilities)
        weights = [p / total for p in probabilities]

        # Select speakers (with replacement allowed for variety)
        num_speakers = self.config.posts_per_round
        speakers = random.choices(self.agents, weights=weights, k=num_speakers)

        # Ensure contrarian has voice at least every 3 rounds
        contrarians = [a for a in self.agents if a.role == AgentRole.CONTRARIAN_PROVOCATEUR]
        if contrarians and round_num % 3 == 0:
            if contrarians[0] not in speakers:
                speakers[0] = contrarians[0]

        # Remove duplicates while maintaining order
        seen = set()
        unique_speakers = []
        for speaker in speakers:
            if speaker.id not in seen:
                seen.add(speaker.id)
                unique_speakers.append(speaker)

        return unique_speakers

    def run_round(self, round_num: int) -> RoundSummary:
        """
        Execute a single simulation round.

        Steps:
        1. Select speakers based on emotional urgency
        2. Generate posts via LLM
        3. Rank posts via amplification algorithm
        4. Distribute feed to all agents
        5. Update emotions and opinions
        6. Detect conversions
        7. Decay emotions

        Args:
            round_num: Current round number

        Returns:
            RoundSummary with all tracked data
        """
        # 1. Select speakers
        speakers = self.select_speakers(round_num)

        # 2. Generate posts
        round_posts = []
        for agent in speakers:
            post = self.llm.generate_post(
                agent,
                self.config.debate_topic,
                self.config.max_tokens_per_response
            )
            post.round_num = round_num
            round_posts.append(post)
            agent.posts_made.append(post.id)

        self.all_posts.extend(round_posts)

        # 3. Rank and sample visible posts
        visible_posts = self.amplifier.sample_visible_posts(
            self.all_posts,
            round_num,
            sample_size=10
        )

        # 4. Distribute to all agents and update states
        round_conversions: List[ConversionEvent] = []
        last_influential_post: Optional[Post] = None

        for agent in self.agents:
            for post in visible_posts:
                if post.author_id == agent.id:
                    continue  # Don't read own posts

                # Remember the post
                agent.remember_post(post, self.config.memory_window)

                # Compute emotional impact and opinion influence
                impact, opinion_influence = self.emotion_engine.process_post_for_reader(
                    post, agent
                )

                # Apply emotional impact
                self.emotion_engine.apply_impact(agent, impact, post.author_id)

                # Update opinion (only for neutrals - others have fixed positions)
                if agent.role == AgentRole.NEUTRAL_OBSERVER:
                    # Get influence components
                    influence_dir, influence_str, is_contrarian = compute_opinion_influence(
                        post,
                        agent.opinion.position,
                        agent.get_trust(post.author_id)
                    )

                    # Apply opinion update (personality-aware)
                    delta = agent.opinion.update(
                        influence=influence_dir * influence_str,
                        source_trust=agent.get_trust(post.author_id),
                        emotional_impact=post.emotional_intensity,
                        is_contrarian_source=is_contrarian,
                        logical_coherence=post.logical_coherence,
                        personality_traits=agent.personality_traits
                    )

                    # Track potentially influential post
                    if abs(delta) > 0.05:
                        last_influential_post = post

                    # Check for conversion
                    conversion = detect_conversion(agent, round_num, last_influential_post)
                    if conversion:
                        round_conversions.append(conversion)
                        print(f"  CONVERSION: {agent.name} -> {conversion.direction}")

        # 5. Decay emotions for all agents
        for agent in self.agents:
            agent.emotional_state.decay(self.config.emotional_decay_rate)

        # 6. Record round in tracker
        summary = self.tracker.record_round(
            round_num,
            round_posts,
            self.agents,
            round_conversions
        )

        return summary

    def run_simulation(self, verbose: bool = True) -> SimulationTracker:
        """
        Run the complete simulation.

        Args:
            verbose: Whether to print progress

        Returns:
            SimulationTracker with all recorded data
        """
        # Initialize
        self.initialize_population()

        if verbose:
            print(f"\nStarting simulation: {self.config.debate_topic[:50]}...")
            print(f"Duration: {self.config.num_rounds} rounds")
            print(f"Posts per round: {self.config.posts_per_round}")
            print()

        # Record initial state
        initial_dist = self._count_opinions()
        if verbose:
            print(f"Initial distribution: {initial_dist}")
            print("-" * 50)

        # Run rounds
        for round_num in range(1, self.config.num_rounds + 1):
            summary = self.run_round(round_num)

            if verbose and round_num % 10 == 0:
                print(f"Round {round_num}: {summary.opinion_distribution}")
                print(f"  Avg opinion: {summary.average_opinion:+.3f}, "
                      f"Avg arousal: {summary.average_arousal:.3f}, "
                      f"Avg anger: {summary.average_anger:.3f}")

        # Final summary
        if verbose:
            print("-" * 50)
            final_dist = self._count_opinions()
            print(f"Final distribution: {final_dist}")
            print(f"Total conversions: {len(self.tracker.conversion_events)}")

            # Count conversion directions
            to_contrarian = sum(
                1 for e in self.tracker.conversion_events
                if e.direction == "to_contrarian"
            )
            to_consensus = sum(
                1 for e in self.tracker.conversion_events
                if e.direction == "to_consensus"
            )
            print(f"  To contrarian: {to_contrarian}")
            print(f"  To consensus: {to_consensus}")

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
