"""
Core domain models for the Opinion Dynamics Simulation.

Models the agents, their opinions, emotional states, posts, and behavioral metrics
for simulating social media debate dynamics around energy policy.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import statistics


class OpinionType(Enum):
    """Classification of agent opinion position."""
    CONTRARIAN = "contrarian"      # Anti-consensus, provocative
    CONSENSUS = "consensus"        # Mainstream, evidence-based
    NEUTRAL = "neutral"            # Undecided, persuadable


class AgentRole(Enum):
    """Agent behavioral archetype defining debate style."""
    CONTRARIAN_PROVOCATEUR = "contrarian_provocateur"
    CONSENSUS_ADVOCATE = "consensus_advocate"
    NEUTRAL_OBSERVER = "neutral_observer"


@dataclass
class EmotionalState:
    """
    Agent's emotional state affecting behavior and response patterns.

    Models human-like emotional responses to debate content:
    - Arousal: General activation level (calm vs agitated)
    - Valence: Mood direction (negative vs positive)
    - Engagement: Investment in the debate
    - Anger: Specific response to provocation
    - Anxiety: Uncertainty about position
    """
    arousal: float = 0.5        # 0.0=calm, 1.0=highly agitated
    valence: float = 0.0        # -1.0=negative, +1.0=positive mood
    engagement: float = 0.5     # 0.0=disengaged, 1.0=deeply invested
    anger: float = 0.0          # 0.0=calm, 1.0=furious
    anxiety: float = 0.3        # 0.0=confident, 1.0=very uncertain

    # History for volatility calculation
    arousal_history: List[float] = field(default_factory=list)

    def urgency_multiplier(self) -> float:
        """
        Calculate response urgency - agitated/angry agents respond faster.
        Returns multiplier affecting probability of posting.
        """
        base = 0.5
        arousal_boost = self.arousal * 0.3
        anger_boost = self.anger * 0.2
        engagement_boost = self.engagement * 0.2
        return base + arousal_boost + anger_boost + engagement_boost

    def decay(self, rate: float = 0.1) -> None:
        """
        Emotions decay toward baseline over time.
        Called each round to simulate emotional cooling.
        """
        # Arousal decays toward 0.4 (slightly calm baseline)
        self.arousal = self.arousal - (self.arousal - 0.4) * rate
        # Anger decays faster (people calm down)
        self.anger = max(0.0, self.anger - rate * 1.5)
        # Engagement decays slowly
        self.engagement = max(0.3, self.engagement - rate * 0.5)
        # Valence drifts toward neutral
        self.valence = self.valence * (1 - rate * 0.5)

        # Record for volatility tracking
        self.arousal_history.append(self.arousal)

    def react_to_provocation(self, intensity: float) -> None:
        """React to provocative content."""
        self.arousal = min(1.0, self.arousal + intensity * 0.3)
        self.anger = min(1.0, self.anger + intensity * 0.4)
        self.engagement = min(1.0, self.engagement + intensity * 0.2)
        self.valence = max(-1.0, self.valence - intensity * 0.2)

    def react_to_agreement(self, intensity: float) -> None:
        """React to agreeable/validating content."""
        self.arousal = max(0.2, self.arousal - intensity * 0.1)
        self.valence = min(1.0, self.valence + intensity * 0.2)
        self.engagement = min(1.0, self.engagement + intensity * 0.1)

    def get_volatility(self) -> float:
        """Calculate emotional volatility from arousal history."""
        if len(self.arousal_history) < 2:
            return 0.0
        return statistics.stdev(self.arousal_history)

    def to_description(self) -> str:
        """Convert to natural language for prompts."""
        # Arousal description
        if self.arousal < 0.3:
            arousal_desc = "calm and collected"
        elif self.arousal < 0.6:
            arousal_desc = "somewhat alert"
        elif self.arousal < 0.8:
            arousal_desc = "agitated and tense"
        else:
            arousal_desc = "highly activated and restless"

        # Anger description
        if self.anger < 0.2:
            anger_desc = ""
        elif self.anger < 0.5:
            anger_desc = ", mildly frustrated"
        elif self.anger < 0.8:
            anger_desc = ", quite angry"
        else:
            anger_desc = ", furious"

        # Engagement description
        if self.engagement < 0.4:
            engage_desc = "You don't care much about this debate."
        elif self.engagement < 0.7:
            engage_desc = "You're moderately interested in this discussion."
        else:
            engage_desc = "You're deeply invested in this debate and feel compelled to speak."

        return f"You feel {arousal_desc}{anger_desc}. {engage_desc}"


@dataclass
class Opinion:
    """
    Agent's opinion on the energy debate.

    Position: -1.0 (strongly contrarian) to +1.0 (strongly consensus)

    For the energy debate:
    - Negative: "Nuclear only! Renewables are a scam! Markets are rigged!"
    - Positive: "Balanced mix, trust the market, renewables are viable"
    - Near zero: Genuinely undecided
    """
    position: float              # -1.0 to +1.0
    confidence: float = 0.5      # 0.0=uncertain, 1.0=absolutely certain
    stability: float = 0.3       # Resistance to change (grows over time)

    # Track position history for trajectory visualization
    position_history: List[float] = field(default_factory=list)

    def classify(self) -> OpinionType:
        """Classify into discrete category for counting."""
        if self.position < -0.3:
            return OpinionType.CONTRARIAN
        elif self.position > 0.3:
            return OpinionType.CONSENSUS
        return OpinionType.NEUTRAL

    def update(
        self,
        influence: float,
        source_trust: float,
        emotional_impact: float,
        is_contrarian_source: bool = False
    ) -> float:
        """
        Update opinion based on external influence.

        Args:
            influence: Direction and strength of influence (-1 to +1)
            source_trust: Trust in the source (0 to 1)
            emotional_impact: Emotional intensity of the content (0 to 1)
            is_contrarian_source: Whether source is a known contrarian

        Returns:
            The actual change applied (for tracking conversion moments)
        """
        # Calculate susceptibility: uncertain, unstable opinions change more
        susceptibility = (1 - self.confidence * 0.4) * (1 - self.stability * 0.3)

        # Emotional impact increases susceptibility (less rational evaluation)
        susceptibility *= (1 + emotional_impact * 0.4)

        # Backlash effect: extremely provocative content can backfire
        if emotional_impact > 0.8 and is_contrarian_source:
            # 30% chance of reactance (moving opposite direction)
            import random
            if random.random() < 0.3:
                influence = -influence * 0.5

        # Calculate and apply delta
        delta = influence * source_trust * susceptibility * 0.15
        old_position = self.position
        self.position = max(-1.0, min(1.0, self.position + delta))

        # Stability increases slightly (opinions solidify)
        self.stability = min(0.9, self.stability + 0.01)

        # Record history
        self.position_history.append(self.position)

        return self.position - old_position

    def to_description(self) -> str:
        """Convert to natural language for neutral agent prompts."""
        if self.position < -0.6:
            return "You're strongly leaning toward the contrarian view - skeptical of renewables and the energy market."
        elif self.position < -0.3:
            return "You're somewhat skeptical of the mainstream energy narrative."
        elif self.position < -0.1:
            return "You're slightly leaning contrarian but still quite uncertain."
        elif self.position < 0.1:
            return "You're genuinely undecided, seeing valid points on both sides."
        elif self.position < 0.3:
            return "You're slightly leaning toward the consensus view on energy transition."
        elif self.position < 0.6:
            return "You're moderately supportive of the mainstream energy policy approach."
        else:
            return "You strongly support the consensus view on balanced energy transition."


@dataclass
class BehaviorMetrics:
    """
    Tracks an agent's behavioral patterns over the simulation.
    Used for analyzing confrontation styles and emotional volatility.
    """
    confrontation_scores: List[float] = field(default_factory=list)
    consensus_orientation_scores: List[float] = field(default_factory=list)
    posts_count: int = 0
    replies_count: int = 0

    @property
    def confrontation_index(self) -> float:
        """Average confrontation level across all posts."""
        if not self.confrontation_scores:
            return 0.0
        return statistics.mean(self.confrontation_scores)

    @property
    def consensus_orientation(self) -> float:
        """Average cooperativeness across all posts."""
        if not self.consensus_orientation_scores:
            return 0.5
        return statistics.mean(self.consensus_orientation_scores)

    def record_post(self, confrontation: float, consensus_orient: float, is_reply: bool = False) -> None:
        """Record metrics from a new post."""
        self.confrontation_scores.append(confrontation)
        self.consensus_orientation_scores.append(consensus_orient)
        self.posts_count += 1
        if is_reply:
            self.replies_count += 1


@dataclass
class Post:
    """
    A single post in the debate feed.

    Contains the content plus analyzed metrics for amplification
    and influence calculation.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    author_id: str = ""
    author_name: str = ""
    round_num: int = 0
    content: str = ""

    # Analyzed content metrics
    emotional_intensity: float = 0.0    # 0-1, how emotionally charged
    provocativeness: float = 0.0        # 0-1, how confrontational
    logical_coherence: float = 0.5      # 0-1, argument quality
    consensus_orientation: float = 0.5  # 0-1, how cooperative/agreeable

    # Computed by amplification algorithm
    visibility_score: float = 0.0

    # Metadata
    timestamp: datetime = field(default_factory=datetime.now)
    reply_to: Optional[str] = None

    # Author state at time of posting (for transcript)
    author_arousal: float = 0.0
    author_opinion: float = 0.0

    def engagement_potential(self) -> float:
        """
        Estimate engagement this post will generate.
        Provocative, emotional content generates more engagement.
        """
        return (
            self.emotional_intensity * 0.4 +
            self.provocativeness * 0.4 +
            (1 - self.logical_coherence) * 0.2
        )

    def to_transcript_line(self) -> str:
        """Format for debate transcript output."""
        state_info = f"arousal={self.author_arousal:.2f}, opinion={self.author_opinion:+.2f}"
        metrics = f"visibility={self.visibility_score:.2f}, confrontation={self.provocativeness:.2f}"
        return (
            f"[{self.author_id}-{self.author_name}] ({state_info}):\n"
            f'"{self.content}"\n'
            f">> {metrics}\n"
        )


