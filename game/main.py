from game.field import make_field, print_field, check_ship_full_destroyed
from game.constans import SHIPS, FIELDSIZE_DEFAULT
from game.Ai import Ai
from game.utils import (random_setup_ships, game_over,
                        init_available_cells, manual_ship_placement,
                        record_score,
                        display_scores, move_ship,
                        correct_field_size, set_up_mins, check_mins)
from game.ship import random_place_ship
from game.player_move import (player_move_1v1, is_hit_classic,
                              player_move_classic)

try:
    import pygame
    import threading
    HAS_PYGAME = True
except ImportError:
    HAS_PYGAME = False


def play_music(file_path, volume=0.5):
    def music_worker():
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.set_volume(volume)
        pygame.mixer.music.play(loops=-1)

    thread = threading.Thread(target=music_worker, daemon=True)
    thread.start()


def run_1v1_game(field_size):
    """
    Запускает игру в режиме 1 на 1 с особыми правилами.
    """
    print("\n--- Режим Игры 1 на 1 ---")
    player1_name = input("Введите имя Игрока 1: ")
    player2_name = input("Введите имя Игрока 2: ")

    player1_field = make_field(field_size)
    player2_field = make_field(field_size)

    print(f"\nРасстановка кораблей для {player1_name}:")
    print("Выберите тип расстановки:")
    print("1 - Авто")
    print("2 - Ручная")
    choice1 = input("Ваш выбор (1/2): ")
    if choice1 == '1':
        random_setup_ships(player1_field)
    else:
        manual_ship_placement(player1_field)

    mins_on_player2_field = set_up_mins(player2_field)

    input("\nНажмите Enter, когда Игрок 2 "
          "будет готов расставить свои корабли.")

    print(f"\nРасстановка кораблей для {player2_name}:")
    print("Выберите тип расстановки:")
    print("1 - Авто")
    print("2 - Ручная")
    choice2 = input("Ваш выбор (1/2): ")
    if choice2 == '1':
        random_setup_ships(player2_field)
    else:
        manual_ship_placement(player2_field)

    mins_on_player1_field = set_up_mins(player1_field)

    current_player = 1

    while True:
        if current_player == 1:
            player_name = player1_name
            player_field = player1_field
            opponent_name = player2_name
            opponent_field = player2_field
            player_mins = mins_on_player1_field
            opponent_mins = mins_on_player2_field
        else:
            player_name = player2_name
            player_field = player2_field
            opponent_name = player1_name
            opponent_field = player1_field
            player_mins = mins_on_player2_field
            opponent_mins = mins_on_player1_field

        moved_ship_this_turn = False

        while True:
            if check_mins(opponent_field, opponent_mins):
                print(f"\nИгрок {opponent_name} подорвался на мине")
            if check_mins(player_field, player_mins):
                print(f"\nИгрок {player_name} подорвался на мине")
            print(f"\nХод игрока: {player_name}")
            print(f"\nВаше поле ({player_name}):")
            print_field(player_field, False, player_mins)
            print(f"\nПоле соперника ({opponent_name}):")
            print_field(opponent_field, True, opponent_mins)

            print("\nВыберите действие:")
            print("1. Стрелять")
            if not moved_ship_this_turn:
                print("2. Переместить корабль")
            print("3. Сдаться")
            action_choice = input("Ваш выбор: ")

            if action_choice == '1':
                damaged_cells = player_move_1v1(player_field, opponent_field)

                if len(damaged_cells) != 0:
                    for x, y in damaged_cells:
                        destroyed = (
                            check_ship_full_destroyed(opponent_field, x, y))
                        if destroyed:
                            if game_over(opponent_field):
                                print(f"\nПобедил {player_name}!")
                                input("\nНажмите Enter, "
                                      "чтобы вернуться в меню.")
                                return
                else:
                    print(f"{player_name} промахнулся!")
                    break

            elif action_choice == '2' and not moved_ship_this_turn:
                if move_ship(player_field):
                    moved_ship_this_turn = True
            elif action_choice == '3':
                print(f"\nПобедил {opponent_name}!")
                input("\nНажмите Enter, чтобы вернуться в меню.")
                return
            else:
                print("Некорректный выбор действия.")

        current_player = 2 if current_player == 1 else 1


def start_game(field_size):
    player_name = input("Введите свое имя: ")
    player_field = make_field(field_size)
    bot_field = make_field(field_size)
    player_available_cells = init_available_cells(field_size)
    ai = Ai()

    print("\nВыберите тип расстановки кораблей:")
    print("1 - Авто")
    print("2 - Ручная")
    choice = input("Ваш выбор (1/2): ")
    if choice == '1':
        random_setup_ships(player_field)
    else:
        manual_ship_placement(player_field)

    for count in SHIPS:
        for i in range(count):
            size_of_ship = SHIPS[count]
            random_place_ship(bot_field, size_of_ship)

    player_turn = True
    player_moves = 0

    while True:
        print("\nВаше игровое поле:")
        print_field(player_field, False)
        print("\nИгровое поле соперника:")
        print_field(bot_field, True)
        if player_turn:
            x, y = player_move_classic(bot_field)
            player_moves += 1
            if is_hit_classic(x, y, bot_field):
                print("Вы попали!")
                check_ship_full_destroyed(bot_field, x, y)
                player_turn = True
            else:
                print("Вы промахнулись!")
                player_turn = False
            if game_over(bot_field):
                print("Победа!")
                record_score(player_moves, player_name)
                break
        else:
            print("\nХод соперника:")
            x, y = ai.make_move(player_available_cells)
            print(x, y)
            player_available_cells.remove((x, y))
            if is_hit_classic(x, y, player_field):
                print("Соперник попал!")
                ai.register_hit(
                    x, y, check_ship_full_destroyed(
                        player_field, x, y, player_available_cells))
                player_turn = False
            else:
                print("Соперник промахнулся!")
                ai.register_miss()
                player_turn = True
        if game_over(player_field):
            print("\nВаше игровое поле:")
            print_field(player_field, False)
            print("\nИгровое поле соперника:")
            print_field(bot_field, True)
            print("Проигрыш!")
            break


def main():
    field_size = FIELDSIZE_DEFAULT
    if HAS_PYGAME:
        pygame.init()
        play_music("music.mp3", volume=0.3)
    while True:
        print("\n    Морской Бой    ")
        print("1. Начать игру против бота(классические правила)")
        print("2. Посмотреть таблицу рекордов")
        print("3. Изменить размер поля")
        print("4. Игра 1 на 1 (особые правила)")
        print("0. Выход")
        choice = input("Выберите пункт меню: ")

        if choice == '1':
            start_game(field_size)
        elif choice == '2':
            display_scores()
            input("\nНажмите Enter, чтобы вернуться в меню.")
        elif choice == '3':
            print("\nИзменение размера поля:")
            while True:
                field_size = tuple(map(
                    int, input(
                        "Введите размеры поля через пробел: ").split()))
                if len(field_size) != 2:
                    print("Ошибка: нужно ввести ровно два числа!")
                    continue
                if correct_field_size(field_size):
                    break
            input("\nНажмите Enter, чтобы вернуться в меню.")
        elif choice == '4':
            run_1v1_game(field_size)
        elif choice == '0':
            print("Спасибо за игру!")
            break
        else:
            print("Некорректный выбор. Введите число от 0 до 3.")


if __name__ == "__main__":
    main()
