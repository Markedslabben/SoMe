"""
System Dynamics Model for Opinion Dynamics

Forrester-style System Dynamics implementation using scipy.integrate.odeint.
Models the interaction between algorithmic amplification and opinion formation.

Stocks:
- N: Neutral population
- C: Contrarian-converted population
- S: Consensus-converted population
- A: Aggregate arousal
- F: Frame adoption fraction

Feedback Loops:
- R1: Visibility-Arousal-Susceptibility (Reinforcing)
- R2: Framing Cascade (Reinforcing)
- R3: Population Shift (Reinforcing)
- B1: Arousal Decay (Balancing)
- B2: Pool Depletion (Balancing)
"""

import numpy as np
from scipy.integrate import odeint
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
import json

from sd_parameters import SDParameters, DEFAULT_PARAMS
from sd_equations import (
    exposure_fractions,
    susceptibility,
    arousal_increase_rate,
    arousal_decay_rate,
    conversion_rate_to_contrarian,
    conversion_rate_to_consensus,
    frame_adoption_change,
    visibility_contrarian,
    visibility_consensus,
)


@dataclass
class SDState:
    """Snapshot of system state at a point in time."""
    time: float
    neutrals: float
    contrarian_converts: float
    consensus_converts: float
    arousal: float
    frame_adoption: float

    # Derived quantities
    exposure_c: float = 0.0
    exposure_s: float = 0.0
    susceptibility: float = 0.0
    conversion_rate_c: float = 0.0
    conversion_rate_s: float = 0.0

    def to_dict(self) -> Dict:
        return {
            'time': self.time,
            'N': self.neutrals,
            'C': self.contrarian_converts,
            'S': self.consensus_converts,
            'A': self.arousal,
            'F': self.frame_adoption,
            'exposure_c': self.exposure_c,
            'exposure_s': self.exposure_s,
            'susceptibility': self.susceptibility,
        }


