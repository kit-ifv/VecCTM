import math

import numpy as np

from traffic.SimulationInterface import SimulationInterface
from traffic.oo.cell_transmission_model import Cell, BorderInCell, Link, MergeLink, DivergeLink, Segment, BorderOutCell, \
    flatten
from resources import Settings
import logging


# Network class for sequential simulation
class NetworkSeq(SimulationInterface):
    counter_cells = -1

    # function to get the next id of the cells
    @staticmethod
    def get_next_id():
        NetworkSeq.counter_cells += 1
        return NetworkSeq.counter_cells

    def __init__(self, yaml_input):
        self.results = {}
        self.cells = []
        self.links = []
        self.segments = []
        self.border_cells = []
        self.second_simulate = 0
        self.timesteps_to_simulate = Settings.STEPS * Settings.INTERVAL
        self.simstep = 0
        self.import_yaml_network(yaml_input)

    # function to build the links between the segments
    def build_links(self):
        links = []
        for segment in self.segments:
            if segment.predecessors and len(segment.predecessors) == 2:
                links.append(MergeLink(Segment.get_segment(segment.predecessors[0]).last_cell,
                                       segment.first_cell,
                                       Segment.get_segment(segment.predecessors[1]).last_cell,
                                       0.50,
                                       0.50
                                       ))
            if segment.successors and len(segment.successors) == 2:
                links.append(DivergeLink(segment.last_cell,
                                         Segment.get_segment(segment.successors[0]).first_cell,
                                         Segment.get_segment(segment.successors[1]).first_cell,
                                         0.50,
                                         0.50
                                         )
                             )
            if segment.successors and len(segment.successors) == 1 and len(
                    Segment.get_segment(segment.successors[0]).predecessors) == 1:
                links.append(Link(segment.last_cell, Segment.get_segment(segment.successors[0]).first_cell))
        return links

    # function use to create the cells of a segment
    def create_segment_cells(self, id, values: dict):
        predecessor = values.pop("predecessor")
        successor = values.pop("successor")
        segment = Segment(id, predecessors=predecessor, successors=successor)
        cells = []
        segment_length = values.pop("length")
        if "name" in values.keys():
            values.pop("name")  # just for human readability in generated yaml files
        velo_free = values["velocity_free"]
        cell_length = (velo_free / 3.6) * Settings.TIME_STEP
        cell_count = int(math.ceil(segment_length / cell_length))

        first: Cell

        if not predecessor:
            first = BorderInCell(cell_id=NetworkSeq.get_next_id(), length=cell_length, **values)
            self.border_cells.append(first)
            values.pop("border_flow")
        else:
            first = Cell(cell_id=NetworkSeq.get_next_id(), length=cell_length, **values)
        segment.first_cell = first
        cells.append(segment.first_cell)
        prev = first
        for i in range(1, cell_count - 1):
            cell = Cell(cell_id=NetworkSeq.get_next_id(), length=cell_length, **values)
            cells.append(cell)
            self.links.append(Link(prev, cell))
            prev = cell

        # last cell
        if not successor:
            # BorderOutCell
            cell = BorderOutCell(cell_id=NetworkSeq.get_next_id(), length=cell_length, **values)
        else:
            cell = Cell(cell_id=NetworkSeq.get_next_id(), length=cell_length, **values)
        self.links.append(Link(prev, cell))
        cells.append(cell)
        segment.last_cell = cell

        flatten_cells = flatten(cells)
        segment.cells = flatten_cells
        self.segments.append(segment)
        self.cells.extend(flatten_cells)
        return segment

    def get_results_dict(self):
        results = {}

        pass  # TODO: implement

    def get_results_np(self):
        pass

    def get_segments(self):
        segments_dict = {}
        for segment in self.segments:
            log = []
            for cell in segment.cells:
                log = np.vstack((log, cell.log['vehicles']))
            segments_dict[segment.segment_id] = {self.LOG: [cell.log for cell in segment.cells],
                                                 self.PREDECESSORS: segment.predecessors,
                                                 self.SUCCESSORS: segment.successors,
                                                 self.MAX_VEHICLE: [cell.max_vehicle for cell in segment.cells],
                                                 self.LANES: [cell.lane for cell in segment.cells]
                                                 }
        return sorted(segments_dict.items())

    def import_yaml_network(self, yaml_input):
        yaml_segments = yaml_input[Settings.YAML_SEGMENT]
        if (yaml_segments):
            all_segments = []
            isconverted = False
            logging.info("Start of yml to object conversion!")
            try:
                for key, values in yaml_segments.items():
                    self.create_segment_cells(key, values)
                isconverted = True
            except IndexError as ex:
                isconverted = False
                logging.error(ex, "Index in yml file list is not correct! A list is too big!")
            if isconverted:
                logging.info("Convertion successful!")
            self.build_links()

        else:
            logging.warning("No segments given!")

    # function use to simulate the network
    def simulate(self):
        while self.second_simulate < self.timesteps_to_simulate:
            if self.second_simulate % Settings.INTERVAL == 0:
                self.simstep += 1
                print("Simulating t = ", self.simstep)
                var2 = list(map(lambda cell: cell.next_simstep(self.simstep), self.cells))
            if self.second_simulate % Settings.LOGGING_INTERVAL == 0:
                var3 = list(
                    map(lambda cell: cell.log_timestep(self.second_simulate / Settings.LOGGING_INTERVAL), self.cells))

            # var2 = list(map(lambda cell: cell.log_timestep(self.second_simulate), self.cells))
            linkflow = list(map(lambda link: link.calc_flows(), self.links))
            linkvehi = list(map(lambda cell: cell.alter_vehicles(), self.cells))

            self.second_simulate += Settings.TIME_STEP
        print("Simulation finished!")

    @staticmethod
    def get_name():
        return "Object Orientation Sequential"

    def __str__(self):
        return self.get_name()


# This function plots the results
def show_results():
    Segment.plot_every_segment()


def save_result_plot():
    if Settings.SHOW_PLOTS:  # if plots are shown, they are saved while showing
        return
    for segment in Segment.segments.values():
        fig = segment.plot_heatmap_timesteps()


if __name__ == '__main__':
    main()
