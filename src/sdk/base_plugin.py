from abc import ABC, abstractmethod

class BasePlugin(ABC):
    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def generate(self, config, output_dir):
        """Generate configuration for specific OS"""
        pass