class OpinionDynamicsSD:
    """
    Forrester-style System Dynamics model of algorithmic amplification
    and opinion dynamics.

    Implements the causal structure identified in the agent-based simulation:
    - Algorithmic visibility bias (8.7x contrarian advantage)
    - Arousal-susceptibility feedback loop
    - Threshold dynamics at arousal ~0.93
    - Frame adoption cascade

    Example:
        params = SDParameters()
        model = OpinionDynamicsSD(params)
        results = model.run()
        model.plot_stocks()
    """

    def __init__(self, params: Optional[SDParameters] = None):
        """
        Initialize the System Dynamics model.

        Args:
            params: Model parameters. Uses defaults if not provided.
        """
        self.params = params or DEFAULT_PARAMS
        self.results: Optional[np.ndarray] = None
        self.time_points: Optional[np.ndarray] = None
        self.state_history: List[SDState] = []

    def initial_state(self) -> np.ndarray:
        """
        Get initial state vector.

        Returns:
            Array [N, C, S, A, F]
        """
        return np.array([
            self.params.initial_neutrals,      # N
            0.0,                                # C (converted)
            0.0,                                # S (converted)
            self.params.initial_arousal,       # A
            self.params.initial_frame_adoption # F
        ])

    def derivatives(self, state: np.ndarray, t: float) -> np.ndarray:
        """
        Calculate time derivatives for all stocks.

        This is the core of the system dynamics model, implementing
        all stock-flow relationships.

        Args:
            state: Current state vector [N, C, S, A, F]
            t: Current time (not used, system is autonomous)

        Returns:
            Array of derivatives [dN/dt, dC/dt, dS/dt, dA/dt, dF/dt]
        """
        # Unpack state
        N, C, S, A, F = state

        # Ensure non-negative stocks
        N = max(0, N)
        C = max(0, C)
        S = max(0, S)
        A = np.clip(A, 0, self.params.max_arousal)
        F = np.clip(F, 0, 1)

        # === Calculate auxiliaries ===

        # Exposure fractions (how much of each content type is seen)
        exp_c, exp_s = exposure_fractions(C, S, F, self.params)

        # === Calculate flows ===

        # Conversion flows
        conv_to_c = conversion_rate_to_contrarian(N, exp_c, A, self.params)
        conv_to_s = conversion_rate_to_consensus(N, exp_s, A, self.params)

        # Ensure conversions don't exceed available neutrals
        total_conv = conv_to_c + conv_to_s
        if total_conv > N and N > 0:
            scale = N / total_conv
            conv_to_c *= scale
            conv_to_s *= scale

        # Arousal flows
        arousal_up = arousal_increase_rate(exp_c, A, self.params)
        arousal_down = arousal_decay_rate(A, self.params)

        # Frame adoption flow
        frame_change = frame_adoption_change(F, exp_c, self.params)

        # === Calculate derivatives ===

        dN_dt = -conv_to_c - conv_to_s
        dC_dt = conv_to_c
        dS_dt = conv_to_s
        dA_dt = arousal_up - arousal_down
        dF_dt = frame_change

        return np.array([dN_dt, dC_dt, dS_dt, dA_dt, dF_dt])

    def run(
        self,
        t_final: Optional[float] = None,
        dt: Optional[float] = None,
        initial_state: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Run the system dynamics simulation.

        Args:
            t_final: End time (default: params.t_final)
            dt: Time step for output (default: params.dt)
            initial_state: Custom initial state (default: from params)

        Returns:
            Results array with shape (n_timesteps, 5)
        """
        t_final = t_final or self.params.t_final
        dt = dt or self.params.dt
        initial = initial_state if initial_state is not None else self.initial_state()

        # Create time points
        self.time_points = np.arange(0, t_final + dt, dt)

        # Integrate ODEs
        self.results = odeint(self.derivatives, initial, self.time_points)

        # Build state history with derived quantities
        self._build_state_history()

        return self.results

    def _build_state_history(self):
        """Build detailed state history with derived quantities."""
        self.state_history = []

        for i, t in enumerate(self.time_points):
            N, C, S, A, F = self.results[i]
            exp_c, exp_s = exposure_fractions(C, S, F, self.params)
            sus = susceptibility(A, self.params)
            conv_c = conversion_rate_to_contrarian(N, exp_c, A, self.params)
            conv_s = conversion_rate_to_consensus(N, exp_s, A, self.params)

            state = SDState(
                time=t,
                neutrals=N,
                contrarian_converts=C,
                consensus_converts=S,
                arousal=A,
                frame_adoption=F,
                exposure_c=exp_c,
                exposure_s=exp_s,
                susceptibility=sus,
                conversion_rate_c=conv_c,
                conversion_rate_s=conv_s,
            )
            self.state_history.append(state)

    def get_final_state(self) -> SDState:
        """Get the final state of the simulation."""
        if not self.state_history:
            raise RuntimeError("Run simulation first")
        return self.state_history[-1]

    def get_state_at_time(self, t: float) -> SDState:
        """Get state closest to specified time."""
        if not self.state_history:
            raise RuntimeError("Run simulation first")
        idx = int(t / self.params.dt)
        idx = min(idx, len(self.state_history) - 1)
        return self.state_history[idx]

    def find_threshold_crossing(self) -> Optional[float]:
        """
        Find the time when arousal first crosses the threshold.

        Returns:
            Time of threshold crossing, or None if never crossed
        """
        if not self.state_history:
            raise RuntimeError("Run simulation first")

        for state in self.state_history:
            if state.arousal >= self.params.threshold_arousal:
                return state.time
        return None

    def get_summary(self) -> Dict:
        """
        Get summary statistics of the simulation.

        Returns:
            Dictionary with key metrics
        """
        if not self.state_history:
            raise RuntimeError("Run simulation first")

        final = self.get_final_state()
        threshold_time = self.find_threshold_crossing()

        # Find peak arousal
        peak_arousal = max(s.arousal for s in self.state_history)
        peak_arousal_time = next(
            s.time for s in self.state_history if s.arousal == peak_arousal
        )

        return {
            'initial': {
                'neutrals': self.params.initial_neutrals,
                'arousal': self.params.initial_arousal,
            },
            'final': {
                'neutrals': final.neutrals,
                'contrarian_converts': final.contrarian_converts,
                'consensus_converts': final.consensus_converts,
                'arousal': final.arousal,
                'frame_adoption': final.frame_adoption,
            },
            'dynamics': {
                'threshold_crossing_time': threshold_time,
                'peak_arousal': peak_arousal,
                'peak_arousal_time': peak_arousal_time,
                'visibility_ratio': self.params.visibility_ratio,
            },
            'conversion_rates': {
                'to_contrarian_pct': (final.contrarian_converts /
                                      self.params.initial_neutrals * 100),
                'to_consensus_pct': (final.consensus_converts /
                                     self.params.initial_neutrals * 100),
            },
            'parameters': self.params.to_dict(),
        }

    def to_dataframe(self):
        """
        Convert results to pandas DataFrame.

        Returns:
            DataFrame with all state variables over time
        """
        import pandas as pd

        if not self.state_history:
            raise RuntimeError("Run simulation first")

        data = [s.to_dict() for s in self.state_history]
        return pd.DataFrame(data)

    def save_results(self, filepath: str):
        """Save simulation results to JSON."""
        summary = self.get_summary()
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)

    def validate_conservation(self) -> bool:
        """
        Verify that population is conserved (N + C + S = constant).

        Returns:
            True if conservation holds within tolerance
        """
        if self.results is None:
            raise RuntimeError("Run simulation first")

        initial_total = self.params.initial_neutrals
        tolerances = []

        for i in range(len(self.time_points)):
            N, C, S, _, _ = self.results[i]
            current_total = N + C + S
            tolerances.append(abs(current_total - initial_total))

        max_error = max(tolerances)
        return max_error < 0.01  # 1% tolerance


def compare_with_abm(sd_results: Dict, abm_results: Dict) -> Dict:
    """
    Compare System Dynamics results with Agent-Based Model results.

    Args:
        sd_results: Summary from SD model
        abm_results: Results from agent-based simulation

    Returns:
        Comparison metrics
    """
    return {
        'contrarian_converts': {
            'SD': sd_results['final']['contrarian_converts'],
            'ABM': abm_results.get('to_contrarian', 12),
            'match': abs(sd_results['final']['contrarian_converts'] -
                        abm_results.get('to_contrarian', 12)) < 2,
        },
        'consensus_converts': {
            'SD': sd_results['final']['consensus_converts'],
            'ABM': abm_results.get('to_consensus', 0),
            'match': abs(sd_results['final']['consensus_converts'] -
                        abm_results.get('to_consensus', 0)) < 1,
        },
        'threshold_time': {
            'SD': sd_results['dynamics']['threshold_crossing_time'],
            'ABM': abm_results.get('threshold_round', 46),
        },
    }


if __name__ == "__main__":
    # Run demonstration
    print("Opinion Dynamics System Dynamics Model")
    print("=" * 60)

    # Create and run model
    model = OpinionDynamicsSD()
    model.run()

    # Print summary
    summary = model.get_summary()

    print("\nFinal State:")
    print(f"  Neutrals remaining: {summary['final']['neutrals']:.1f}")
    print(f"  Converted to contrarian: {summary['final']['contrarian_converts']:.1f}")
    print(f"  Converted to consensus: {summary['final']['consensus_converts']:.1f}")
    print(f"  Final arousal: {summary['final']['arousal']:.3f}")
    print(f"  Frame adoption: {summary['final']['frame_adoption']:.3f}")

    print("\nDynamics:")
    print(f"  Threshold crossing: t={summary['dynamics']['threshold_crossing_time']}")
    print(f"  Peak arousal: {summary['dynamics']['peak_arousal']:.3f} at t={summary['dynamics']['peak_arousal_time']}")
    print(f"  Visibility ratio: {summary['dynamics']['visibility_ratio']:.2f}x")

    print("\nConversion Rates:")
    print(f"  To contrarian: {summary['conversion_rates']['to_contrarian_pct']:.1f}%")
    print(f"  To consensus: {summary['conversion_rates']['to_consensus_pct']:.1f}%")

    print("\nConservation check:", "PASSED" if model.validate_conservation() else "FAILED")

    # Compare with ABM results
    abm_results = {
        'to_contrarian': 12,
        'to_consensus': 0,
        'threshold_round': 46,
    }
    comparison = compare_with_abm(summary, abm_results)
    print("\nComparison with ABM:")
    print(f"  Contrarian converts: SD={comparison['contrarian_converts']['SD']:.1f}, "
          f"ABM={comparison['contrarian_converts']['ABM']} "
          f"({'MATCH' if comparison['contrarian_converts']['match'] else 'MISMATCH'})")
