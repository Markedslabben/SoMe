"""
Emotional dynamics engine for the Opinion Dynamics Simulation.

Models human-like emotional responses to debate content including:
- Emotional contagion (anger spreads)
- Provocation responses
- Agreement validation
- Backlash effects
"""

from dataclasses import dataclass
from typing import Tuple
from models import EmotionalState, Post, Agent


@dataclass
class EmotionalImpact:
    """Result of processing a post's emotional impact on a reader."""
    arousal_delta: float = 0.0
    anger_delta: float = 0.0
    valence_delta: float = 0.0
    engagement_delta: float = 0.0
    trust_delta: float = 0.0


class EmotionalEngine:
    """
    Processes emotional dynamics between posts and readers.

    Models how reading content affects emotional state and
    how emotional state affects behavior.
    """

    # Thresholds for emotional responses
    PROVOCATION_THRESHOLD = 0.5     # Above this triggers anger
    AGREEMENT_THRESHOLD = 0.3       # Below this is agreeable content
    EXTREME_PROVOCATION = 0.8       # Above this can cause backlash
    CONTAGION_RATE = 0.3            # How much emotion spreads

    def calculate_emotional_impact(
        self,
        post: Post,
        reader: Agent,
        opinion_alignment: float
    ) -> EmotionalImpact:
        """
        Calculate how a post affects a reader's emotional state.

        Args:
            post: The post being read
            reader: The agent reading the post
            opinion_alignment: How aligned their opinions are (-1 to +1)

        Returns:
            EmotionalImpact with deltas to apply
        """
        impact = EmotionalImpact()

        # Base emotional contagion from post intensity
        impact.arousal_delta = post.emotional_intensity * self.CONTAGION_RATE

        # Provocation effects
        if post.provocativeness > self.PROVOCATION_THRESHOLD:
            # Disagreement with provocative content causes anger
            if opinion_alignment < 0:  # They disagree with post
                anger_increase = post.provocativeness * abs(opinion_alignment) * 0.5
                impact.anger_delta = anger_increase
                impact.valence_delta = -post.provocativeness * 0.3

                # Extreme provocation may reduce trust in author
                if post.provocativeness > self.EXTREME_PROVOCATION:
                    impact.trust_delta = -0.15
            else:
                # Agreement with provocative content validates and energizes
                impact.engagement_delta = post.provocativeness * 0.3
                impact.valence_delta = post.provocativeness * 0.1

        # Agreeable/consensus-oriented content
        if post.consensus_orientation > 0.6:
            if opinion_alignment > 0:  # They agree with post
                impact.arousal_delta -= 0.1  # Calming effect
                impact.valence_delta += 0.15
                impact.trust_delta += 0.05
            else:
                # Disagreement with reasonable content is less inflammatory
                impact.arousal_delta += 0.05

        # Engagement always increases when reading (they're paying attention)
        impact.engagement_delta += 0.1 * post.emotional_intensity

        return impact

    def apply_impact(self, agent: Agent, impact: EmotionalImpact, author_id: str) -> None:
        """Apply emotional impact to an agent."""
        state = agent.emotional_state

        state.arousal = max(0.0, min(1.0, state.arousal + impact.arousal_delta))
        state.anger = max(0.0, min(1.0, state.anger + impact.anger_delta))
        state.valence = max(-1.0, min(1.0, state.valence + impact.valence_delta))
        state.engagement = max(0.0, min(1.0, state.engagement + impact.engagement_delta))

        # Update trust in author
        if impact.trust_delta != 0:
            agent.update_trust(author_id, impact.trust_delta)

    def process_post_for_reader(
        self,
        post: Post,
        reader: Agent
    ) -> Tuple[EmotionalImpact, float]:
        """
        Full processing of a post's effect on a reader.

        Returns:
            Tuple of (EmotionalImpact, opinion_influence)
        """
        # Calculate opinion alignment
        # Infer post's opinion direction from its characteristics
        if post.provocativeness > 0.5:
            # Provocative posts are typically contrarian
            post_opinion = -0.7
        elif post.consensus_orientation > 0.6:
            # Consensus-oriented posts support mainstream
            post_opinion = 0.6
        else:
            # Neutral/mixed posts
            post_opinion = 0.0

        opinion_alignment = 1 - abs(post_opinion - reader.opinion.position) / 2

        # Calculate emotional impact
        impact = self.calculate_emotional_impact(post, reader, opinion_alignment)

        # Calculate opinion influence direction
        # Positive = toward consensus, Negative = toward contrarian
        if post.provocativeness > post.consensus_orientation:
            influence_direction = -1  # Contrarian influence
        else:
            influence_direction = 1   # Consensus influence

        # Influence strength based on emotional intensity and logic
        influence_strength = (
            post.emotional_intensity * 0.4 +
            post.logical_coherence * 0.3 +
            (1 if opinion_alignment > 0.5 else 0.5) * 0.3
        )

        opinion_influence = influence_direction * influence_strength * 0.3

        return impact, opinion_influence


def calculate_response_probability(agent: Agent, base_rate: float = 0.2) -> float:
    """
    Calculate probability that an agent posts this round.

    Agitated, angry, engaged agents are more likely to respond.
    """
    urgency = agent.emotional_state.urgency_multiplier()

    # Contrarians are naturally more vocal
    role_boost = 0.2 if "CONTRARIAN" in agent.role.name else 0.0

    # Recently provoked agents respond more
    anger_boost = agent.emotional_state.anger * 0.3

    probability = base_rate * urgency + role_boost + anger_boost

    return min(0.9, probability)  # Cap at 90%


def describe_emotional_climate(agents: list) -> str:
    """Generate a natural language description of population emotional state."""
    avg_arousal = sum(a.emotional_state.arousal for a in agents) / len(agents)
    avg_anger = sum(a.emotional_state.anger for a in agents) / len(agents)
    avg_engagement = sum(a.emotional_state.engagement for a in agents) / len(agents)

    if avg_arousal > 0.7:
        arousal_desc = "The debate has become heated and intense."
    elif avg_arousal > 0.5:
        arousal_desc = "There's notable tension in the discussion."
    else:
        arousal_desc = "The conversation remains relatively calm."

    if avg_anger > 0.5:
        anger_desc = " Many participants are visibly frustrated."
    elif avg_anger > 0.3:
        anger_desc = " Some irritation is apparent."
    else:
        anger_desc = ""

    if avg_engagement > 0.7:
        engage_desc = " People are deeply invested in the outcome."
    elif avg_engagement > 0.5:
        engage_desc = " Interest in the debate is moderate."
    else:
        engage_desc = " Engagement seems to be waning."

    return arousal_desc + anger_desc + engage_desc
