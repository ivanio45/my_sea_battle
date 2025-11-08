import random
from game.constans import EMPTY, SHIP, DAMAGED


def ship_not_near(field, x, y, ship_size, position):
    """
    Проверяет, можно ли разместить
    корабль в (x, y) с учетом границ и соседних кораблей.
    """
    field_size_y = len(field)
    field_size_x = len(field[0])
    ship_coords = []
    if position == 'h':
        if x + ship_size > field_size_x:
            return False
        for i in range(ship_size):
            cage_x = x + i
            cage_y = y
            if field[cage_y][cage_x] != EMPTY:
                return False
            ship_coords.append((cage_x, cage_y))
    else:
        if y + ship_size > field_size_y:
            return False
        for i in range(ship_size):
            cage_x = x
            cage_y = y + i
            if field[cage_y][cage_x] != EMPTY:
                return False
            ship_coords.append((cage_x, cage_y))

    for ship_x, ship_y in ship_coords:
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                if dx == 0 and dy == 0:
                    continue
                check_x = ship_x + dx
                check_y = ship_y + dy
                if (0 <= check_x < field_size_x and
                        0 <= check_y < field_size_y):
                    if (check_x, check_y) not in ship_coords:
                        if field[check_y][check_x] == SHIP:
                            return False
    return True


def random_place_ship(field, ship_size):
    """
    Случайная расстановка корабля
    """
    field_size_y = len(field)
    field_size_x = len(field[0])

    max_attempts = 500
    attempts = 0
    while attempts < max_attempts:
        attempts += 1
        position = random.choice(['h', 'v'])
        if position == 'v' and field_size_y - ship_size < 0:
            position = 'h'
        if position == 'h' and field_size_x - ship_size < 0:
            position = 'v'
        if position == 'h':
            x = random.randint(0, field_size_x - ship_size)
            y = random.randint(0, field_size_y - 1)
        else:
            x = random.randint(0, field_size_x - 1)
            y = random.randint(0, field_size_y - ship_size)
        if ship_not_near(field, x, y, ship_size, position):
            if position == 'h':
                for i in range(ship_size):
                    field[y][x + i] = SHIP
            else:
                for i in range(ship_size):
                    field[y + i][x] = SHIP
            return True
    print(f"Ошибка: Не удалось разместить корабль")
    return False


def find_ship_cages(field, x, y):
    """
    Определяются занимаемые данным кораблем клетки
    """
    field_size_y = len(field)
    field_size_x = len(field[0])

    steps = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    cages = []
    stack = [(x, y)]
    while stack:
        a, b = stack.pop()
        if (a, b) not in cages:
            cages.append((a, b))
            for i, j in steps:
                c = a + i
                d = b + j
                if (0 <= c < field_size_x and
                        0 <= d < field_size_y and ((c, d) not in cages)):
                    if field[d][c] == DAMAGED or field[d][c] == SHIP:
                        stack.append((c, d))
    return cages
