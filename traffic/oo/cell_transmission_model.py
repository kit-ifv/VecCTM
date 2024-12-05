import os
from datetime import datetime
from statistics import median

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import mplcursors
from PyQt5.QtWidgets import QApplication, QTabWidget, QVBoxLayout, QWidget
import numpy as np

from resources import Settings, ListMethods


def mid(a, b, c):
    return median([a, b, c])


def flatten(lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(flatten(item))
        else:
            flat_list.append(item)
    return flat_list


class Cell:

    def __init__(self, cell_id, length, velocity_free, lanes = 3, wave_coef= Settings.get_settings().WAVE_COEFFICIENT,
                 vehicle_number=0.0):
        self.settings = Settings.get_settings()
        self.id = cell_id  # address of cell
        self.length = length  # length of cell in m
        self.lanes = ListMethods.__fill_slots__(lanes)  # number of lanes for every timestep
        self.lane = self.lanes[0]
        self.max_vehicle = length * self.lane / self.settings.CAR_LENGTH  # number of vehicle that fit in the cell, 6m is the length of a car
        self.velocity_free = velocity_free / 3.6  # free traffic velocity of vehicle
        self.link_in: Link = None
        self.link_out: Link = None
        self.flow_in = 0
        self.flow_out = 0
        self.max_flow = self.settings.FLOW_PER_LANE * self.lane / 3600  # max inflow of vehicles per hour. 1800 is the max flow of a lane
        self.wave_coef = self.settings.WAVE_COEFFICIENT
        self.delta = self.wave_coef / self.velocity_free
        self.vehicle_number = vehicle_number
        self.log = {}
        self.v = velocity_free
        self.flow = min(self.flow_in, self.flow_out, self.max_flow)

    def alter_vehicles(self):

        self.vehicle_number += (self.flow_in - self.flow_out)
        if self.vehicle_number < 0:
            self.vehicle_number = 0
        if self.vehicle_number > self.max_vehicle:
            self.vehicle_number = self.max_vehicle

    def get_send(self):
        return min(self.max_flow, self.vehicle_number)

    def get_recieve(self):
        # return self.max_inflow
        return min(self.max_flow, self.delta * (self.max_vehicle - self.vehicle_number))

    def set_flow_in(self, flow_in):
        self.flow_in = flow_in

    def set_flow_out(self, flow_out):
        self.flow_out = flow_out

    def get_flow(self):
        return min(self.flow_in, self.flow_out, self.max_flow)

    def log_timestep(self, timestep):
        self.log[timestep] = {"flow_in": self.flow_in, "flow_out": self.flow_out, "flow": self.get_flow(),
                              "vehicles": self.vehicle_number}

    def print_log(self):
        print("Log for Cell ", self.id)
        print("{:<8} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} |".format('Step', 'flow_in', 'flow_out', 'flow',
                                                                            'vehicles', 'max_vehicles'))
        for t in range(0, len(self.log)):
            flow_in, flow_out, flow, vehicles = self.log[t + 1].values()
            print("{:<8} | {:<10} | {:<10} | {:<10} | {:<10} | {:<10} |".format(t, flow_in, flow_out, flow,
                                                                                vehicles, self.max_vehicle))

    def get_log_vehicles_relative(self):
        log_vehicle = [(entry['vehicles'] * 100) / self.max_vehicle for entry in self.log.values()]
        # print(f" of cell {self.id}: Vehicles in percent: {log_vehicle}")
        return log_vehicle

    def get_log_vehicles_abs(self):
        log_vehicle = [entry['vehicles'] for entry in self.log.values()]
        return log_vehicle
    def get_log_flow(self):
        log_flow = [(entry['flow']) for entry in self.log.values()]
        # print(f" of cell {self.id}: Flow in percent: {log_flow}")
        return log_flow

    def get_vehicle_km(self):
        log_v_km = [(entry['vehicles'] * (1000 / self.length)) for entry in self.log.values()]
        return log_v_km

    def update_to_simstep(self, step):
        self.lane = self.lanes[step - 1]
        self.max_vehicle = self.length * self.lane / self.settings.CAR_LENGTH
        self.max_flow = self.settings.FLOW_PER_LANE * self.lane / 3600

    def next_simstep(self, step):
        self.update_to_simstep(step)
        # self.log_timestep(step)

    def __str__(self):
        return f"Cell {self.id}"
class BorderInCell(Cell):
    def __init__(self, border_flow, **kwargs):
        super().__init__(**kwargs)
        self.border_flow = ListMethods.__fill_slots__(border_flow)
        self.flow_in = min(self.border_flow[0] / 3600, self.max_flow)
        self.flow = self.get_flow()

    def update_to_simstep(self, step):
        super().update_to_simstep(step)
        self.flow_in = min((self.border_flow[step - 1]) / 3600, self.max_flow)  # flow in veh/s

    def __str__(self):
        return f"BorderInCell {self.id}"

class BorderOutCell(Cell):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.flow_out = self.max_flow

    def __str__(self):
        return f"BorderOutCell {self.id}"


class Link:
    def __init__(self, cell_in: Cell, cell_out: Cell):
        self.cell_in = cell_in
        self.cell_out = cell_out
        self.flow_k = 0
        self.cell_in.link_out = self
        self.cell_out.link_in = self

    def calc_flow(self):
        self.flow_k = min(self.cell_in.get_send(), self.cell_out.get_recieve())

    def calc_flows(self):

        self.calc_flow()
        self.cell_in.set_flow_out(self.flow_k)
        self.cell_out.set_flow_in(self.flow_k)

    def calc_vehicles(self):
        pass
        self.cell_in.alter_vehicles()
        self.cell_out.alter_vehicles()

    def get_out(self):
        return [self.cell_out]

    def __str__(self):
        return f"Ordinary Link from {self.cell_in.id} to {self.cell_out.id}"
class MergeLink(Link):
    def __init__(self, cell_in: Cell, cell_out: Cell, cell_comp: Cell, probability_ord, probability_comp):
        super().__init__(cell_in, cell_out)
        self.cell_comp = cell_comp
        self.flow_comp = 0
        self.probability_comp = probability_comp
        self.probability_ord = probability_ord
        self.cell_comp.link_out = self
        # print(cell_in.id, cell_out.id, cell_comp.id)

    def calc_flow(self):
        if not self.cell_out.get_recieve() <= (self.cell_in.get_send() + self.cell_comp.get_send()):
            self.flow_k = self.cell_in.get_send()
            self.flow_comp = self.cell_comp.get_send()
            return

        self.flow_k = mid(self.cell_in.get_send(),
                          self.cell_out.get_recieve() - self.cell_comp.get_send(),
                          self.probability_ord * self.cell_out.get_recieve()
                          )
        self.flow_comp = mid(self.cell_comp.get_send(),
                             self.cell_out.get_recieve() - self.cell_in.get_send(),
                             self.probability_comp * self.cell_out.get_recieve()
                             )

    def calc_vehicles(self):
        pass
        super().calc_vehicles()
        self.cell_comp.alter_vehicles()

    def calc_flows(self):

        self.calc_flow()
        self.cell_in.set_flow_out(self.flow_k)
        self.cell_comp.set_flow_out(self.flow_comp)
        self.cell_out.set_flow_in(self.flow_k + self.flow_comp)

    def __str__(self):
        return f"Merge Link from {self.cell_in.id} and {self.cell_comp.id} to {self.cell_out.id}"

class DivergeLink(Link):
    def __init__(self, cell_in: Cell, cell_out: Cell, cell_comp: Cell, probability_ord, probability_comp):
        super().__init__(cell_in, cell_out)
        self.cell_comp = cell_comp
        self.flow_comp = 0
        self.probability_comp = probability_comp
        self.probability_ord = probability_ord
        self.flow_tot = 0
        self.cell_comp.link_in = self

    def calc_flow(self):
        self.flow_tot = min(self.cell_in.get_send(), min(
                            self.cell_out.get_recieve() / self.probability_ord,
            self.cell_comp.get_recieve() / self.probability_comp))
        self.flow_k = self.probability_ord * self.flow_tot
        self.flow_comp = self.probability_comp * self.flow_tot

    def calc_flows(self):
        self.calc_flow()
        self.cell_in.set_flow_out(self.flow_tot)
        self.cell_out.set_flow_in(self.flow_k)
        self.cell_comp.set_flow_in(self.flow_comp)

    def calc_vehicles(self):
        pass
        super().calc_vehicles()
        self.cell_comp.alter_vehicles()

    def get_out(self):
        return [self.cell_out, self.cell_comp]

    def __str__(self):
        return f"Diverge Link from {self.cell_in.id} to {self.cell_out.id} and {self.cell_comp.id}"


class Segment:
    segments = {}

    def __init__(self, id, predecessors, successors):
        self.settings = Settings.get_settings()
        self.first_cell: Cell
        self.last_cell: Cell
        self.cells = []
        self.segment_id: int
        self.predecessors: [] = []
        self.successors: [] = []
        self.segment_id = id
        if predecessors:
            self.predecessors = list(predecessors)
        if successors:
            self.successors = list(successors)
        Segment.segments[id] = self
        #print(f"Segment {id} {predecessors} {successors}")

    @staticmethod
    def get_segment(id):
        return Segment.segments[id]

    @staticmethod
    def plot_every_segment():
        app = QApplication([])
        tabs = QTabWidget()
        for segment in Segment.segments.values():
            fig = segment.plot_heatmap_timesteps()
            canvas = FigureCanvas(fig)
            tab = QWidget()
            layout = QVBoxLayout(tab)
            layout.addWidget(canvas)
            tabs.addTab(tab, f"Segment {segment.segment_id}")
        tabs.setWindowTitle("Objects")
        tabs.show()
        app.exec_()

    @staticmethod
    def save_log():
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # get current working directory
        subdirectory = 'oo/'  # specify the subdirectory
        directory = os.path.join(os.getcwd(), Settings.get_settings().RESULT_PATH + subdirectory)
        os.makedirs(directory, exist_ok=True)
        csv_path = os.path.join(directory, f'{timestamp}.csv')
        print(f"Saving results to {csv_path}")
        array = np.empty([])

        for segment in Segment.segments.values():
            for cell in segment.cells:

                response = cell.get_log_vehicles_abs()
                # con = np.concatenate((np.array(cell.id), np.array(response)), axis=0)
                if array.size == 1:
                    array = np.array(response)
                else:
                    array = np.vstack((array, response))

        np.savetxt(csv_path, np.transpose(array), delimiter=';')
        print(f"Saved results to {csv_path}")

    def plot_heatmap_timesteps(self):

        log_vehicles = []

        for cell in self.cells:
            response = cell.get_vehicle_km()
            log_vehicles.append(response)
        log_data = np.array(log_vehicles)

        vmin = 0
        vmax = (1000 / self.settings.CAR_LENGTH) * self.first_cell.lane #1000m is a km. Density of cars per km

        # Create heatmap
        fig, ax = plt.subplots()
        heatmap = ax.imshow(log_data, cmap=plt.cm.Reds, vmin=vmin, vmax=vmax, aspect='auto')

        # Set axis labels
        fig.set_size_inches(10, 8)  # Set the size of the figure
        ax.set_xticks(np.arange(log_data.shape[1]) + 0.5)
        ax.set_yticks(np.arange(log_data.shape[0]) + 0.5)
        ax.set_xticklabels(range(log_data.shape[1]), fontsize=8)
        ax.set_yticklabels(range(log_data.shape[0]), fontsize=8)
        ax.xaxis.tick_top()
        # add title to plot
        plt.title(f'Heatmap of {self.segment_id}')
        # Add colorbar
        cbar = plt.colorbar(heatmap)

        # Add cursor tooltip to each cell
        mplcursors.cursor(heatmap, hover=True).connect(
            "add", lambda sel: sel.annotation.set_text(
                f'Timestep: {int(sel.target[0])}\nCell: {int(sel.target[1])}\nValue: {log_data[int(sel.target[1]), int(sel.target[0])]}'
            )
        )
        # check if directory exists
        if not os.path.exists(self.settings.RESULT_PATH + "oo\\"):
            os.makedirs(self.settings.RESULT_PATH + "oo\\")

        plt.savefig(
            self.settings.RESULT_PATH + "oo\\" + datetime.now().strftime("%Y%m%d-%H%M") + f"_Segment_{self.segment_id}.png")
        return fig
