"""
Opinion Dynamics Simulation

An agent-based model simulating how contrarian vs consensus opinions
spread in a social network with algorithmic amplification.

Example:
    from opinion_dynamics.simulation import SimulationEngine
    from opinion_dynamics.models import SimulationConfig

    config = SimulationConfig(num_rounds=50)
    engine = SimulationEngine(config, api_key="sk-...")
    tracker = engine.run_simulation()
"""

from .models import (
    Agent,
    AgentRole,
    Post,
    Opinion,
    OpinionType,
    EmotionalState,
    SimulationConfig,
    ConversionEvent
)
from .simulation import SimulationEngine
from .tracking import SimulationTracker

__version__ = "1.0.0"
__all__ = [
    "Agent",
    "AgentRole",
    "Post",
    "Opinion",
    "OpinionType",
    "EmotionalState",
    "SimulationConfig",
    "ConversionEvent",
    "SimulationEngine",
    "SimulationTracker"
]
