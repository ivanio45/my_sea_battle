from game.constans import EMPTY, SHIPS, SHIP, DAMAGED
from game.field import print_field, mark_around_ship
from game.ship import random_place_ship, ship_not_near, find_ship_cages


def clear_field(field):
    """
    Очистка поля перед новой генерацией
    """
    for row in field:
        for i in range(len(row)):
            row[i] = EMPTY


def random_setup_ships(field):
    """
    Расстановка кораблей с возможностью перегенерации
    """
    while True:
        clear_field(field)
        for count in SHIPS:
            for i in range(count):
                size_of_ship = SHIPS[count]
                random_place_ship(field, size_of_ship)
        print("\nВаша расстановка кораблей:")
        print_field(field, hide_ships=False)
        choice = input("\nВас устраивает расстановка?"
                       " (да/нет): ").strip().lower()
        if choice == 'да':
            break


def game_over(field):
    """
    Проверка на конец игры
    """
    for row in field:
        for cage in row:
            if cage == SHIP:
                return False
    return True


def init_available_cells(field_size):
    """
    Функция определяет клетки, еще не задействованные в игре
    """
    return {(x, y) for x in range(field_size[0])
            for y in range(field_size[1])}


def place_ship_manual(field, size, x, y, direction):
    """
    Ручная расстановка корабля
    """
    field_size_y = len(field)
    field_size_x = len(field[0])

    direction = direction.lower()
    if direction == 'h':
        if x + size > field_size_x:
            print("Корабль выходит за границы поля!")
            return False
        if not ship_not_near(field, x, y, size, direction):
            print("Здесь нельзя разместить корабль!")
            return False
        for i in range(size):
            if field[y][x + i] != EMPTY:
                print("Здесь нельзя разместить корабль!")
                return False
    else:
        if y + size > field_size_y:
            print("Корабль выходит за границы поля!")
            return False
        if not ship_not_near(field, x, y, size, direction):
            print("Здесь нельзя разместить корабль!")
            return False
        for i in range(size):
            if field[y + i][x] != EMPTY:
                print("Здесь нельзя разместить корабль!")
                return False

    if direction == 'h':
        for i in range(size):
            field[y][x + i] = SHIP
    else:
        for i in range(size):
            field[y + i][x] = SHIP

    return True


def manual_ship_placement(field):
    """
    Процесс ручной расстановки кораблей
    """
    print("Формат: x y h/v (например: 3 5 v - вертикально)")
    field_size = len(field)
    ships_to_place = []
    for size, count in SHIPS.items():
        ships_to_place.extend([size] * count)

    while ships_to_place:
        print_field(field, hide_ships=False)
        size = ships_to_place[0]
        print(f"Размещаем корабль длиной {size} "
              f"(осталось {ships_to_place.count(size)})")

        try:
            coords = input("Введите координаты и "
                           "направление (x y h/v): ").lower().split()
            if len(coords) != 3:
                raise ValueError
            x, y, direction = int(coords[0]), int(coords[1]), coords[2]
            if direction not in ('h', 'v'):
                raise ValueError
            if place_ship_manual(field, size, x, y, direction):
                ships_to_place.remove(size)
        except ValueError:
            print("Ошибка ввода! Используйте формат: x y h/v")


def record_score(moves, player_name):
    """
    Записывает количество ходов игрока в файл рекордов с именем.
    """
    with open("scores.txt", "a") as file:
        file.write(f"{player_name}:{moves}\n")


def display_scores():
    with open("scores.txt", "r") as file:
        scores = []
        for line in file:
            name, score = line.split(":")
            scores.append((name, int(score)))
        scores.sort(key=lambda item: item[1])
        if scores:
            print("\nТаблица рекордов:")
            rank = 1
            for name, score in scores[:10]:
                print(f"{rank}. {name}: {score} ходов")
                rank += 1
        else:
            print("\nВ таблице пока нет записей!")


