from abc import ABC, abstractmethod

import pandas as pd



class IVisualizeHeatmap(ABC):
    @abstractmethod
    def visualize_heatmap(self) -> None:
        pass

class IVisualizeGraph(ABC):
    @abstractmethod
    def visualize_graph(self) -> None:
        pass