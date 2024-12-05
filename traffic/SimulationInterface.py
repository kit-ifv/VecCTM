import logging
from abc import abstractmethod

from resources import Settings, YAMLImport


class SimulationInterface:
    MAX_VEHICLE = "max_vehicle"
    LOG = "log"
    PREDECESSORS = "predecessors"
    SUCCESSORS = "successors"
    LANES = "lanes"
    VEHICLES = "vehicles"

    def __init__(self, segments):
        self.results_np = None
        self.results_dict = {}
        self.settings = Settings.get_settings()
        self.import_yaml_network(segments)

    @abstractmethod
    def simulate(self):
        pass

    @abstractmethod
    def import_yaml_network(self, yaml_input):
        if not yaml_input:
            logging.error("No Input given!")
            return
        return

    @abstractmethod
    @DeprecationWarning
    def get_results_dict(self):
        # result_dict should be in this form:
        # results = {timestep: {segment_id: {vehicles: [list of vehicle numbers], predecessors: [list], successors: [list], max_vehicle: int}}
        return self.results_dict

    '''
    result_np should be in this form:
    results = [[c1(0), c2(0),..., cn-1(0), cn(0)],[c1(1), c2(1),..., cn-1(1), cn(1)] ...]
                timestep 1                         timestep 2
    '''

    @abstractmethod
    @DeprecationWarning
    def get_results_np(self):
        # result_np should be in this form:
        # results = [[c1(0), c2(0),..., cn-1(0), cn(0)],[c1(1), c2(1),..., cn-1(1), cn(1)] ...]
        return self.results_np

    '''
    returns segments as dict
    segments = {segment_id: {log: [list of cells log], predecessors: [list], successors: [list], max_vehicle: [list], lanes: [list]}
    '''
    @abstractmethod
    @DeprecationWarning
    def get_segments(self):
        pass

    @staticmethod
    def get_name():
        return "SimulationInterface"
