import random


class Ai:
    def __init__(self):
        self.first_hit = None
        self.last_hit = None
        self.direction = None
        self.directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def make_move(self, available_cells):
        """
        Автоматический ход бота
        """
        if self.direction:
            next_move = (self.last_hit[0] + self.direction[0],
                         self.last_hit[1] + self.direction[1])
            if next_move in available_cells:
                return next_move
            else:
                direction = (-self.direction[0], -self.direction[1])
                next_move = (self.first_hit[0] + direction[0],
                             self.first_hit[1] + direction[1])
                if next_move in available_cells:
                    return next_move
                else:
                    self.direction = None

        if self.last_hit:
            for dx, dy in self.directions:
                next_move = (self.first_hit[0] + dx, self.first_hit[1] + dy)
                if next_move in available_cells:
                    return next_move

        return random.choice(list(available_cells))

    def register_hit(self, x, y, is_ship_destroyed=False):
        """
        Регистрация попадания
        """
        if is_ship_destroyed:
            self.first_hit = None
            self.last_hit = None
            self.direction = None
            return

        if not self.first_hit:
            self.first_hit = (x, y)
        else:
            dx = x - self.last_hit[0]
            dy = y - self.last_hit[1]
            if abs(dx) > 1:
                dx = dx // abs(dx)
            if abs(dy) > 1:
                dy = dy // abs(dy)
            self.direction = (dx, dy)

        self.last_hit = (x, y)

    def register_miss(self):
        """
        Регистрация промаха
        """
        if self.direction:
            self.direction = (-self.direction[0], -self.direction[1])
            self.last_hit = self.first_hit
