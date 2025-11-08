import random

from game.constans import EMPTY, SHIP, DAMAGED, MISSED
from game.ship import find_ship_cages


def player_move_classic(field):
    """
    Функция отвечает за ход игрока
    """
    field_size_y = len(field)
    field_size_x = len(field[0])
    while True:
        try:
            x, y = map(int, input("Ваш ход: ").split())
            if (0 <= x < field_size_x and 0 <= y < field_size_y and
                    (field[y][x] == EMPTY or field[y][x] == SHIP)):
                return x, y
            elif 0 <= x < field_size_x and 0 <= y < field_size_y:
                print("Клетка уже в игре. Попробуйте еще раз.")
            else:
                print("Введите 2 числа в пределах поля")
        except ValueError:
            print("Ошибка. Введите два числа через пробел.")


def player_move_1v1(player_field, enemy_field):
    """
    Функция отвечает за ход игрока
    """

    print("Выберите клетку, принадлежащую "
          "кораблю, которым хотите выстрелить (x y):")
    player_field_size_y = len(player_field)
    player_field_size_x = len(player_field[0])

    ship_x, ship_y = map(int, input().split())
    if not (0 <= ship_x < player_field_size_x and
            0 <= ship_y < player_field_size_y):
        print("Некорректные координаты корабля.")
        return False
    if player_field[ship_y][ship_x] != SHIP:
        print("В выбранной клетке нет вашего неподбитого корабля.")
        return False

    ship_cells = find_ship_cages(player_field, ship_x, ship_y)
    if all(player_field[y][x] == DAMAGED for x, y in ship_cells):
        print("Этот корабль уничтожен, им нельзя выстрелить.")
        return False

    ship_size = len(ship_cells)

    field_size_y = len(enemy_field)
    field_size_x = len(enemy_field[0])

    while True:
        try:
            x, y = map(int, input(
                "Введите координаты выстрела (x y): ").split())
            if (0 <= x < field_size_x and
                    0 <= y < field_size_y and enemy_field[y][x] != DAMAGED):
                break
            elif 0 <= x < field_size_x and 0 <= y < field_size_y:
                print("Клетка уже в игре. Попробуйте еще раз.")
            else:
                print("Введите 2 числа в пределах поля")
        except ValueError:
            print("Ошибка. Введите два числа через пробел.")

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    hit_cells = [(x, y)]
    cells = []
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        if 0 <= nx < field_size_x and 0 <= ny < field_size_y:
            cells.append((nx, ny))
    for i in range(ship_size - 1):
        if len(cells) != 0:
            new_hit = random.choice(cells)
            cells.remove(new_hit)
            hit_cells.append(new_hit)

    damaged_cells = []
    for x, y in hit_cells:
        hit = is_hit_1v1(x, y, enemy_field)
        if hit:
            damaged_cells.append((x, y))
    print(f"Игрок выстрелил "
          f"{ship_size}-палубным кораблем по {hit_cells}")
    return damaged_cells


def is_hit_classic(x, y, field):
    """
    Проверка на попадание
    """
    if field[y][x] == SHIP:
        field[y][x] = DAMAGED
        return True
    else:
        field[y][x] = MISSED
        return False


def is_hit_1v1(x, y, field):
    if field[y][x] == SHIP:
        field[y][x] = DAMAGED
        return True
