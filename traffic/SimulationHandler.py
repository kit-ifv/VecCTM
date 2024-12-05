import enum
import linecache
import logging
import sys
import time
import yaml
from traffic.oo.networkseq import NetworkSeq
from traffic.vector.vector_flow import VectorizedFlow
from traffic.SimulationInterface import SimulationInterface

from resources.YAMLImport import NetworkYAMLImport


class SimulationType(enum.Enum):
    # VECTORIZED_FULL_MATRIX = VectorFullMatrix
    # VECTORIZED_SPARSE_MATRIX = VectorSparse
    VECTORIZED_VEC_FLOW = VectorizedFlow
    SEQUENTIAL = NetworkSeq

    # PARALLEL = NetworkPar
    @staticmethod
    def get_types():
        return [sim_type for sim_type in SimulationType]

    @staticmethod
    def get_type(type):
        return SimulationType[type]

    def __str__(self):
        return self.name

    def get_name(self):
        return self.name

    def get_simulation_class(self):
        return self.value


class SimulationHandler:
    is_simulating = False
    all_simulated = True

    @staticmethod
    def exec_simulations(simulation_types: list, yaml_file_path: str):
        all_ctm_simulations = []
        SimulationHandler.is_running = True

        for simulation_type in simulation_types:
            try:
                ctm_simulation_class = simulation_type.get_simulation_class()
                ctm_simulation = SimulationHandler.pre_simulation(ctm_simulation_class, yaml_file_path)
                all_ctm_simulations.append(ctm_simulation)
            except yaml.YAMLError as exc:
                SimulationHandler.print_exception()
                SimulationHandler.all_simulated = False
                return
            except Exception as e:
                SimulationHandler.print_exception()
                SimulationHandler.all_simulated = False
                return
            try:
                logging.info(f"Simulation of file {yaml_file_path} with {ctm_simulation.get_name()} started...")
                start = time.time()
                SimulationHandler.simulation(ctm_simulation)
                end = time.time()

                logging.info(f"Running time: {end - start:.2f} seconds")
                logging.info(f"Simulation of file {yaml_file_path} with {ctm_simulation.get_name()} finished.")
            except Exception as e:
                SimulationHandler.print_exception()
                SimulationHandler.all_simulated = False

            try:
                SimulationHandler.post_simulation(ctm_simulation)
            except Exception as e:
                SimulationHandler.print_exception()
                SimulationHandler.all_simulated = False

        SimulationHandler.is_running = False
        return all_ctm_simulations

    @staticmethod
    def is_running():

        return SimulationHandler.is_simulating

    @staticmethod
    def get_all_simulated():
        return SimulationHandler.all_simulated

    @staticmethod
    def pre_simulation(simulation_interface: SimulationInterface, yaml_file_path: str):
        logging.info(f"Preparing simulation with {simulation_interface.get_name()}")
        segments = NetworkYAMLImport(yaml_file_path).import_file()


        ctm_simulation = simulation_interface(segments)
        return ctm_simulation

    @staticmethod
    def simulation(ctm_simulation: SimulationInterface):
        ctm_simulation.simulate()

    @staticmethod
    def post_simulation(ctm_simulation: SimulationInterface):
        pass


    @staticmethod
    def print_exception():
        exc_type, exc_obj, tb = sys.exc_info()
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        logging.error(f"EXCEPTION IN ({filename}, LINE {lineno} '{line.strip()}'): {exc_obj}")