@dataclass
class Agent:
    """
    A social media agent in the energy debate simulation.

    Each agent has:
    - A role determining their base behavior (contrarian/consensus/neutral)
    - An opinion that can shift (for neutrals)
    - Emotional state affecting responses
    - Memory of recent posts
    - Trust scores for other agents
    - Behavioral metrics tracking their style
    """
    id: str
    role: AgentRole
    name: str
    opinion: Opinion
    emotional_state: EmotionalState = field(default_factory=EmotionalState)
    behavior_metrics: BehaviorMetrics = field(default_factory=BehaviorMetrics)

    # Memory: recent posts seen (sliding window)
    memory: List[str] = field(default_factory=list)

    # Posts authored by this agent
    posts_made: List[str] = field(default_factory=list)

    # Trust in other agents (agent_id -> trust score)
    trust_scores: Dict[str, float] = field(default_factory=dict)

    # Track conversion events
    conversion_events: List[Dict] = field(default_factory=list)

    @property
    def initial_type(self) -> str:
        """What type was this agent initially?"""
        if self.role == AgentRole.CONTRARIAN_PROVOCATEUR:
            return "contrarian"
        elif self.role == AgentRole.CONSENSUS_ADVOCATE:
            return "consensus"
        return "neutral"

    def remember_post(self, post: Post, max_memory: int = 15) -> None:
        """Add post to memory with sliding window."""
        summary = f"[{post.author_name}]: {post.content}"
        self.memory.append(summary)
        if len(self.memory) > max_memory:
            self.memory.pop(0)

    def get_trust(self, other_id: str, default: float = 0.5) -> float:
        """Get trust score for another agent."""
        return self.trust_scores.get(other_id, default)

    def update_trust(self, other_id: str, delta: float) -> None:
        """Adjust trust based on interaction quality."""
        current = self.get_trust(other_id)
        self.trust_scores[other_id] = max(0.1, min(1.0, current + delta))

    def check_conversion(self, round_num: int, trigger_post: Optional[Post] = None) -> Optional[Dict]:
        """
        Check if a conversion happened (neutral crossing threshold).
        Returns conversion event dict if conversion occurred.
        """
        if self.role != AgentRole.NEUTRAL_OBSERVER:
            return None

        history = self.opinion.position_history
        if len(history) < 2:
            return None

        prev_pos = history[-2]
        curr_pos = history[-1]

        # Check if crossed contrarian threshold
        if prev_pos >= -0.3 and curr_pos < -0.3:
            event = {
                "round": round_num,
                "agent_id": self.id,
                "direction": "to_contrarian",
                "prev_position": prev_pos,
                "new_position": curr_pos,
                "trigger_post": trigger_post.content if trigger_post else None,
                "trigger_author": trigger_post.author_name if trigger_post else None,
                "emotional_state": {
                    "arousal": self.emotional_state.arousal,
                    "anger": self.emotional_state.anger
                }
            }
            self.conversion_events.append(event)
            return event

        # Check if crossed consensus threshold
        if prev_pos <= 0.3 and curr_pos > 0.3:
            event = {
                "round": round_num,
                "agent_id": self.id,
                "direction": "to_consensus",
                "prev_position": prev_pos,
                "new_position": curr_pos,
                "trigger_post": trigger_post.content if trigger_post else None,
                "trigger_author": trigger_post.author_name if trigger_post else None,
                "emotional_state": {
                    "arousal": self.emotional_state.arousal,
                    "anger": self.emotional_state.anger
                }
            }
            self.conversion_events.append(event)
            return event

        return None


