"""Abstract plugin contract for configuration generators."""

from abc import ABC, abstractmethod


class BasePlugin(ABC):
    """Base class all platform plugins must implement."""

    def __init__(self):
        """Initialize common plugin metadata."""
        self.name = self.__class__.__name__

    @abstractmethod
    def generate(self, config: dict, output_dir: str) -> None:
        """Generate platform-specific configuration artifacts.

        Args:
            config: Plugin-ready internal configuration model.
            output_dir: Target directory where generated files are written.

        Returns:
            None. Implementations write generated files to ``output_dir``.
        """
        pass