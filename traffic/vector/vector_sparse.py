import tkinter as tk
from tkinter import filedialog
import time
import yaml
from traffic.vector import vector_full as vf
import numpy as np
import scipy.sparse as sparse


class VectorSparse(vf.VectorFullMatrix):

    def __init__(self, yaml_input):
        super().__init__(yaml_input)

    #    def create_segment_cells(self, key, values: dict):
    #        super().create_segment_cells(key, values)

    def create_adjacent_matrix(self):

        # temp_adjacent_matrix = sparse.csr_matrix((len(self.cells), len(self.cells)), dtype=np.double)
        row = []
        col = []
        data = []
        for segment in self.segment_map.values():
            first = segment[self.FIRST]
            last = segment[self.LAST]
            for i in range(first, last):
                row.append(i + 1)
                col.append(i)
                data.append(self.ADJACENT_FACTOR)

            if segment[self.SUCCESSORS]:
                for i in segment[self.SUCCESSORS]:
                    first_of_successor = self.segment_map[i][self.FIRST]
                    if first_of_successor in row and last in col:
                        continue
                    row.append(first_of_successor)
                    col.append(last)
                    data.append(self.ADJACENT_FACTOR)

            if segment[self.PREDECESSORS] and len(segment[self.PREDECESSORS]) == 2:
                for i in segment[self.PREDECESSORS]:
                    last_of_predecessor = self.segment_map[i][self.LAST]
                    if first in row and last_of_predecessor in col:
                        continue
                    row.append(first)
                    col.append(last_of_predecessor)
                    data.append(self.ADJACENT_FACTOR)
        self.adjacent_matrix = sparse.csr_matrix((data, (row, col)), shape=(len(self.cells), len(self.cells)))

    def init_flows(self):
        # print(ndarray.nonzero(adjacent_matrix))
        for i in range(0, len(self.flow)):
            link_found = False
            cell_b = i
            if not i in self.flow_dict:
                self.flow_dict[i] = {}
            if self.adjacent_matrix.getrow(i).count_nonzero() > 1:  # Merge
                nonzero = self.adjacent_matrix.getrow(i).nonzero()

                cell_a = nonzero[1][0]  # get first y coordinate
                cell_c = nonzero[1][1]  # get second y coordinate
                self.flow_dict[cell_a] = {}
                self.flow_dict[cell_c] = {}
                self.flow_dict[cell_a]['type'] = 'merge'
                self.flow_dict[cell_c]['type'] = 'merge'
                self.flow_dict[cell_c]['c'] = cell_a  # complementary for c is a
                self.flow_dict[cell_a]['c'] = cell_c  # complementary for a is c
                self.flow_dict[cell_c]['b'] = cell_b
                self.flow_dict[cell_a]['b'] = cell_b
                link_found = True

            if self.adjacent_matrix.getcol(i).count_nonzero() > 1:  # Diverge
                nonzero = self.adjacent_matrix.getcol(i).nonzero()
                cell_a = nonzero[0][0]  # get first x coordinate
                cell_c = nonzero[0][1]  # get second x coordinate
                self.flow_dict[i]['type'] = 'diverge'
                self.flow_dict[i]['a'] = cell_a
                self.flow_dict[i]['c'] = cell_c
                link_found = True

            if self.adjacent_matrix.getcol(i).count_nonzero() == 1:  # ordinary

                link_found = True
                nonzero = self.adjacent_matrix.getcol(i).nonzero()
                cell_a = nonzero[0][0]  # get value of row / x-coordinate
                if not self.flow_dict[i]:  # other kind of link exists already
                    self.flow_dict[i]['type'] = 'ord'
                    self.flow_dict[i]['a'] = cell_a

            if self.adjacent_matrix.getcol(i).count_nonzero() == 0 \
                    and not self.adjacent_matrix.getrow(i).count_nonzero() == 0:  # Border Out Cell
                link_found = True
                self.flow_dict[i]['type'] = 'border'  # border out

            if not link_found:
                error = 'No allowed link found for cell ' + str(i)
                raise Exception(error)


def main():
    root = tk.Tk()
    root.withdraw()

    file_path = filedialog.askopenfilename()
    with open(file_path, "r") as stream:
        # with open(Settings.get_settings().SIM_FILE, "r") as stream:
        try:
            yaml_input = yaml.safe_load(stream)
            start = time.time()
            simulation = VectorSparse(yaml_input)
            simulation.simulate()
            end = time.time()
            print(f"Running time: {end - start:.2f} seconds")
            simulation.show_results()
        except yaml.YAMLError as exc:
            print(exc)
            return


if __name__ == '__main__':
    main()
