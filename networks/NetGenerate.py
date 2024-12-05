import math
import random

import yaml

from resources import Settings


class Segment:
    segments = {}

    def __init__(self, segment_id, lanes, length, predecessor, successor, velocity_free, is_border, name):
        self.SEGMENT_ID = segment_id
        self.LANES = lanes
        self.LENGTH = length
        self.predecessor = predecessor
        self.successor = successor
        self.velocity_free = velocity_free
        self.is_border = is_border
        self.name = name
        if self.is_border:
            self.border_flow = Segment.generate_border_flow()
        Segment.segments[segment_id] = self

    @staticmethod
    def generate_border_flow():
        return {j: int(random.random() * 5400) for j in range(0, Settings.STEPS, 3)}

    @staticmethod
    def get_segment(segment_id):
        return Segment.segments[segment_id]

    def get_segment_id(self):
        return self.SEGMENT_ID

    def add_predecessor(self, predecessor):
        self.predecessor.append(predecessor)
        self.set_is_border(False)

    def add_successor(self, successor):
        self.successor.append(successor)

    def set_is_border(self, is_border):
        self.is_border = is_border

    def get_yaml_representation(self):
        yaml_dict = {}
        if self.is_border and self.predecessor == []:
            return {self.SEGMENT_ID: {'name': self.name,
                                      'length': self.LENGTH,
                                      'lanes': self.LANES,
                                      'velocity_free': self.velocity_free,
                                      'predecessor': self.predecessor,
                                      'successor': self.successor,
                                      'border_flow': [self.border_flow]}}
        return {self.SEGMENT_ID: {'name': self.name,
                                  'length': self.LENGTH,
                                  'lanes': self.LANES,
                                  'velocity_free': self.velocity_free,
                                  'predecessor': self.predecessor,
                                  'successor': self.successor}}

    def __str__(self):
        return f'Segment({self.SEGMENT_ID}, {self.LANES}, {self.LENGTH}, {self.predecessor}, {self.successor}, {self.velocity_free}, {self.is_border}, {self.border_flow})'


