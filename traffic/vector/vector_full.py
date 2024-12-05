import tkinter as tk
from tkinter import filedialog
import time
import yaml
from traffic.vector import vector_general as vg
import numpy as np


class VectorFullMatrix(vg.VectorCTM):
    flow_dict = {}
    ADJACENT_FACTOR = 1
    def __init__(self, yaml_input):
        super().__init__(yaml_input)

    def create_adjacent_matrix(self):
        temp_adjacent_matrix = np.zeros((len(self.cells), len(self.cells)), np.double)
        for segment in self.segment_map.values():
            first = segment[self.FIRST]
            last = segment[self.LAST]
            for i in range(first, last):
                temp_adjacent_matrix[i + 1][i] = self.ADJACENT_FACTOR

            if segment[self.SUCCESSORS]:
                for i in segment[self.SUCCESSORS]:
                    first_of_successor = self.segment_map[i][self.FIRST]
                    temp_adjacent_matrix[first_of_successor][last] = self.ADJACENT_FACTOR

            if segment[self.PREDECESSORS] and len(segment[self.PREDECESSORS]) == 2:
                for i in segment[self.PREDECESSORS]:
                    last_of_predecessor = self.segment_map[i][self.LAST]
                    temp_adjacent_matrix[first][last_of_predecessor] = self.ADJACENT_FACTOR
        self.adjacent_matrix = temp_adjacent_matrix
    def calc_div_coefficient(self, a):
        return 1 / a # adjacent matrix entry of diverge link
    def calc_flows(self):
        for i in range(0, len(self.flow)):
            match self.flow_dict[i]['type']:
                case 'border':

                    self.flow[i] = self.send[i]
                    continue
                case 'ord':
                    self.flow[i] = min(self.receive[self.flow_dict[i]['a']], self.send[i])
                    continue
                case 'diverge':
                    self.flow[i] = min(self.send[i], self.receive[self.flow_dict[i]['a']] / self.adjacent_matrix[
                        self.flow_dict[i]['a'], i],
                                       self.receive[self.flow_dict[i]['c']] / self.adjacent_matrix[
                                           self.flow_dict[i]['c'], i])
                    continue
                case 'merge':
                    cell_a = i  # merging cell
                    cell_b = self.flow_dict[i]['b']  # merged cell
                    cell_c = self.flow_dict[i]['c']  # other merging cell

                    if self.receive[cell_b] >= self.send[cell_a] + self.send[cell_c]:
                        self.flow[cell_a] = self.send[cell_a]

                    else:
                        self.flow[cell_a] = vg.VectorCTM.mid(self.send[cell_a],
                                                             self.receive[cell_b] - self.send[cell_c],
                                                             self.adjacent_matrix[cell_b, cell_a] * self.receive[
                                                                 cell_b])

    # initialze flows with a dictionary to save runtime of slicing the adjacent matrix
    def init_flows(self):
        # print(ndarray.nonzero(adjacent_matrix))
        for i in range(0, len(self.flow)):
            link_found = False
            cell_b = i
            if cell_b == 461:
                print('debug')
            if not i in self.flow_dict:
                self.flow_dict[i] = {}
            if np.count_nonzero(self.adjacent_matrix[i, :]) == 2:  # Merge Zeile der Matrix
                other_cells = np.ndarray.nonzero(self.adjacent_matrix[i, :])[0]  # get first of tuple

                cell_a = np.ndarray.min(other_cells)
                cell_c = np.ndarray.max(other_cells)

                self.flow_dict[cell_a] = {}
                self.flow_dict[cell_c] = {}
                self.flow_dict[cell_a]['type'] = 'merge'
                self.flow_dict[cell_c]['type'] = 'merge'
                self.flow_dict[cell_c]['c'] = cell_a  # complementary for c is a
                self.flow_dict[cell_a]['c'] = cell_c  # complementary for a is c
                self.flow_dict[cell_c]['b'] = cell_b
                self.flow_dict[cell_a]['b'] = cell_b
                link_found = True

            if np.count_nonzero(self.adjacent_matrix[:, i]) == 2:  # Diverge
                other_cells = np.ndarray.nonzero(self.adjacent_matrix[:, i])[0]  # get first of tuple

                cell_a = np.ndarray.min(other_cells)
                cell_c = np.ndarray.max(other_cells)

                self.flow_dict[i]['type'] = 'diverge'
                self.flow_dict[i]['a'] = cell_a
                self.flow_dict[i]['c'] = cell_c
                link_found = True

            if np.count_nonzero(self.adjacent_matrix[:, i]) == 1:  # ordinary

                link_found = True
                other_cells = np.ndarray.nonzero(self.adjacent_matrix[:, i])[0]  # get first of tuple
                cell_a = np.ndarray.min(other_cells)  # only one value so get value of row / x-coordinate

                if not self.flow_dict[i]:  # other kind of link exists already
                    self.flow_dict[i]['type'] = 'ord'
                    self.flow_dict[i]['a'] = cell_a

            if np.count_nonzero(self.adjacent_matrix[:, i]) == 0 and not np.count_nonzero(
                    self.adjacent_matrix[i, :]) == 0:  # Border Out Cell
                link_found = True
                self.flow_dict[i]['type'] = 'border'  # border out

            if not link_found:
                error = 'No allowed link found for cell ' + str(i)
                raise Exception(error)

    def simulate(self):
        super().simulate()


def main():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename()
    with open(file_path, "r") as stream:
        # with open(Settings.SIM_FILE, "r") as stream:
        try:
            yaml_input = yaml.safe_load(stream)
            start = time.time()
            simulation = VectorFullMatrix(yaml_input)
            simulation.simulate()
            end = time.time()
            print(f"Running time: {end - start:.2f} seconds")
            simulation.show_results()
        except yaml.YAMLError as exc:
            print(exc)
            return


if __name__ == '__main__':
    main()