@dataclass
class SimulationConfig:
    """Configuration for the simulation run."""
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

    # Debate topic
    debate_topic: str = (
        "The Energy Transition: Should we rely primarily on renewables, nuclear, "
        "or a mix? How should the electricity market be structured? "
        "Are current consumer electricity prices and energy taxes justified?"
    )

    @property
    def total_agents(self) -> int:
        return self.num_contrarians + self.num_consensus + self.num_neutrals


@dataclass
class ConversionEvent:
    """Record of a neutral agent crossing an opinion threshold."""
    round_num: int
    agent_id: str
    agent_name: str
    direction: str  # "to_contrarian" or "to_consensus"
    prev_position: float
    new_position: float
    trigger_post_content: Optional[str]
    trigger_post_author: Optional[str]
    agent_arousal: float
    agent_anger: float

    def to_log_entry(self) -> str:
        """Format for transcript output."""
        direction_text = "CONTRARIAN" if self.direction == "to_contrarian" else "CONSENSUS"
        trigger_info = ""
        if self.trigger_post_content:
            trigger_info = (
                f"- Trigger post: [{self.trigger_post_author}] "
                f'"{self.trigger_post_content[:80]}..."\n'
            )

        return (
            f"\n{'='*60}\n"
            f"CONVERSION EVENT @ Round {self.round_num}\n"
            f"Agent {self.agent_id} ({self.agent_name}) shifted to {direction_text}\n"
            f"- Previous position: {self.prev_position:+.2f}\n"
            f"- New position: {self.new_position:+.2f}\n"
            f"{trigger_info}"
            f"- Emotional state: arousal={self.agent_arousal:.2f}, anger={self.agent_anger:.2f}\n"
            f"{'='*60}\n"
        )
