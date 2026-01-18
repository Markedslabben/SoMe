"""
System Dynamics Equations Module

Auxiliary calculations for the Opinion Dynamics model.
Implements visibility, susceptibility, exposure, and flow calculations
based on the algorithmic amplification analysis.

Mathematical foundation:
- Visibility follows platform algorithm: (emotion*0.4 + provoc*0.4) * engagement^2
- Susceptibility increases with arousal (Elaboration Likelihood Model)
- Threshold dynamics model the mass conversion event at arousal ~0.93
"""

import numpy as np
from typing import Tuple
from sd_parameters import SDParameters


def visibility_contrarian(params: SDParameters) -> float:
    """
    Calculate contrarian content visibility score.

    Based on the amplification algorithm:
    visibility = (emotion_weight * emotion + provocative_weight * provocativeness)
                 * engagement_boost ^ exponent

    Returns:
        Contrarian visibility score
    """
    base_score = (params.emotion_weight * params.contrarian_emotion +
                  params.provocative_weight * params.contrarian_provocativeness)
    engagement_factor = params.contrarian_engagement_boost ** params.engagement_exponent
    return base_score * engagement_factor


def visibility_consensus(params: SDParameters) -> float:
    """
    Calculate consensus content visibility score.

    Consensus content scores much lower due to lower emotional intensity
    and provocativeness values.

    Returns:
        Consensus visibility score
    """
    base_score = (params.emotion_weight * params.consensus_emotion +
                  params.provocative_weight * params.consensus_provocativeness)
    engagement_factor = params.consensus_engagement_boost ** params.engagement_exponent
    return base_score * engagement_factor


def exposure_fractions(
    converted_C: float,
    converted_S: float,
    frame_adoption: float,
    params: SDParameters
) -> Tuple[float, float]:
    """
    Calculate exposure fractions for contrarian and consensus content.

    Exposure is proportional to:
    - Visibility of content type
    - Number of agents producing that content type
    - Secondary propagation from frame adoption (neutrals echoing contrarian frames)

    Args:
        converted_C: Number of neutrals converted to contrarian
        converted_S: Number of neutrals converted to consensus
        frame_adoption: Fraction of population using contrarian frames (0-1)
        params: Model parameters

    Returns:
        Tuple of (exposure_C, exposure_S) as fractions summing to ~1
    """
    vis_c = visibility_contrarian(params)
    vis_s = visibility_consensus(params)

    # Population producing each content type
    # Fixed advocates + converted neutrals
    # Frame adoption adds secondary propagation (neutrals echoing contrarian framing)
    pop_c = params.fixed_contrarians + converted_C
    pop_c_effective = pop_c * (1 + params.secondary_propagation * frame_adoption)

    pop_s = params.fixed_consensus + converted_S

    # Total visibility-weighted content production
    total_weighted = vis_c * pop_c_effective + vis_s * pop_s

    if total_weighted < 1e-10:
        # Avoid division by zero at initialization
        return 0.5, 0.5

    exposure_c = (vis_c * pop_c_effective) / total_weighted
    exposure_s = (vis_s * pop_s) / total_weighted

    return exposure_c, exposure_s


def susceptibility(arousal: float, params: SDParameters) -> float:
    """
    Calculate conversion susceptibility based on arousal level.

    Implements the Elaboration Likelihood Model insight:
    - Higher arousal → peripheral processing → higher susceptibility
    - Threshold effect at arousal > 0.93 triggers mass conversion

    Uses smooth threshold function to avoid discontinuities in ODE solver.

    Args:
        arousal: Current aggregate arousal level (0-1)
        params: Model parameters

    Returns:
        Susceptibility multiplier (>= base_susceptibility)
    """
    # Base susceptibility increases linearly with arousal
    base = params.base_susceptibility * (1 + params.arousal_amplifier * arousal)

    # Smooth threshold function (sigmoid)
    # When arousal > threshold, susceptibility jumps by threshold_multiplier
    threshold_effect = 1.0 + (params.threshold_multiplier - 1.0) * _smooth_threshold(
        arousal, params.threshold_arousal, params.threshold_smoothing
    )

    return base * threshold_effect


def _smooth_threshold(x: float, threshold: float, smoothing: float) -> float:
    """
    Smooth approximation of step function for numerical stability.

    Uses logistic sigmoid: 1 / (1 + exp(-(x - threshold) / smoothing))

    Args:
        x: Input value
        threshold: Threshold value
        smoothing: Smoothing parameter (smaller = sharper transition)

    Returns:
        Value between 0 and 1
    """
    z = (x - threshold) / smoothing
    # Clip to avoid overflow
    z = np.clip(z, -50, 50)
    return 1.0 / (1.0 + np.exp(-z))


