__author__ = 'daniel'


class BoxTest:
    def __init__(self, data_x, data_y, i, j):
        self.data_x = data_x
        self.data_y = data_y
        self.i = i
        self.j = j

        # compute quantiles. Not using ranges since they are only overhead.
        self.x_q_i = self.data_x.quantile(self.i)
        self.x_q_j = self.data_x.quantile(self.j)
        self.y_q_i = self.data_y.quantile(self.i)
        self.y_q_j = self.data_y.quantile(self.j)

    def perform(self):
        return self.are_distinct() and self.x_q_j < self.y_q_i

    def are_distinct(self):
        overlap = self.overlap(self.x_q_i, self.x_q_j, self.y_q_i, self.y_q_j)
        return not overlap

    def get_lowest(self):
        if self.x_q_j < self.y_q_i:
            return self.data_y

        return self.data_x

    def x_box(self):
        return [self.x_q_i, self.x_q_j]

    def y_box(self):
        return [self.y_q_i, self.y_q_j]

    def overlap(self, a_lower, a_upper, b_lower, b_upper):
        return a_upper > b_lower and a_lower < b_upper














