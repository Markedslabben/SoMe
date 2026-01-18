"""
Algorithmic feed amplification model for the Opinion Dynamics Simulation.

Models how social media algorithms prioritize emotional/provocative content,
creating feedback loops that advantage controversial positions.
"""

import random
from typing import List, Tuple
from models import Post, Agent, SimulationConfig


class AmplificationAlgorithm:
    """
    Models social media feed ranking algorithm.

    Key insight: Engagement-driven algorithms amplify emotional
    and provocative content because it generates more reactions,
    even if those reactions are negative.

    The visibility formula creates a feedback loop:
    provocative → more visible → more exposure → more influence → more provocation
    """

    def __init__(self, config: SimulationConfig):
        """
        Initialize with configuration weights.

        Args:
            config: Simulation config with amplification weights
        """
        self.emotion_weight = config.emotion_weight
        self.provocative_weight = config.provocative_weight
        self.recency_weight = config.recency_weight

    def compute_visibility(self, post: Post, current_round: int) -> float:
        """
        Compute visibility score for a post.

        Formula:
        visibility = (emotion_weight * emotional_intensity +
                     provocative_weight * provocativeness +
                     recency_weight * recency_score) * engagement_boost

        Args:
            post: The post to score
            current_round: Current simulation round

        Returns:
            Visibility score (0.0 to ~2.0, can exceed 1.0 for viral content)
        """
        # Recency decay: newer posts score higher
        rounds_old = max(0, current_round - post.round_num)
        recency_score = 1.0 / (1.0 + rounds_old * 0.25)

        # Base visibility from content features
        base_visibility = (
            self.emotion_weight * post.emotional_intensity +
            self.provocative_weight * post.provocativeness +
            self.recency_weight * recency_score
        )

        # Engagement boost: highly engaging content gets exponential amplification
        # This is the key feedback mechanism that advantages provocative content
        engagement = post.engagement_potential()
        engagement_boost = 1.0 + (engagement ** 2) * 0.6

        # Small random factor (algorithmic noise)
        noise = random.uniform(0.95, 1.05)

        return base_visibility * engagement_boost * noise

    def rank_feed(self, posts: List[Post], current_round: int) -> List[Post]:
        """
        Rank all posts by visibility score.

        Args:
            posts: List of posts to rank
            current_round: Current simulation round

        Returns:
            Posts sorted by visibility (highest first)
        """
        for post in posts:
            post.visibility_score = self.compute_visibility(post, current_round)

        return sorted(posts, key=lambda p: p.visibility_score, reverse=True)

    def sample_visible_posts(
        self,
        posts: List[Post],
        current_round: int,
        sample_size: int = 8
    ) -> List[Post]:
        """
        Sample posts for an agent's feed, weighted by visibility.

        Higher visibility = higher probability of being seen.
        This models the algorithmic curation of social media feeds.

        Args:
            posts: All available posts
            current_round: Current round
            sample_size: How many posts to show

        Returns:
            Sampled posts (weighted by visibility)
        """
        if not posts:
            return []

        if len(posts) <= sample_size:
            return posts

        # Compute visibility scores
        ranked = self.rank_feed(posts, current_round)

        # Weighted sampling without replacement
        weights = [p.visibility_score + 0.1 for p in ranked]  # +0.1 floor
        selected = []
        remaining = list(zip(ranked, weights))

        for _ in range(min(sample_size, len(remaining))):
            total = sum(w for _, w in remaining)
            if total <= 0:
                break

            r = random.random() * total
            cumsum = 0
            for i, (post, weight) in enumerate(remaining):
                cumsum += weight
                if r <= cumsum:
                    selected.append(post)
                    remaining.pop(i)
                    break

        return selected


def compute_opinion_influence(
    post: Post,
    reader_position: float,
    source_trust: float
) -> Tuple[float, float, bool]:
    """
    Compute how a post influences a reader's opinion.

    Args:
        post: The post being read
        reader_position: Reader's current opinion position
        source_trust: Reader's trust in the post author

    Returns:
        Tuple of (influence_direction, influence_strength, is_contrarian_source)
    """
    # Infer post's position from content characteristics
    # High provocativeness suggests contrarian position
    # High consensus orientation suggests mainstream position
    if post.provocativeness > 0.5 and post.provocativeness > post.consensus_orientation:
        post_position = -0.7 - (post.provocativeness * 0.3)  # More provocative = more extreme
        is_contrarian = True
    elif post.consensus_orientation > 0.5:
        post_position = 0.5 + (post.consensus_orientation * 0.3)
        is_contrarian = False
    else:
        # Mixed/neutral post
        post_position = 0.0
        is_contrarian = False

    # Direction of influence (toward post's position)
    influence_direction = post_position - reader_position

    # Strength based on:
    # - Emotional intensity (emotional arguments are more persuasive short-term)
    # - Logical coherence (rational arguments are more persuasive long-term)
    # - Visibility/repetition effect
    emotional_persuasion = post.emotional_intensity * 0.4
    logical_persuasion = post.logical_coherence * 0.3
    visibility_effect = min(post.visibility_score, 1.0) * 0.3

    influence_strength = emotional_persuasion + logical_persuasion + visibility_effect

    return influence_direction, influence_strength, is_contrarian


def analyze_amplification_bias(posts: List[Post]) -> dict:
    """
    Analyze whether the algorithm shows bias toward certain content.

    Compares average visibility of contrarian vs consensus posts.

    Args:
        posts: All posts from simulation

    Returns:
        Dict with bias analysis metrics
    """
    contrarian_posts = [p for p in posts if p.provocativeness > 0.5]
    consensus_posts = [p for p in posts if p.consensus_orientation > 0.5]
    neutral_posts = [p for p in posts if p.provocativeness <= 0.5 and p.consensus_orientation <= 0.5]

    def avg_visibility(post_list):
        if not post_list:
            return 0.0
        return sum(p.visibility_score for p in post_list) / len(post_list)

    contrarian_avg = avg_visibility(contrarian_posts)
    consensus_avg = avg_visibility(consensus_posts)
    neutral_avg = avg_visibility(neutral_posts)

    # Calculate bias ratio
    if consensus_avg > 0:
        bias_ratio = contrarian_avg / consensus_avg
    else:
        bias_ratio = float('inf') if contrarian_avg > 0 else 1.0

    return {
        "contrarian_posts_count": len(contrarian_posts),
        "consensus_posts_count": len(consensus_posts),
        "neutral_posts_count": len(neutral_posts),
        "contrarian_avg_visibility": contrarian_avg,
        "consensus_avg_visibility": consensus_avg,
        "neutral_avg_visibility": neutral_avg,
        "bias_ratio": bias_ratio,  # >1 means contrarian content is amplified more
        "interpretation": (
            "Strong contrarian amplification" if bias_ratio > 1.5 else
            "Moderate contrarian amplification" if bias_ratio > 1.2 else
            "Roughly balanced" if 0.8 <= bias_ratio <= 1.2 else
            "Consensus content amplified more"
        )
    }
