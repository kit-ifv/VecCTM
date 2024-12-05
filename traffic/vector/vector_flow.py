import time
import tkinter as tk

import numpy as np
import scipy.sparse as sparse
import yaml

from resources import Settings
from traffic.vector.vector_sparse import VectorSparse
from visualize import Visualization


def xor(a, b):
    return (a and not b) or (not a and b)


class VectorizedFlow(VectorSparse):
    def __init__(self, yaml_input):

        self.bool_merge_capacity = None
        self.bool_merge = None
        self.bool_ord = None
        self.bool_diverge = None

        self.border_out_flow = None
        self.merge_matrix = None
        self.first_diverge_matrix = None
        self.second_diverge_matrix = None
        self.diverge_percentage = None
        super().__init__(yaml_input)

    def init_vectors(self):
        # cells is now filled
        self.bool_ord = np.zeros(len(self.cells), dtype=bool)
        self.bool_merge = np.zeros(len(self.cells), dtype=bool)
        self.bool_merge_capacity = np.zeros(len(self.cells), dtype=bool)
        self.bool_diverge = np.zeros(len(self.cells), dtype=bool)

        self.border_out_flow = np.zeros(len(self.cells))

        self.merge_matrix = sparse.csr_matrix(np.diag(np.ones(len(self.cells), dtype=bool)))
        self.first_diverge_matrix = sparse.csr_matrix(np.zeros((len(self.cells), len(self.cells)), dtype=bool))
        self.second_diverge_matrix = sparse.csr_matrix(np.zeros((len(self.cells), len(self.cells)), dtype=bool))

        self.diverge_percentage = np.ones(len(self.cells))
    def calc_div_coefficient(self, a):
        return 1  # now is every entry in the adjacent matrix 1

    def is_capacity_sufficient(self):
        self.bool_merge_capacity = np.array(
            self.adjacent_matrix.transpose().dot(np.greater_equal(self.receive, self.adjacent_matrix.dot(self.send))),
            dtype=bool)

    def calc_flows(self):
        self.is_capacity_sufficient()
        ordinary_flow = self.bool_ord * np.minimum(self.send, self.adjacent_matrix.transpose().dot(self.receive))

        merge_flow = self.bool_merge * self.bool_merge_capacity * self.send
        merge_flow_cap_limit = (self.bool_merge * np.invert(self.bool_merge_capacity)) \
                               * self.vector_mid(self.send,
                                                 self.merge_percentage * self.adjacent_matrix.transpose().dot(
                                                     self.receive),
                                                 self.adjacent_matrix.transpose().dot(
                                                     self.receive) - self.merge_matrix.dot(self.send))

        diverge_flow = self.bool_diverge * np.minimum(self.send,
                                                      np.minimum(self.first_diverge_matrix.dot(
                                                          self.receive / self.diverge_percentage),
                                                          self.second_diverge_matrix.dot(
                                                              self.receive / self.diverge_percentage)))
        self.flow = ordinary_flow + merge_flow + merge_flow_cap_limit + diverge_flow
        '''self.flow = self.bool_ord * np.minimum(self.send, self.receive) \
                    + self.bool_merge * self.bool_merge_capacity * self.merge_matrix.dot(self.send) \
                    + (self.bool_merge * np.invert(self.bool_merge_capacity)) \
                    * self.vector_mid(self.send,
                                      self.merge_percentage * self.adjacent_matrix.transpose().dot(self.receive),
                                      self.receive - self.merge_matrix.dot(
                                          self.send)) \
                    + self.bool_diverge * np.minimum(self.send,
                                                     self.first_diverge_matrix.dot(
                                                         self.receive / self.diverge_percentage),
                                                     self.second_diverge_matrix.dot(
                                                         self.receive / self.diverge_percentage))'''

    def vector_mid(self, a, b, c):
        return np.median(np.stack([a, b, c]), axis=0)

    def init_flows(self):
        self.init_vectors()
        for i in range(0, len(self.flow)):
            link_found = False
            cell_b = i
            if self.adjacent_matrix.getrow(i).count_nonzero() > 1:  # Merge
                nonzero = self.adjacent_matrix.getrow(i).nonzero()
                cell_a = nonzero[1][0]  # get first y coordinate
                cell_c = nonzero[1][1]  # get second y coordinate
                self.bool_merge[cell_a] = True
                self.bool_ord[cell_a] = False
                self.merge_percentage[cell_a] = 0.5

                self.bool_merge[cell_c] = True
                self.bool_ord[cell_c] = False
                self.merge_percentage[cell_c] = 0.5

                '''
                betrachtet wird nur der ausgehende Fluss,
                daher werden nur die Werte von a und c gesetzt
                a 
                 \
                  b 
                 / 
                c
                Aus Sicht von a und c ist deren Verbindung ordinary, erst durch b 
                wird sichtbar, dass es sich um einen Merge handelt.
                '''

                # swap rows in merge matrix
                self.merge_matrix[[cell_a, cell_c]] = self.merge_matrix[[cell_c, cell_a]]

            if self.adjacent_matrix.getcol(i).count_nonzero() > 1:  # Diverge
                nonzero = self.adjacent_matrix.getcol(i).nonzero()
                cell_a = nonzero[0][0]  # get first x coordinate
                cell_c = nonzero[0][1]  # get second x coordinate

                self.bool_diverge[cell_b] = True
                '''
                Anders als beim Merge wird beim diverge der ausgehende Gesamtfluss von b berechnet
                und anschließend mithilfe der Verteilungen in der Adjazenzmatrix auf a und c verteilt.
                  a
                 /
                b
                 \
                  c 
                '''
                self.first_diverge_matrix[cell_b, cell_a] = True
                self.second_diverge_matrix[cell_b, cell_c] = True
                self.diverge_percentage[cell_a] = 0.5
                self.diverge_percentage[cell_c] = 0.5

            if self.adjacent_matrix.getcol(i).count_nonzero() == 1:  # ordinary
                if not self.bool_merge[cell_b]:
                    self.bool_ord[cell_b] = True

            if xor(self.bool_ord[cell_b], xor(self.bool_merge[cell_b], self.bool_diverge[cell_b])):
                '''
                Es darf ausschließlich ein bool-Wert true sein, da eine Zelle ausschließlich
                einem Typ zugeordnet werden darf.
                '''
                link_found = True
            if self.adjacent_matrix.getcol(i).count_nonzero() == 0 \
                    and not self.adjacent_matrix.getrow(i).count_nonzero() == 0:  # Border Out Cell
                self.border_out_flow[cell_b] = self.max_flow[cell_b]
                link_found = True

            if not link_found:
                print("No link found for cell " + str(cell_b))

    def calc_cells(self):
        self.cells = self.cells + self.diverge_percentage * self.adjacent_matrix.dot(
            self.flow) - self.flow + self.current_border_flow
        cbof = np.minimum(self.border_out_flow, self.cells)
        self.cells = self.cells - cbof
        return


    @staticmethod
    def get_name():
        return "Vectorized Calculation with Vectorized Flow"


def main():
    root = tk.Tk()
    root.withdraw()

    file_path = tk.filedialog.askopenfilename()
    with open(file_path, "r") as stream:
        # with open(Settings.SIM_FILE, "r") as stream:
        try:
            yaml_input = yaml.safe_load(stream)
            simulation = VectorizedFlow(yaml_input)
            start = time.time()
            simulation.simulate()
            end = time.time()
            print(f"Running time: {end - start:.2f} seconds")
            if Settings.SAVE_RESULTS:
                simulation.save_results()
            if Settings.SHOW_PLOTS:
                simulation.show_results()
            if Settings.SAVE_PLOTS:
                simulation.save_result_plots()
        except yaml.YAMLError as exc:
            print(exc)
            return


if __name__ == '__main__':
    main()