def move_ship(field):
    """
    Реализует логику перемещения
    одного неподбитого корабля на одну клетку.
    """
    print("\n--- Перемещение корабля ---")
    print("Выберите клетку, принадлежащую "
          "кораблю, который хотите переместить (x y):")
    field_size_y = len(field)
    field_size_x = len(field[0])

    ship_x, ship_y = map(int, input().split())
    if not (0 <= ship_x < field_size_x and 0 <= ship_y < field_size_y):
        print("Некорректные координаты корабля.")
        return False
    if field[ship_y][ship_x] != SHIP:
        print("В выбранной клетке нет вашего неподбитого корабля.")
        return False

    ship_cells = find_ship_cages(field, ship_x, ship_y)
    if any(field[y][x] == DAMAGED for x, y in ship_cells):
        print("Этот корабль подбит, его нельзя переместить.")
        return False

    print("Введите куда переместить корабль(вверх, вниз, влево, вправо):")
    direction = input().strip().lower()
    dx, dy = 0, 0
    if direction == 'вверх':
        dy = -1
    elif direction == 'вниз':
        dy = 1
    elif direction == 'влево':
        dx = -1
    elif direction == 'вправо':
        dx = 1
    else:
        return False

    new_ship_cells = [(x + dx, y + dy) for x, y in ship_cells]

    if not all(0 <= x < field_size_x and
               0 <= y < field_size_y for x, y in new_ship_cells):
        print("Новая позиция выходит за пределы поля.")
        return False

    original_cells_state = [(x, y, field[y][x]) for x, y in ship_cells]
    for x, y in ship_cells:
        field[y][x] = EMPTY

    if len(new_ship_cells) > 1:
        is_horizontal = new_ship_cells[0][1] == new_ship_cells[1][1]
        new_position = 'h' if is_horizontal else 'v'
        if new_position == 'h':
            new_head_x = min(cell[0] for cell in new_ship_cells)
            new_head_y = new_ship_cells[0][1]
        else:
            new_head_y = min(cell[1] for cell in new_ship_cells)
            new_head_x = new_ship_cells[0][0]
    else:
        new_position = 'h'
        new_head_x, new_head_y = new_ship_cells[0]

    can_place_at_new_pos = ship_not_near(
        field, new_head_x, new_head_y, len(ship_cells), new_position)
    if can_place_at_new_pos:
        for new_x, new_y in new_ship_cells:
            field[new_y][new_x] = SHIP
        print("Корабль успешно перемещен!")
        return True
    else:
        for x, y, state in original_cells_state:
            field[y][x] = state
        print("Невозможно переместить "
              "корабль на новую позицию (занято).")
        return False


def correct_field_size(field_size):
    x, y = field_size
    if x < 1 or y < 1 or x > 42 or y > 42:
        print("Введите корректные размеры (оба числа от 0 до 42)")
        return False

    min_d = min(x, y)
    max_d = max(x, y)
    min_sizes = {
        1: 30,
        2: 27,
        3: 18,
        4: 13,
        5: 11,
        6: 10,
        7: 8,
    }.get(min_d, 0)

    if min_d <= 7 and max_d < min_sizes:
        print(f"При {min_d=} {max_d} должен быть минимум {min_sizes}")
        return False

    return True


def set_up_mins(field):
    mins = []
    field_size_x = len(field[0])
    field_size_y = len(field)
    print(f"Расстановка мин на поле соперника")
    for i in range(5):
        while True:
            x, y = map(int, input(
                f"Введите координаты для {i + 1} "
                f"мины из {5} (x y): ").split())
            if (0 <= x < field_size_x and
                    0 <= y < field_size_y and (x, y) not in mins):
                mins.append((x, y))
                break
            elif (0 <= x < field_size_x and
                  0 <= y < field_size_y and (x, y) in mins):
                print("Мина уже в игре. Попробуйте еще раз.")
            else:
                print("Введите 2 числа в пределах поля")
    return mins


def check_mins(field, mins):
    damaged = False
    for x, y in mins:
        if field[y][x] == SHIP:
            damaged = True
            cages = find_ship_cages(field, x, y)
            for i, j in cages:
                field[j][i] = DAMAGED
            mark_around_ship(field, None, cages)
    return damaged
