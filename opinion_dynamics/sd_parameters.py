"""
System Dynamics Model Parameters

Calibrated parameters from the agent-based opinion dynamics simulation.
Based on Forrester's System Dynamics methodology.

Parameter sources:
- Population: Experiment design (1 contrarian, 4 consensus, 20 neutral)
- Content characteristics: Measured from simulation posts
- Dynamics: Calibrated to match observed conversion patterns
"""

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class SDParameters:
    """
    Parameters for the Opinion Dynamics System Dynamics model.

    All parameters are derived from or calibrated against the
    agent-based simulation results.
    """

    # === Population Parameters ===
    initial_neutrals: float = 20.0      # Starting neutral population
    fixed_contrarians: float = 1.0       # Fixed contrarian advocates (not converted)
    fixed_consensus: float = 4.0         # Fixed consensus advocates (not converted)
    initial_arousal: float = 0.47        # Initial aggregate arousal level
    initial_frame_adoption: float = 0.0  # Initial contrarian frame adoption

    # === Content Characteristics (measured from simulation) ===
    # Contrarian content properties
    contrarian_emotion: float = 0.58           # Avg emotional intensity
    contrarian_provocativeness: float = 0.54   # Avg provocativeness score
    contrarian_engagement_boost: float = 1.3   # Engagement multiplier

    # Consensus content properties
    consensus_emotion: float = 0.04            # Avg emotional intensity
    consensus_provocativeness: float = 0.03   # Avg provocativeness score
    consensus_engagement_boost: float = 1.0    # Engagement multiplier

    # === Algorithm Parameters ===
    emotion_weight: float = 0.4          # Weight of emotion in visibility
    provocative_weight: float = 0.4      # Weight of provocativeness
    recency_weight: float = 0.2          # Weight of recency (constant, cancels)
    engagement_exponent: float = 2.0     # Squared engagement boost

    # === Conversion Dynamics ===
    base_conversion_rate: float = 0.015  # Base conversion rate per time unit
    arousal_amplifier: float = 2.5       # How much arousal increases susceptibility
    base_susceptibility: float = 0.3     # Base susceptibility to conversion

    # === Threshold Dynamics (mass conversion trigger) ===
    threshold_arousal: float = 0.93      # Arousal level triggering mass conversion
    threshold_multiplier: float = 4.0    # Susceptibility multiplier above threshold
    threshold_smoothing: float = 0.05    # Smoothing for threshold transition

    # === Arousal Dynamics ===
    arousal_contagion_rate: float = 0.18  # Rate of arousal spread from exposure (tuned to match ABM peak)
    arousal_decay_rate: float = 0.012     # Natural arousal decay rate
    max_arousal: float = 1.0              # Maximum arousal level

    # === Frame Adoption Dynamics ===
    frame_adoption_rate: float = 0.06     # Rate of frame adoption
    frame_decay_rate: float = 0.008       # Rate of frame decay
    secondary_propagation: float = 0.4    # Boost from converted neutrals

    # === Simulation Settings ===
    t_final: float = 50.0                 # Final time (rounds)
    dt: float = 0.1                       # Time step for output

    @property
    def total_population(self) -> float:
        """Total initial population (should remain constant)."""
        return self.initial_neutrals + self.fixed_contrarians + self.fixed_consensus

    @property
    def visibility_ratio(self) -> float:
        """Calculate theoretical visibility ratio from content characteristics."""
        vis_c = (self.emotion_weight * self.contrarian_emotion +
                 self.provocative_weight * self.contrarian_provocativeness)
        vis_s = (self.emotion_weight * self.consensus_emotion +
                 self.provocative_weight * self.consensus_provocativeness)

        # Apply engagement boost
        vis_c *= self.contrarian_engagement_boost ** self.engagement_exponent
        vis_s *= self.consensus_engagement_boost ** self.engagement_exponent

        return vis_c / vis_s if vis_s > 0 else float('inf')

    def to_dict(self) -> Dict[str, Any]:
        """Convert parameters to dictionary for serialization."""
        return {
            'population': {
                'initial_neutrals': self.initial_neutrals,
                'fixed_contrarians': self.fixed_contrarians,
                'fixed_consensus': self.fixed_consensus,
                'initial_arousal': self.initial_arousal,
                'initial_frame_adoption': self.initial_frame_adoption,
            },
            'content': {
                'contrarian_emotion': self.contrarian_emotion,
                'contrarian_provocativeness': self.contrarian_provocativeness,
                'consensus_emotion': self.consensus_emotion,
                'consensus_provocativeness': self.consensus_provocativeness,
            },
            'algorithm': {
                'emotion_weight': self.emotion_weight,
                'provocative_weight': self.provocative_weight,
                'engagement_exponent': self.engagement_exponent,
            },
            'dynamics': {
                'base_conversion_rate': self.base_conversion_rate,
                'arousal_amplifier': self.arousal_amplifier,
                'threshold_arousal': self.threshold_arousal,
                'threshold_multiplier': self.threshold_multiplier,
            },
            'derived': {
                'total_population': self.total_population,
                'visibility_ratio': self.visibility_ratio,
            }
        }

    @classmethod
    def policy_reduced_bias(cls) -> 'SDParameters':
        """Policy scenario: Reduced algorithmic bias (visibility ratio ~2x)."""
        params = cls()
        # Reduce engagement boost and provocativeness weight
        params.contrarian_engagement_boost = 1.1
        params.provocative_weight = 0.2
        return params

    @classmethod
    def policy_cooling_off(cls) -> 'SDParameters':
        """Policy scenario: Mandatory cooling-off periods."""
        params = cls()
        params.arousal_decay_rate = 0.045  # 3x faster decay
        return params

    @classmethod
    def policy_friction(cls) -> 'SDParameters':
        """Policy scenario: Add friction before sharing provocative content."""
        params = cls()
        params.arousal_contagion_rate = 0.04  # Reduced spread
        params.frame_adoption_rate = 0.02     # Slower frame adoption
        return params


# Default calibrated parameters
DEFAULT_PARAMS = SDParameters()


if __name__ == "__main__":
    # Print parameter summary
    params = SDParameters()
    print("System Dynamics Model Parameters")
    print("=" * 50)
    print(f"Total population: {params.total_population}")
    print(f"Visibility ratio: {params.visibility_ratio:.2f}x")
    print(f"Threshold arousal: {params.threshold_arousal}")
    print()
    print("Initial state:")
    print(f"  Neutrals: {params.initial_neutrals}")
    print(f"  Arousal: {params.initial_arousal}")
    print(f"  Frame adoption: {params.initial_frame_adoption}")