def arousal_increase_rate(
    exposure_c: float,
    arousal: float,
    params: SDParameters
) -> float:
    """
    Calculate rate of arousal increase from provocative content exposure.

    Arousal increases when population is exposed to provocative content.
    Rate is bounded by (1 - arousal) to prevent exceeding max.

    Models emotional contagion: reading emotionally charged content
    elevates reader's emotional state.

    Args:
        exposure_c: Exposure fraction to contrarian content
        arousal: Current arousal level
        params: Model parameters

    Returns:
        Rate of arousal increase (dA/dt contribution)
    """
    # Arousal increase proportional to:
    # - Exposure to provocative content
    # - Provocativeness of that content
    # - Room to grow (1 - current arousal)
    return (params.arousal_contagion_rate *
            exposure_c *
            params.contrarian_provocativeness *
            (params.max_arousal - arousal))


def arousal_decay_rate(arousal: float, params: SDParameters) -> float:
    """
    Calculate natural arousal decay rate.

    Arousal decays proportionally to current level (exponential decay).
    Models natural "cooling off" when not actively provoked.

    Args:
        arousal: Current arousal level
        params: Model parameters

    Returns:
        Rate of arousal decay (dA/dt contribution, positive value)
    """
    return params.arousal_decay_rate * arousal


def conversion_rate_to_contrarian(
    neutrals: float,
    exposure_c: float,
    arousal: float,
    params: SDParameters
) -> float:
    """
    Calculate rate of neutral → contrarian conversion.

    Conversion rate depends on:
    - Available neutral population (pool to convert from)
    - Exposure to contrarian content
    - Susceptibility (function of arousal)

    Args:
        neutrals: Current neutral population
        exposure_c: Exposure fraction to contrarian content
        arousal: Current arousal level (affects susceptibility)
        params: Model parameters

    Returns:
        Rate of conversion to contrarian (dC/dt, -dN/dt contribution)
    """
    sus = susceptibility(arousal, params)
    # Normalize by total population for rate calculation
    return params.base_conversion_rate * sus * exposure_c * neutrals


def conversion_rate_to_consensus(
    neutrals: float,
    exposure_s: float,
    arousal: float,
    params: SDParameters
) -> float:
    """
    Calculate rate of neutral → consensus conversion.

    Note: High arousal actually reduces consensus conversion because
    peripheral processing favors simple emotional messages over
    nuanced consensus arguments.

    Args:
        neutrals: Current neutral population
        exposure_s: Exposure fraction to consensus content
        arousal: Current arousal level
        params: Model parameters

    Returns:
        Rate of conversion to consensus (dS/dt, -dN/dt contribution)
    """
    # Consensus conversion is REDUCED at high arousal
    # (central route processing requires low arousal)
    arousal_penalty = 1.0 / (1.0 + params.arousal_amplifier * arousal)
    sus = params.base_susceptibility * arousal_penalty

    return params.base_conversion_rate * sus * exposure_s * neutrals


def frame_adoption_change(
    frame_adoption: float,
    exposure_c: float,
    params: SDParameters
) -> float:
    """
    Calculate rate of change in contrarian frame adoption.

    Frames spread through exposure and are reinforced by existing adoption.
    Frame adoption represents linguistic/framing influence even before
    opinion conversion.

    Args:
        frame_adoption: Current frame adoption fraction (0-1)
        exposure_c: Exposure to contrarian content
        params: Model parameters

    Returns:
        Rate of frame adoption change (dF/dt)
    """
    # Adoption increases with exposure, bounded by (1 - F)
    # Secondary propagation means existing frame adoption increases exposure
    effective_exposure = exposure_c * (1 + params.secondary_propagation * frame_adoption)
    adoption_rate = params.frame_adoption_rate * effective_exposure * (1 - frame_adoption)

    # Natural decay of frames when not reinforced
    decay_rate = params.frame_decay_rate * frame_adoption

    return adoption_rate - decay_rate


if __name__ == "__main__":
    # Test equations with default parameters
    params = SDParameters()

    print("Equation Tests")
    print("=" * 50)

    # Visibility
    vis_c = visibility_contrarian(params)
    vis_s = visibility_consensus(params)
    print(f"Visibility contrarian: {vis_c:.4f}")
    print(f"Visibility consensus: {vis_s:.4f}")
    print(f"Visibility ratio: {vis_c/vis_s:.2f}x")
    print()

    # Exposure at t=0
    exp_c, exp_s = exposure_fractions(0, 0, 0, params)
    print(f"Initial exposure contrarian: {exp_c:.3f}")
    print(f"Initial exposure consensus: {exp_s:.3f}")
    print()

    # Susceptibility at different arousal levels
    print("Susceptibility by arousal:")
    for a in [0.3, 0.5, 0.7, 0.9, 0.95]:
        sus = susceptibility(a, params)
        print(f"  Arousal {a:.2f}: {sus:.3f}")
    print()

    # Conversion rates
    print("Conversion rates (20 neutrals, baseline exposure):")
    for a in [0.5, 0.9, 0.95]:
        rate_c = conversion_rate_to_contrarian(20, 0.8, a, params)
        rate_s = conversion_rate_to_consensus(20, 0.2, a, params)
        print(f"  Arousal {a:.2f}: to_C={rate_c:.3f}/t, to_S={rate_s:.4f}/t")
