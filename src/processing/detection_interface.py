from abc import ABC, abstractmethod

class DetectionAlgorithm(ABC):
    @abstractmethod
    def detect(self, price):
        pass
