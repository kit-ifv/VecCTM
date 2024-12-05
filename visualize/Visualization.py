import logging
from datetime import datetime
from enum import Enum
import tkinter as tk
from tkinter import ttk

from resources.Settings import get_settings
from traffic.SimulationInterface import SimulationInterface
import numpy as np
from matplotlib import pyplot as plt
import networkx as nx
from resources import Settings


class VisualizationType(Enum):
    HEATMAP = "heatmap"
    GRAPHMAP = "graphmap"

    @staticmethod
    def get_types():
        return [vis_type for vis_type in VisualizationType]

    @staticmethod
    def get_type(type):
        return VisualizationType[type]

    def __str__(self):
        return self.name

    def get_name(self):
        return self.name


class Visualization:
    plots = {}

    @staticmethod
    def add_visualization_plot(simulation: SimulationInterface, plot):
        Visualization.plots.update({simulation.get_name(): plot})

    @staticmethod
    def clear_visualization_plots():
        Visualization.plots.clear()

    @staticmethod
    def save_results(simulation: SimulationInterface):
        logging.info("Saving results...")
        pass  # TODO: implement

    @staticmethod
    def show_results(simulation: SimulationInterface, type: VisualizationType, parentFrame):
        logging.info("Showing results...")
        print("TestVIZ")
        plot = None
        match type:
            case VisualizationType.HEATMAP:
                plot = Visualization.plot_heatmap_segments(simulation, parentFrame)
            case VisualizationType.GRAPHMAP:
                plot = Visualization.plot_graphmap_segments(simulation)
        Visualization.add_visualization_plot(simulation, plot)
        return
        # match type:
        #     case VisualizationType.HEATMAP:
        #         frame = tk.Frame()
        #         label = tk.Label(frame, text="Results HEATMAP")
        #         label.pack()
        #         return frame
        #         notebook = plot_heatmap_segments(simulation)
        #         return notebook
        #         return plot_heatmap_segments(simulation.get_results_dict())
        #     case VisualizationType.GRAPHMAP:
        #         frame = tk.Frame()
        #         label = tk.Label(frame, text="Results GRAPHMAP")
        #         label.pack()
        #         plot_graphmap_segments(simulation.get_results_dict(), frame)
        #         return frame

    @staticmethod
    def save_result_plots(simulation: SimulationInterface):
        logging.info("Saving result plots...")
        for plot in Visualization.plots:
            plot.savefig(Settings.RESULT_PATH + datetime.now().strftime("%Y%m%d-%H%M") + ".png")
        return

    @staticmethod
    def plot_graphmap_segments(simulation: SimulationInterface):
        results_dict = simulation.get_results_dict()
        traffic_network = Visualization.build_graph(results_dict)

        pos = nx.spectral_layout(traffic_network)
        plt.clf()
        fignum = plt.get_fignums()
        fig, axs = plt.subplots(1)
        fignum = plt.get_fignums()
        nx.draw(traffic_network, pos, with_labels=True, node_size=800, node_color='red', ax=axs)
        fignum = plt.get_fignums()
        ax.set_axis_off()
        # plt.draw()
        fignum = plt.get_fignums()
        plt.savefig(Settings.RESULT_PATH + datetime.now().strftime("%Y%m%d-%H%M") + ".png")

    @staticmethod
    def build_graph(results):
        traffic_network = nx.DiGraph()
        if not results:
            return traffic_network
        for node in results[1].keys():
            traffic_network.add_node(node, traffic=results[1][node]['vehicles'])

        for time_step, data in results.items():
            for node, segment_data in data.items():
                if segment_data['successors']:
                    for successor in segment_data['successors']:
                        traffic_network.add_edge(node, successor)

        return traffic_network

    @staticmethod
    def update(time_step, results, traffic_network, pos, ax, fig_canvas):
        print(f'Updating time step: {time_step}')
        pass
        time_step = int(time_step) - 1
        # Calculate the average number of vehicles for each segment at the current time step
        avg_traffic = {
            node: np.divide(np.sum(results[time_step][node]['vehicles']), results[time_step][node]['max_vehicle']) * 100
            for
            node in results[time_step].keys()}

        # Update node colors based on the average traffic
        node_colors = [avg_traffic[node] for node in traffic_network.nodes]

        # Update existing plot
        ax.clear()
        nx.draw(traffic_network, pos, with_labels=True, node_size=800, node_color=node_colors, cmap=plt.cm.Reds, ax=ax,
                vmin=0, vmax=100)

        # Set plot title
        ax.set_title(f'Time Step: {time_step}')

        # Redraw canvas
        fig_canvas.draw()

    @staticmethod
    # segments must be a dict of a segments data with segment_id as key
    def plot_heatmap_segments(simulation: SimulationInterface, parent):
        tabs = ttk.Notebook(parent)
        tabs.pack(fill=tk.BOTH, expand=True)
        # result_np should be in this form:
        # results = [[c1(0), c2(0),..., cn-1(0), cn(0)],[c1(1), c2(1),..., cn-1(1), cn(1)] ...]
        #             timestep 1                         timestep 2
        results = simulation.get_results_np()
        plots = []
        print(simulation.get_segments())
        for key, segment in simulation.get_segments().items():
            plots = Visualization.plot_heatmap_timesteps(key, segment[SimulationInterface.LOG],
                                                         segment[SimulationInterface.MAX_VEHICLE],
                                                         segment[SimulationInterface.LANES])

        return plots

    @staticmethod
    def plot_heatmap_timesteps(segment_id, log, max_vehicle, lanes):
        np_log = np.array(log)
        np_max_vehicle = np.array(max_vehicle)
        np_lanes = np.array(lanes)

        length = np_max_vehicle * get_settings().CAR_LENGTH / np_lanes

        log_data = (np_log * 1000) / length
        log_data = np.transpose(log_data)

        vmin = 0
        vmax = (1000 / get_settings().CAR_LENGTH) * np.max(lanes)  # 1000m is a km. Density of cars per km

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
        plt.title(f'Heatmap of {segment_id}')
        # Add colorbar
        cbar = plt.colorbar(heatmap)

        # # Add cursor tooltip to each cell
        # mplcursors.cursor(heatmap, hover=True).connect(
        #     "add", lambda sel: sel.annotation.set_text(
        #         f'Timestep: {int(sel.target[0])}\nCell: {int(sel.target[1])}\nValue: {log_data[int(sel.target[1]), int(sel.target[0])]}'
        #     )
        # )
        #
        # if Settings.SAVE_PLOTS:
        #     # check if directory exists
        #     if not os.path.exists(Settings.RESULT_PATH + "oo\\"):
        #         os.makedirs(Settings.RESULT_PATH + "oo\\")
        #
        #     plt.savefig(
        #         Settings.RESULT_PATH + "oo\\" + datetime.now().strftime("%Y%m%d-%H%M") + f"_Segment_{segment_id}.png")

        return fig
