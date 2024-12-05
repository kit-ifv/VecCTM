import logging
import math
import os
from abc import abstractmethod
from datetime import datetime
from statistics import median

import pandas as pd
from matplotlib import pyplot as plt
import numpy as np

import visualize.IVisualize
from resources import Settings, ListMethods
from traffic.SimulationInterface import SimulationInterface


class VectorCTM(SimulationInterface, visualize.IVisualize.IVisualizeGraph, visualize.IVisualize.IVisualizeHeatmap):
    FIRST = "first"
    LAST = "last"
    border_flow = []
    current_border_flow = []
    cells = []
    adjacent_matrix = []
    segment_map = {}
    lanes = []
    velo = []
    flow = []
    max_flow = []
    delta = []
    max_veh = []
    receive = []
    send = []
    merge_percentage = []
    log = []
    sim_step = 0
    csv_path = ""



    def __init__(self, segments):
        super().__init__(segments)
        self.create_adjacent_matrix()
        self.results = {}

        self.border_flow = np.array(self.border_flow) / 3600
        self.cells = np.array(self.cells)
        self.lanes = np.array(self.lanes)
        self.velo = np.array(self.velo)
        self.flow = np.array(self.flow)
        self.max_flow = np.array(self.max_flow) / 3600
        self.delta = np.array(self.delta)  # veh/h -> veh/s
        self.max_veh = np.array(self.max_veh)
        self.merge_percentage = np.zeros(len(self.cells))
        self.receive = np.array(self.receive)
        self.send = np.array(self.send)
        self.current_border_flow = np.minimum(self.border_flow[:, self.sim_step], self.receive)
        self.init_flows()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # get current working directory
        subdirectory = 'vector/'  # specify the subdirectory
        directory = os.path.join(os.getcwd(), self.settings.RESULT_PATH + subdirectory)
        os.makedirs(directory, exist_ok=True)
        self.csv_path = os.path.join(directory, f'{timestamp}.csv')
        # updated_data = np.vstack((np.transpose(self.cells), np.transpose(self.cells)))
        # np.savetxt(self.csv_path, self.cells, delimiter=';')

    def mid(a, b, c):
        return median([a, b, c])

    def sim_log(self):
        self.log.append(self.cells)

    def init_flows(self):
        pass
    def import_yaml_network(self, segments):
        logging.info("Start of yml to object conversion!")
        for key, values in segments.items():
            try:
                self.create_segment_cells(key, values)

            except IndexError as ex:
                logging.error(ex, "Index in yml file list is not correct! A list is too big!")
        self.print_segment_map()
        logging.info("Finalized Conversion!")
        return self

    def create_segment_cells(self, key, values: dict):
        index = len(self.cells)
        segment_length = values.pop("length")
        velo_free = values["velocity_free"]
        cell_length = (velo_free / 3.6) * self.settings.TIME_STEP
        cell_count = math.ceil(segment_length / cell_length)
        self.segment_map[key] = {}
        self.segment_map[key][self.FIRST] = index
        self.segment_map[key][self.PREDECESSORS] = values['predecessor']
        self.segment_map[key][self.SUCCESSORS] = values['successor']
        self.segment_map[key][self.LAST] = index + cell_count - 1

        for i in range(0, cell_count):
            total_index = index + i
            self.cells.append(0.0)
            self.lanes.append(values['lanes'])
            self.velo.append(values['velocity_free'] / 3.6)
            self.max_flow.append(self.settings.FLOW_PER_LANE * self.lanes[total_index])
            self.max_veh.append(cell_length * self.lanes[total_index] / self.settings.CAR_LENGTH)
            self.delta.append(self.settings.WAVE_COEFFICIENT / (values['velocity_free'] / 3.6))
            self.send.append(min(self.max_flow[total_index], self.cells[total_index]))
            self.receive.append(min(self.max_flow[total_index],
                                    self.delta[total_index] * (self.max_veh[total_index] - self.cells[total_index])))
            self.flow.append(0.0)

            # set border flow
            if i == 0:
                if 'border_flow' in values.keys():
                    self.border_flow.append(ListMethods.__fill_slots__(values['border_flow']))
                else:
                    self.border_flow.append([0] * self.settings.STEPS)

            else:
                self.border_flow.append([0] * self.settings.STEPS)

    def get_results_dict(self):
        if self.results:
            return self.results
        self.results = {}
        np_log = np.array(self.log)
        for time_step in range(0, len(self.log)):
            self.results[time_step] = {}
            for key, segment in self.segment_map.items():
                self.results[time_step][key] = {
                    self.VEHICLES: np_log[time_step, segment[self.FIRST]:segment[self.LAST]],
                    self.PREDECESSORS: segment[self.PREDECESSORS],
                    self.SUCCESSORS: segment[self.SUCCESSORS],
                    self.MAX_VEHICLE: sum(self.max_veh[segment[self.FIRST]:segment[self.LAST]])}
        return self.results

    def get_results_np(self):
        return np.array(self.log)

    def get_segments(self):
        segments = {}
        np_log = np.array(self.log)
        for key, segment in self.segment_map.items():
            segments[key] = {self.LOG: np_log[:, segment[self.FIRST]:segment[self.LAST]],
                             self.PREDECESSORS: segment[self.PREDECESSORS],
                             self.SUCCESSORS: segment[self.SUCCESSORS],
                             self.MAX_VEHICLE: self.max_veh[segment[self.FIRST]:segment[self.LAST]],
                             self.LANES: self.lanes[segment[self.FIRST]:segment[self.LAST]]}
        return segments




    def save_results(self):
        print("Saving results to: ", self.csv_path)
        np.savetxt(self.csv_path, self.log, delimiter=';')
        print("Log saved to: ", self.csv_path)

    # updates the vehiclenumber in each cell
    def calc_cells(self):
        self.cells = self.cells + self.adjacent_matrix.dot(self.flow) - self.flow + self.current_border_flow


    # calculates the sending flow capacity for each cell
    def calc_send(self):
        self.send = np.minimum(self.cells, self.max_flow)

    # calculates the receiving flow capacity for each cell
    def calc_receive(self):
        self.receive = np.maximum(np.minimum(self.max_flow, self.delta * (self.max_veh - self.cells)),
                                  np.zeros(len(self.cells)))

    def update_border_flow(self):
        self.current_border_flow = np.minimum(self.border_flow[:, self.sim_step - 1], self.receive)

    @abstractmethod
    def create_adjacent_matrix(self):
        self.adjacent_matrix = np.zeros((len(self.cells), len(self.cells)))
        pass

    @abstractmethod
    def calc_flows(self):
        pass

    @abstractmethod
    def simulate(self):
        for second in range(0, self.settings.STEPS * self.settings.INTERVAL):
            self.second = second
            # print("Receive", receive)
            # print("Send", send)
            # print("second", second)
            if second % self.settings.INTERVAL == 0:

                self.sim_step += 1
                print("Simulating t = ", self.sim_step)
            if second % self.settings.LOGGING_INTERVAL == 0:
                self.sim_log()

            self.calc_flows()
            self.calc_cells()
            self.calc_send()
            self.calc_receive()
            self.update_border_flow()

    def print_segment_map(self):
        # for key in self.segment_map.keys():
        #     print(f"Segment {key}: First: {self.segment_map[key][self.FIRST]} Last: {self.segment_map[key][self.LAST]}")
        print(f"Total Cells: {len(self.cells)}")

    def visualize_graph(self):
        pass

    def visualize_heatmap(self):
        data = pd.DataFrame(self.get_results_np())
        print(data)
        # fig = plt.figure()
        # ax = fig.add_subplot(111, projection='3d')
        x, y, z, xticks, yticks = self.plottable_3d_info(data)

        ### Set up axes and put data on the surface.
        fig = plt.figure()
        axes = fig.add_subplot(projection='3d')
        surf = axes.plot_surface(x, y, z)
        #fig.colorbar(surf, shrink=0.5, aspect=5)

        ### Customize labels and ticks (only really necessary with
        ### non-numeric axes).
        axes.set_xlabel('Cells')
        axes.set_ylabel('Timesteps')
        axes.set_zlabel('traffic volume')
        axes.set_zlim3d(bottom=0)

        plt.xticks(**xticks)
        plt.yticks(**yticks)
        fig.savefig('heatmap.pdf', format='pdf')

        plt.show()

    def plottable_3d_info(self, df: pd.DataFrame):
        """
        Transform Pandas data into a format that's compatible with
        Matplotlib's surface and wireframe plotting.
        """
        index = df.index
        columns = df.columns

        x, y = np.meshgrid(np.arange(len(columns)), np.arange(len(index)))
        z = np.array([[df[c][i] for c in columns] for i in index])

        xticks = dict(ticks=np.arange(len(columns)), labels=columns)
        yticks = dict(ticks=np.arange(len(index)), labels=index)

        return x, y, z, xticks, yticks