class Cloverleaf:
    CLOVERLEAF_SEGMENTS_AMOUNT = 28
    CLOVERLEAF_MAIN_TRACKS_AMOUNT = 4
    CLOVERLEAF_MAIN_SEGMENTS_INSIDE_AMOUNT = 5  # on in and one out, three inside
    CLOVERLEAF_MAIN_SEGMENTS_TOTAL_AMOUNT = CLOVERLEAF_MAIN_TRACKS_AMOUNT * CLOVERLEAF_MAIN_SEGMENTS_INSIDE_AMOUNT
    CLOVERLEAF_STRAIGHT_RAMP = 4
    CLOVERLEAF_CIRC_RAMP = 4
    LANES_MAIN = 3
    SPEED_MAIN = 130
    LENGTH_INSIDE = 500
    LENGTH_OUTSIDE = 2000
    LANES_RAMP = 1
    SPEED_RAMP = 80

    def __init__(self, cloverleaf_id, row, col, grid_size):
        self.cloverleaf_id: int = cloverleaf_id
        self.row = row
        self.col = col
        self.grid_size = grid_size
        self.LENGTH_OUTSIDE = self.calc_length_outside()
        print(self.LENGTH_OUTSIDE)
        self.segments = {}
        self.generate_segments()
        self.generate_inside_connections()

    def calc_length_outside(self):
        total_cell_number = 800 * ((self.grid_size + 1) ** 2)
        inner_cell_number = 352 * (self.grid_size ** 2)
        outer_segment_number = 8 * (self.grid_size ** 2)
        main_speed = self.SPEED_MAIN / 3.6
        length = total_cell_number - inner_cell_number
        length = length / outer_segment_number
        length = length * main_speed
        print(length)
        return math.floor(length)
    def __str__(self):
        return f'Cloverleaf({self.cloverleaf_id}, {self.row}, {self.col}, {self.grid_size}, {self.segments})'

    def generate_segments(self):
        # generate incoming segments
        for i in range(1, Cloverleaf.CLOVERLEAF_MAIN_SEGMENTS_TOTAL_AMOUNT + 1, 5):
            self.segments[self.get_seg_id(i)] = (
                Segment(self.get_seg_id(i), self.LANES_MAIN, self.LENGTH_OUTSIDE, [], [], self.SPEED_MAIN, True,
                        self.get_segment_name("main_in", i)))
        # generate outgoing segments
        for i in range(5, Cloverleaf.CLOVERLEAF_MAIN_SEGMENTS_TOTAL_AMOUNT + 1, 5):
            self.segments[self.get_seg_id(i)] = (
                Segment(self.get_seg_id(i), self.LANES_MAIN, self.LENGTH_OUTSIDE, [], [], self.SPEED_MAIN, True,
                        self.get_segment_name("main_out", i)))
        # generate main inside segments
        for i in range(0, 4):
            for j in range(2, 5):
                self.segments[self.get_seg_id(i * 5 + j)] = (
                    Segment(self.get_seg_id(i * 5 + j), self.LANES_MAIN, self.LENGTH_INSIDE, [], [], self.SPEED_MAIN,
                            False, self.get_segment_name("main_inside", i * 5 + j)))
        # generate ramp segments
        for i in range(self.CLOVERLEAF_MAIN_SEGMENTS_TOTAL_AMOUNT + 1, self.CLOVERLEAF_SEGMENTS_AMOUNT + 1):
            self.segments[self.get_seg_id(i)] = (
                Segment(self.get_seg_id(i), self.LANES_RAMP, self.LENGTH_INSIDE, [], [], self.SPEED_RAMP, False,
                        self.get_segment_name("ramp", i)))

    def get_segment_name(self, stype, sid):
        return f"s{self.cloverleaf_id}_r{self.row}_c{self.col}_{stype}_{sid}"

    def get_seg_id(self, i):
        return self.cloverleaf_id * Cloverleaf.CLOVERLEAF_SEGMENTS_AMOUNT + i

    def get_seg_id_other(self, cloverleaf_id, i):
        return cloverleaf_id * Cloverleaf.CLOVERLEAF_SEGMENTS_AMOUNT + i

    def generate_inside_connections(self):
        j = 1
        # generate connections between main tracks
        for i in range(1, Cloverleaf.CLOVERLEAF_MAIN_SEGMENTS_TOTAL_AMOUNT + 1, 5):
            # 1, 6, 11, 16
            self.segments[self.get_seg_id(i)].add_successor(self.get_seg_id(i + 1))
            self.segments[self.get_seg_id(i)].add_successor(
                self.get_seg_id(Cloverleaf.CLOVERLEAF_MAIN_SEGMENTS_TOTAL_AMOUNT + j))

            # 2, 7, 12, 17
            self.segments[self.get_seg_id(i + 1)].add_predecessor(self.get_seg_id(i))
            self.segments[self.get_seg_id(i + 1)].add_successor(self.get_seg_id(i + 2))

            # 3, 8, 13, 18
            self.segments[self.get_seg_id(i + 2)].add_predecessor(self.get_seg_id(i + 1))
            if i == 1:  # id 3
                self.segments[self.get_seg_id(i + 2)].add_predecessor(self.get_seg_id(27))
            if i == 6:  # id 8
                self.segments[self.get_seg_id(i + 2)].add_predecessor(self.get_seg_id(28))
            if i == 11:  # id 13
                self.segments[self.get_seg_id(i + 2)].add_predecessor(self.get_seg_id(26))
            if i == 16:  # id 18
                self.segments[self.get_seg_id(i + 2)].add_predecessor(self.get_seg_id(25))
            self.segments[self.get_seg_id(i + 2)].add_successor(self.get_seg_id(i + 3))
            self.segments[self.get_seg_id(i + 2)].add_successor(self.get_seg_id(
                Cloverleaf.CLOVERLEAF_MAIN_SEGMENTS_TOTAL_AMOUNT + Cloverleaf.CLOVERLEAF_STRAIGHT_RAMP + j))

            # 4, 9, 14, 19
            self.segments[self.get_seg_id(i + 3)].add_predecessor(self.get_seg_id(i + 2))
            self.segments[self.get_seg_id(i + 3)].add_successor(self.get_seg_id(i + 4))

            # 5, 10, 15, 20
            self.segments[self.get_seg_id(i + 4)].add_predecessor(self.get_seg_id(i + 3))
            if i == 1:  # id 5
                self.segments[self.get_seg_id(i + 4)].add_predecessor(self.get_seg_id(24))
            if i == 6:  # id 10
                self.segments[self.get_seg_id(i + 4)].add_predecessor(self.get_seg_id(23))
            if i == 11:  # id 15
                self.segments[self.get_seg_id(i + 4)].add_predecessor(self.get_seg_id(21))
            if i == 16:  # id 20
                self.segments[self.get_seg_id(i + 4)].add_predecessor(self.get_seg_id(22))
            j += 1
        # generate connections between main and ramp tracks
        # segment 21
        self.segments[self.get_seg_id(21)].add_predecessor(self.get_seg_id(1))
        self.segments[self.get_seg_id(21)].add_successor(self.get_seg_id(15))

        # segment 22
        self.segments[self.get_seg_id(22)].add_predecessor(self.get_seg_id(6))
        self.segments[self.get_seg_id(22)].add_successor(self.get_seg_id(20))

        # segment 23
        self.segments[self.get_seg_id(23)].add_predecessor(self.get_seg_id(11))
        self.segments[self.get_seg_id(23)].add_successor(self.get_seg_id(10))

        # segment 24
        self.segments[self.get_seg_id(24)].add_predecessor(self.get_seg_id(16))
        self.segments[self.get_seg_id(24)].add_successor(self.get_seg_id(5))

        # segment 25
        self.segments[self.get_seg_id(25)].add_predecessor(self.get_seg_id(3))
        self.segments[self.get_seg_id(25)].add_successor(self.get_seg_id(18))

        # segment 26
        self.segments[self.get_seg_id(26)].add_predecessor(self.get_seg_id(8))
        self.segments[self.get_seg_id(26)].add_successor(self.get_seg_id(13))

        # segment 27
        self.segments[self.get_seg_id(27)].add_predecessor(self.get_seg_id(13))
        self.segments[self.get_seg_id(27)].add_successor(self.get_seg_id(3))

        # segment 28
        self.segments[self.get_seg_id(28)].add_predecessor(self.get_seg_id(18))
        self.segments[self.get_seg_id(28)].add_successor(self.get_seg_id(8))

        # interconnections
        if (self.grid_size <= 1):
            return
        # up and down
        # down
        if self.grid_size - 1 > self.row >= 0:
            self.segments[self.get_seg_id(15)].add_successor(
                self.get_seg_id_other(self.cloverleaf_id + self.grid_size, 11))
            self.segments[self.get_seg_id(16)].add_predecessor(
                self.get_seg_id_other(self.cloverleaf_id + self.grid_size, 20))
        # up
        if self.row > 0:
            self.segments[self.get_seg_id(20)].add_successor(
                self.get_seg_id_other(self.cloverleaf_id - self.grid_size, 16))
            self.segments[self.get_seg_id(11)].add_predecessor(
                self.get_seg_id_other(self.cloverleaf_id - self.grid_size, 15))

        # left and right connections
        # left
        if self.col > 0:
            self.segments[self.get_seg_id(10)].add_successor(self.get_seg_id_other(self.cloverleaf_id - 1, 6))
            self.segments[self.get_seg_id(1)].add_predecessor(self.get_seg_id_other(self.cloverleaf_id - 1, 5))
        # right
        if 0 <= self.col < self.grid_size - 1:
            self.segments[self.get_seg_id(5)].add_successor(self.get_seg_id_other(self.cloverleaf_id + 1, 1))
            self.segments[self.get_seg_id(6)].add_predecessor(self.get_seg_id_other(self.cloverleaf_id + 1, 10))




    def get_yaml_representation(self):
        yaml_dict = {}
        for segment in self.segments.values():
            yaml_dict.update(segment.get_yaml_representation())
        return yaml_dict


