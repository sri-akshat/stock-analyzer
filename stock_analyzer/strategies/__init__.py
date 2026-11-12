from .base import Strategy
from .support_resistance import SupportResistanceStrategy
from .momentum import MomentumStrategy
from .mean_reversion import MeanReversionStrategy
from .composite import CompositeStrategy

# Registry: the name used in configs, CLI and the database -> class.
STRATEGIES = {
    s.name: s for s in (
        SupportResistanceStrategy,
        MomentumStrategy,
        MeanReversionStrategy,
        CompositeStrategy,
    )
}

__all__ = [
    "Strategy",
    "SupportResistanceStrategy",
    "MomentumStrategy",
    "MeanReversionStrategy",
    "CompositeStrategy",
    "STRATEGIES",
]
