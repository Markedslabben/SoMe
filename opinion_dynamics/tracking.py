"""
Tracking system for the Opinion Dynamics Simulation.

Records:
- Full conversation transcript with metadata
- Per-agent state over time
- Conversion events
- Behavioral metrics evolution
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from models import Agent, Post, OpinionType, ConversionEvent
import json
from datetime import datetime


@dataclass
class AgentSnapshot:
    """Snapshot of an agent's state at a specific round."""
    round_num: int
    agent_id: str
    opinion_position: float
    opinion_type: str
    arousal: float
    anger: float
    engagement: float
    confrontation_avg: float
    consensus_orientation_avg: float


@dataclass
class RoundSummary:
    """Summary of a single simulation round."""
    round_num: int
    posts: List[Post]
    opinion_distribution: Dict[str, int]
    average_opinion: float
    average_arousal: float
    average_anger: float
    conversions: List[ConversionEvent]


class SimulationTracker:
    """
    Comprehensive tracking for the simulation.

    Maintains:
    - Full transcript of all posts
    - Per-agent history (opinion, emotion trajectories)
    - Round-by-round summaries
    - Conversion events
    """

    def __init__(self):
        self.all_posts: List[Post] = []
        self.round_summaries: List[RoundSummary] = []
        self.agent_histories: Dict[str, List[AgentSnapshot]] = {}
        self.conversion_events: List[ConversionEvent] = []
        self.start_time: datetime = datetime.now()

    def record_round(
        self,
        round_num: int,
        posts: List[Post],
        agents: List[Agent],
        conversions: List[ConversionEvent]
    ) -> RoundSummary:
        """
        Record all data from a simulation round.

        Args:
            round_num: Current round number
            posts: Posts made this round
            agents: All agents (for state snapshot)
            conversions: Any conversion events this round

        Returns:
            RoundSummary for this round
        """
        # Store posts
        for post in posts:
            post.round_num = round_num
            self.all_posts.append(post)

        # Count opinions
        distribution = {t.value: 0 for t in OpinionType}
        total_opinion = 0.0
        total_arousal = 0.0
        total_anger = 0.0

        for agent in agents:
            opinion_type = agent.opinion.classify()
            distribution[opinion_type.value] += 1
            total_opinion += agent.opinion.position
            total_arousal += agent.emotional_state.arousal
            total_anger += agent.emotional_state.anger

            # Record agent snapshot
            snapshot = AgentSnapshot(
                round_num=round_num,
                agent_id=agent.id,
                opinion_position=agent.opinion.position,
                opinion_type=opinion_type.value,
                arousal=agent.emotional_state.arousal,
                anger=agent.emotional_state.anger,
                engagement=agent.emotional_state.engagement,
                confrontation_avg=agent.behavior_metrics.confrontation_index,
                consensus_orientation_avg=agent.behavior_metrics.consensus_orientation
            )

            if agent.id not in self.agent_histories:
                self.agent_histories[agent.id] = []
            self.agent_histories[agent.id].append(snapshot)

        # Store conversion events
        self.conversion_events.extend(conversions)

        # Create round summary
        n = len(agents)
        summary = RoundSummary(
            round_num=round_num,
            posts=posts,
            opinion_distribution=distribution,
            average_opinion=total_opinion / n if n > 0 else 0,
            average_arousal=total_arousal / n if n > 0 else 0,
            average_anger=total_anger / n if n > 0 else 0,
            conversions=conversions
        )

        self.round_summaries.append(summary)
        return summary

    def get_agent_trajectory(self, agent_id: str) -> List[AgentSnapshot]:
        """Get full history for a specific agent."""
        return self.agent_histories.get(agent_id, [])

    def get_opinion_trajectories(self) -> Dict[str, List[float]]:
        """
        Get opinion position over time for all agents.

        Returns:
            Dict mapping agent_id to list of positions by round
        """
        trajectories = {}
        for agent_id, snapshots in self.agent_histories.items():
            trajectories[agent_id] = [s.opinion_position for s in snapshots]
        return trajectories

    def get_confrontation_trajectories(self) -> Dict[str, List[float]]:
        """Get confrontation index over time for all agents."""
        trajectories = {}
        for agent_id, snapshots in self.agent_histories.items():
            trajectories[agent_id] = [s.confrontation_avg for s in snapshots]
        return trajectories

    def get_emotional_trajectories(self) -> Dict[str, Dict[str, List[float]]]:
        """
        Get emotional state trajectories for all agents.

        Returns:
            Dict mapping agent_id to dict with 'arousal', 'anger', 'engagement' lists
        """
        trajectories = {}
        for agent_id, snapshots in self.agent_histories.items():
            trajectories[agent_id] = {
                'arousal': [s.arousal for s in snapshots],
                'anger': [s.anger for s in snapshots],
                'engagement': [s.engagement for s in snapshots]
            }
        return trajectories

    def generate_transcript(self) -> str:
        """
        Generate full debate transcript as readable text.

        Returns:
            Formatted transcript string
        """
        lines = [
            "=" * 70,
            "ENERGY DEBATE SIMULATION - FULL TRANSCRIPT",
            f"Generated: {datetime.now().isoformat()}",
            f"Total Rounds: {len(self.round_summaries)}",
            f"Total Posts: {len(self.all_posts)}",
            f"Conversion Events: {len(self.conversion_events)}",
            "=" * 70,
            ""
        ]

        current_round = -1
        for post in self.all_posts:
            # Round header
            if post.round_num != current_round:
                current_round = post.round_num
                # Find round summary
                summary = next(
                    (s for s in self.round_summaries if s.round_num == current_round),
                    None
                )

                lines.append("")
                lines.append(f"{'='*30} ROUND {current_round} {'='*30}")

                if summary:
                    dist = summary.opinion_distribution
                    lines.append(
                        f"Opinion Distribution: "
                        f"Contrarian={dist['contrarian']}, "
                        f"Neutral={dist['neutral']}, "
                        f"Consensus={dist['consensus']}"
                    )
                    lines.append(
                        f"Avg Opinion: {summary.average_opinion:+.2f} | "
                        f"Avg Arousal: {summary.average_arousal:.2f} | "
                        f"Avg Anger: {summary.average_anger:.2f}"
                    )

                # Add conversion events for this round
                round_conversions = [e for e in self.conversion_events if e.round_num == current_round]
                for conv in round_conversions:
                    lines.append(conv.to_log_entry())

                lines.append("-" * 70)

            # Post content
            lines.append(post.to_transcript_line())

        # Final summary
        lines.append("")
        lines.append("=" * 70)
        lines.append("SIMULATION COMPLETE")
        lines.append("=" * 70)

        if self.round_summaries:
            initial = self.round_summaries[0].opinion_distribution
            final = self.round_summaries[-1].opinion_distribution

            lines.append("")
            lines.append("INITIAL DISTRIBUTION:")
            lines.append(f"  Contrarian: {initial['contrarian']}")
            lines.append(f"  Neutral: {initial['neutral']}")
            lines.append(f"  Consensus: {initial['consensus']}")

            lines.append("")
            lines.append("FINAL DISTRIBUTION:")
            lines.append(f"  Contrarian: {final['contrarian']}")
            lines.append(f"  Neutral: {final['neutral']}")
            lines.append(f"  Consensus: {final['consensus']}")

            lines.append("")
            lines.append("CHANGES:")
            lines.append(f"  Contrarian: {final['contrarian'] - initial['contrarian']:+d}")
            lines.append(f"  Neutral: {final['neutral'] - initial['neutral']:+d}")
            lines.append(f"  Consensus: {final['consensus'] - initial['consensus']:+d}")

            lines.append("")
            lines.append(f"Total Conversions: {len(self.conversion_events)}")
            to_contrarian = sum(1 for e in self.conversion_events if e.direction == "to_contrarian")
            to_consensus = sum(1 for e in self.conversion_events if e.direction == "to_consensus")
            lines.append(f"  To Contrarian: {to_contrarian}")
            lines.append(f"  To Consensus: {to_consensus}")

        return "\n".join(lines)

    def export_data(self) -> dict:
        """
        Export all tracking data as a dictionary for JSON serialization.
        """
        return {
            "metadata": {
                "start_time": self.start_time.isoformat(),
                "end_time": datetime.now().isoformat(),
                "total_rounds": len(self.round_summaries),
                "total_posts": len(self.all_posts),
                "total_conversions": len(self.conversion_events)
            },
            "round_summaries": [
                {
                    "round": s.round_num,
                    "distribution": s.opinion_distribution,
                    "avg_opinion": s.average_opinion,
                    "avg_arousal": s.average_arousal,
                    "avg_anger": s.average_anger,
                    "num_posts": len(s.posts),
                    "num_conversions": len(s.conversions)
                }
                for s in self.round_summaries
            ],
            "agent_trajectories": {
                agent_id: [
                    {
                        "round": s.round_num,
                        "opinion": s.opinion_position,
                        "type": s.opinion_type,
                        "arousal": s.arousal,
                        "anger": s.anger,
                        "confrontation": s.confrontation_avg
                    }
                    for s in snapshots
                ]
                for agent_id, snapshots in self.agent_histories.items()
            },
            "conversion_events": [
                {
                    "round": e.round_num,
                    "agent": e.agent_id,
                    "name": e.agent_name,
                    "direction": e.direction,
                    "from": e.prev_position,
                    "to": e.new_position,
                    "trigger": e.trigger_post_content,
                    "trigger_author": e.trigger_post_author
                }
                for e in self.conversion_events
            ],
            "posts": [
                {
                    "round": p.round_num,
                    "author_id": p.author_id,
                    "author_name": p.author_name,
                    "content": p.content,
                    "emotional_intensity": p.emotional_intensity,
                    "provocativeness": p.provocativeness,
                    "visibility": p.visibility_score
                }
                for p in self.all_posts
            ]
        }

    def save_transcript(self, filepath: str) -> None:
        """Save transcript to file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(self.generate_transcript())

    def save_data(self, filepath: str) -> None:
        """Save full data export to JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.export_data(), f, indent=2)