def generate_traffic_grid(grid_size):
    traffic_grid = []

    for row in range(0, grid_size):
        for col in range(0, grid_size):
            cloverleaf_id = row * grid_size + col
            traffic_grid.append(Cloverleaf(cloverleaf_id, row, col, grid_size))

    return traffic_grid


def save_yaml(data, filename):
    with open(filename, 'w') as file:
        yaml.dump(get_yaml_representation(data), file, default_flow_style=False)


def get_yaml_representation(data):
    segment_yaml = {}
    for segment in data:
        segment_yaml.update(segment.get_yaml_representation())

    yaml_output = {Settings.YAML_OPTION: get_options(), Settings.YAML_SEGMENT: segment_yaml}
    return yaml_output


def get_options():
    return {
        Settings.YAML_OPTION_LOGGING_INTERVAL: Settings.LOGGING_INTERVAL,
        Settings.YAML_OPTION_DURATION: Settings.STEPS,
        Settings.YAML_OPTION_INTERVAL: Settings.INTERVAL,
        Settings.YAML_OPTION_PERIOD: Settings.TIME_STEP
    }


if __name__ == "__main__":
    grid_size = Settings.GRID_SIZE  # Change this to generate a larger grid
    traffic_grid = generate_traffic_grid(grid_size)

    save_yaml(traffic_grid, 'traffic_grid.yaml')
