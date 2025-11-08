from game.constans import EMPTY, SHIP, LINE, STICK, CROSSING, MISSED, DAMAGED
from game.ship import find_ship_cages


def make_field(field_size):
    """
    Инициализация игрового поля
    """
    field = []
    for i in range(field_size[1]):
        row = []
        for j in range(field_size[0]):
            row.append(EMPTY)
        field.append(row)
    return field


def print_field(field, hide_ships, mins=None):
    """
    Отрисовка игрового поля в консоли
    """
    field_size_y = len(field)
    field_size_x = len(field[0])

    column_nums_str = " " * 3
    for i in range(field_size_x):
        column_nums_str += f" {i:{2}d} "
    print(column_nums_str)
    print(" " * 2 + " " + CROSSING + (LINE * 3 + CROSSING) * field_size_x)
    for i in range(field_size_y):
        row_num = f"{i:{2}d}"
        row = f"{row_num} {STICK}"
        for j in range(field_size_x):
            cage = field[i][j]
            if (hide_ships and mins is not None and
                    (j, i) in mins and cage != MISSED and cage != DAMAGED):
                row += f"{EMPTY + 'M' + EMPTY}{STICK}"
            elif hide_ships and cage == SHIP:
                row += f"{EMPTY * 3}{STICK}"
            else:
                row += f"{EMPTY + cage + EMPTY}{STICK}"
        print(row)
        print(" " * 2 + " " + CROSSING + (LINE * 3 + CROSSING) * field_size_x)


def mark_around_ship(field, player_available_cells, ship_cells):
    """
    Функция отмечает клетки вокруг уничтоженного корабля
    """
    field_size_y = len(field)
    field_size_x = len(field[0])

    for x, y in ship_cells:
        for i in range(-1, 2):
            for j in range(-1, 2):
                a = x + i
                b = y + j
                if 0 <= a < field_size_x and 0 <= b < field_size_y:
                    if field[b][a] == EMPTY:
                        field[b][a] = MISSED
                        if (player_available_cells is not None and
                                not (a == x and b == y)):
                            player_available_cells.remove((a, b))


def check_ship_full_destroyed(field, x, y, player_available_cells=None):
    """
    Проверка уничтожен ли корабль полностью
    """
    cages = find_ship_cages(field, x, y)
    if all(field[j][i] == DAMAGED for i, j in cages):
        mark_around_ship(field, player_available_cells, cages)
        return True
    else:
        return False