def detect_conversion(
    agent: Agent,
    round_num: int,
    trigger_post: Optional[Post] = None
) -> Optional[ConversionEvent]:
    """
    Check if an agent just converted (crossed opinion threshold).

    Each agent can only convert ONCE per direction. Once they've converted
    to contrarian, subsequent threshold crossings in that direction are ignored.
    This prevents the same agent from being counted multiple times due to
    opinion bouncing around the threshold.

    Args:
        agent: The agent to check
        round_num: Current round number
        trigger_post: The post that may have triggered conversion

    Returns:
        ConversionEvent if conversion occurred, None otherwise
    """
    history = agent.opinion.position_history
    if len(history) < 2:
        return None

    prev_pos = history[-2]
    curr_pos = history[-1]

    # Only neutrals can convert
    if agent.role.name != "NEUTRAL_OBSERVER":
        return None

    # Check if crossed contrarian threshold (-0.3) AND hasn't already converted
    if prev_pos >= -0.3 and curr_pos < -0.3 and not agent.has_converted_to_contrarian:
        agent.has_converted_to_contrarian = True  # Mark as converted
        return ConversionEvent(
            round_num=round_num,
            agent_id=agent.id,
            agent_name=agent.name,
            direction="to_contrarian",
            prev_position=prev_pos,
            new_position=curr_pos,
            trigger_post_content=trigger_post.content if trigger_post else None,
            trigger_post_author=trigger_post.author_name if trigger_post else None,
            agent_arousal=agent.emotional_state.arousal,
            agent_anger=agent.emotional_state.anger
        )

    # Check if crossed consensus threshold (+0.3) AND hasn't already converted
    if prev_pos <= 0.3 and curr_pos > 0.3 and not agent.has_converted_to_consensus:
        agent.has_converted_to_consensus = True  # Mark as converted
        return ConversionEvent(
            round_num=round_num,
            agent_id=agent.id,
            agent_name=agent.name,
            direction="to_consensus",
            prev_position=prev_pos,
            new_position=curr_pos,
            trigger_post_content=trigger_post.content if trigger_post else None,
            trigger_post_author=trigger_post.author_name if trigger_post else None,
            agent_arousal=agent.emotional_state.arousal,
            agent_anger=agent.emotional_state.anger
        )

    return None
