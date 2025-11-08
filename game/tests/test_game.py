import unittest
from io import StringIO
from unittest.mock import patch

from game.Ai import Ai
from game.field import (mark_around_ship, check_ship_full_destroyed,
                        make_field, print_field)
from game.main import main, start_game, run_1v1_game
from game.player_move import (is_hit_classic, is_hit_1v1,
                              player_move_1v1, player_move_classic)
from game.utils import (clear_field, game_over,
                        init_available_cells, place_ship_manual,
                        correct_field_size, set_up_mins,
                        check_mins, manual_ship_placement, move_ship)
from game.ship import ship_not_near, random_place_ship, find_ship_cages
from game.constans import EMPTY, SHIP, DAMAGED, MISSED, CROSSING, LINE


class TestShipPlacement(unittest.TestCase):
    def setUp(self):
        self.field = [[EMPTY for i in range(10)] for j in range(10)]
        self.field[3][3] = SHIP
        self.field[3][4] = SHIP

    def test_ship_not_near_horizontal_valid(self):
        self.assertTrue(ship_not_near(self.field, 0, 0, 3, 'h'))

    def test_ship_not_near_vertical_valid(self):
        self.assertTrue(ship_not_near(self.field, 0, 0, 3, 'v'))

    def test_ship_not_near_too_close(self):
        self.assertFalse(ship_not_near(self.field, 2, 2, 3, 'h'))

    def test_ship_not_near_out_of_bounds(self):
        self.assertFalse(ship_not_near(self.field, 9, 0, 3, 'h'))
        self.assertFalse(ship_not_near(self.field, 0, 9, 3, 'v'))

    def test_ship_not_near_overlap(self):
        self.assertFalse(ship_not_near(self.field, 3, 4, 3, 'h'))

    def test_random_place_ship_success(self):
        result = random_place_ship(self.field, 3)
        self.assertTrue(result)
        ship_count = sum(cell == SHIP for row in self.field for cell in row)
        self.assertEqual(ship_count, 5)

    def test_random_place_ship_failure(self):
        filled_field = [[SHIP for _ in range(10)] for _ in range(10)]
        result = random_place_ship(filled_field, 3)
        self.assertFalse(result)

    def test_find_ship_cages_horizontal(self):
        test_field = [[EMPTY for _ in range(10)] for _ in range(10)]
        test_field[3][3] = DAMAGED
        test_field[3][4] = SHIP
        test_field[3][5] = DAMAGED
        cages = find_ship_cages(test_field, 4, 3)
        expected = [(3, 3), (4, 3), (5, 3)]
        self.assertCountEqual(cages, expected)

    def test_find_ship_cages_vertical(self):
        test_field = [[EMPTY for _ in range(10)] for _ in range(10)]
        test_field[2][5] = SHIP
        test_field[3][5] = DAMAGED
        test_field[4][5] = SHIP
        cages = find_ship_cages(test_field, 5, 3)
        expected = [(5, 2), (5, 3), (5, 4)]
        self.assertCountEqual(cages, expected)

    def test_find_ship_cages_single(self):
        test_field = [[EMPTY for _ in range(10)] for _ in range(10)]
        test_field[7][7] = DAMAGED
        cages = find_ship_cages(test_field, 7, 7)
        self.assertEqual(cages, [(7, 7)])


class TestAi(unittest.TestCase):
    def setUp(self):
        self.ai = Ai()
        self.available_cells = {(x, y) for x in range(10) for y in range(10)}

    def test_move_after_first_hit(self):
        self.ai.register_hit(4, 4)
        self.available_cells.remove((4, 4))
        possible_moves = {(3, 4), (5, 4), (4, 3), (4, 5)}
        move = self.ai.make_move(self.available_cells)
        self.assertIn(move, possible_moves)

    def test_move_in_direction_after_second_hit(self):
        self.ai.register_hit(4, 4)
        self.ai.register_hit(5, 4)
        self.available_cells.remove((4, 4))
        self.available_cells.remove((5, 4))
        move = self.ai.make_move(self.available_cells)
        self.assertEqual(move, (6, 4))

    def test_ai_change_direction_after_blocked(self):
        self.ai.first_hit = (2, 2)
        self.ai.last_hit = (3, 2)
        self.ai.direction = (1, 0)
        available_cells = {(2, 2), (1, 2)}

        move = self.ai.make_move(available_cells)
        self.assertEqual(move, (1, 2))

    def test_ai_change_direction_after_blocked_2(self):
        self.ai.first_hit = (2, 2)
        self.ai.last_hit = (3, 2)
        self.ai.direction = (1, 0)
        available_cells = {(2, 2)}

        move = self.ai.make_move(available_cells)
        self.assertEqual(None, self.ai.direction)

    def test_ai_register_hit_with_large_jump(self):
        self.ai.register_hit(2, 2)
        self.ai.register_hit(5, 2)
        self.assertEqual(self.ai.direction, (1, 0))
        self.ai.register_hit(4, 4)
        self.ai.register_hit(1, 4)
        self.assertEqual(self.ai.direction, (-1, 0))

    def test_register_first_hit(self):
        self.ai.register_hit(3, 3)
        self.assertEqual(self.ai.first_hit, (3, 3))
        self.assertEqual(self.ai.last_hit, (3, 3))
        self.assertIsNone(self.ai.direction)

    def test_register_second_hit_vertical(self):
        self.ai.register_hit(3, 3)
        self.ai.register_hit(3, 4)
        self.assertEqual(self.ai.direction, (0, 1))

    def test_register_second_hit_horizontal(self):
        self.ai.register_hit(3, 3)
        self.ai.register_hit(4, 3)
        self.assertEqual(self.ai.direction, (1, 0))

    def test_register_ship_destroyed(self):
        self.ai.register_hit(3, 3)
        self.ai.register_hit(3, 4, is_ship_destroyed=True)
        self.assertIsNone(self.ai.first_hit)
        self.assertIsNone(self.ai.last_hit)
        self.assertIsNone(self.ai.direction)

    def test_register_miss_after_direction(self):
        self.ai.register_hit(3, 3)
        self.ai.register_hit(3, 4)
        self.ai.register_miss()
        self.assertEqual(self.ai.direction, (0, -1))
        self.assertEqual(self.ai.last_hit, (3, 3))

    def test_make_move_after_miss(self):
        self.ai.register_hit(3, 3)
        self.ai.register_hit(3, 4)
        self.ai.register_miss()
        move = self.ai.make_move(self.available_cells)
        self.assertEqual(move, (3, 2))


class TestShipDestruction(unittest.TestCase):
    def setUp(self):
        self.field = [[EMPTY for _ in range(5)] for _ in range(5)]

    def test_mark_around_horizontal_ship(self):
        self.field[2][1] = DAMAGED
        self.field[2][2] = DAMAGED
        ship_cells = [(1, 2), (2, 2)]
        mark_around_ship(self.field, None, ship_cells)
        expected_missed = {
            (0, 1), (0, 2), (0, 3), (1, 1), (1, 3), (2, 1), (2, 3),
            (3, 1), (3, 2), (3, 3)}

        for x, y in expected_missed:
            self.assertEqual(self.field[y][x], MISSED)

    def test_check_ship_full_destroyed_true(self):
        self.field[1][1] = DAMAGED
        self.field[1][2] = DAMAGED

        result = check_ship_full_destroyed(self.field, 1, 1)
        self.assertTrue(result)
        self.assertEqual(self.field[0][0], MISSED)
        self.assertEqual(self.field[2][3], MISSED)

    def test_check_ship_full_destroyed_false(self):
        self.field[3][3] = DAMAGED
        self.field[3][4] = SHIP

        result = check_ship_full_destroyed(self.field, 3, 3)
        self.assertFalse(result)

    def test_mark_around_edge_ship(self):
        self.field[4][4] = DAMAGED
        result = check_ship_full_destroyed(self.field, 4, 4)
        self.assertTrue(result)
        expected_missed = {(3, 3), (3, 4), (4, 3)}
        for x, y in expected_missed:
            self.assertEqual(self.field[y][x], MISSED)

    def test_make_field(self):
        temp_field = make_field((5, 5))
        self.assertEqual(self.field, temp_field)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_field_show_all(self, mock_stdout):
        self.field[1][1] = SHIP
        print_field(self.field, hide_ships=False)
        output = mock_stdout.getvalue()

        self.assertIn("     0   1   2   3   4", output)
        self.assertIn("0 │   │   │   │   │   │", output)
        self.assertIn("1 │   │ ■ │   │   │   │", output)
        self.assertIn(CROSSING, output)
        self.assertIn(LINE, output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_print_field_hide_ships(self, mock_stdout):
        self.field[1][1] = SHIP
        print_field(self.field, hide_ships=True)
        output = mock_stdout.getvalue()

        self.assertIn("     0   1   2   3   4", output)
        self.assertIn("0 │   │   │   │   │   │", output)
        self.assertIn("1 │   │   │   │   │   │", output)
        self.assertIn(CROSSING, output)
        self.assertIn(LINE, output)


class TestPlayerMoves(unittest.TestCase):
    def setUp(self):
        self.enemy_field = [[EMPTY for _ in range(5)] for _ in range(5)]
        self.enemy_field[2][2] = SHIP

    def test_is_hit_classic_hit(self):
        result = is_hit_classic(2, 2, self.enemy_field)
        self.assertTrue(result)
        self.assertEqual(self.enemy_field[2][2], DAMAGED)

    def test_is_hit_classic_miss(self):
        result = is_hit_classic(1, 1, self.enemy_field)
        self.assertFalse(result)
        self.assertEqual(self.enemy_field[1][1], MISSED)

    def test_is_hit_1v1_hit(self):
        result = is_hit_1v1(2, 2, self.enemy_field)
        self.assertTrue(result)
        self.assertEqual(self.enemy_field[2][2], DAMAGED)


class TestGameLogic(unittest.TestCase):
    def setUp(self):
        self.field = [[EMPTY for _ in range(10)] for _ in range(10)]

    def test_clear_field(self):
        self.field[0][0] = SHIP
        self.field[1][1] = DAMAGED
        clear_field(self.field)
        for row in self.field:
            self.assertTrue(all(cell == EMPTY for cell in row))

    def test_game_over_true(self):
        self.assertTrue(game_over(self.field))

    def test_game_over_false(self):
        self.field[0][0] = SHIP
        self.assertFalse(game_over(self.field))

    def test_init_available_cells(self):
        cells = init_available_cells((10, 10))
        self.assertEqual(len(cells), 100)

    def test_place_ship_manual_horizontal(self):
        result = place_ship_manual(self.field, 3, 0, 0, 'h')
        self.assertTrue(result)
        self.assertEqual(self.field[0][0], SHIP)
        self.assertEqual(self.field[0][1], SHIP)
        self.assertEqual(self.field[0][2], SHIP)

    def test_place_ship_manual_vertical(self):
        result = place_ship_manual(self.field, 3, 0, 0, 'v')
        self.assertTrue(result)
        self.assertEqual(self.field[0][0], SHIP)
        self.assertEqual(self.field[1][0], SHIP)
        self.assertEqual(self.field[2][0], SHIP)

    def test_place_ship_manual_invalid_position(self):
        self.field[0][0] = SHIP
        result = place_ship_manual(self.field, 3, 0, 0, 'h')
        self.assertFalse(result)

    def test_correct_field_size_valid(self):
        self.assertTrue(correct_field_size((10, 10)))
        self.assertTrue(correct_field_size((7, 8)))

    def test_correct_field_size_invalid(self):
        self.assertFalse(correct_field_size((0, 0)))
        self.assertFalse(correct_field_size((3, 3)))

    @patch('builtins.input', side_effect=['0 0', '1 1', '2 2', '3 3', '4 4'])
    def test_set_up_mins(self, mock_input):
        mins = set_up_mins(self.field)
        self.assertEqual(len(mins), 5)
        self.assertEqual(mins, [(0, 0), (1, 1), (2, 2), (3, 3), (4, 4)])

    def test_check_mins(self):
        self.field[0][0] = SHIP
        self.field[1][1] = SHIP
        damaged = check_mins(self.field, [(0, 0), (2, 2)])
        self.assertTrue(damaged)
        self.assertEqual(self.field[0][0], DAMAGED)
        self.assertEqual(self.field[1][1], SHIP)

    @patch('builtins.input', side_effect=['0 0 v', '0 2 v',
                                          '0 4 v', '0 6 v',
                                          '2 0 v', '2 3 v',
                                          '2 6 v', '4 0 v',
                                          '4 4 v', '6 0 v'])
    @patch('game.utils.place_ship_manual', side_effect=[True, True, True, True,
                                                        True, True, True, True,
                                                        True, True])
    @patch('sys.stdout', new_callable=StringIO)
    def test_successful_placement(self, mock_stdout, mock_place, mock_input):
        manual_ship_placement(self.field)
        self.assertEqual(mock_place.call_count, 10)
        output = mock_stdout.getvalue()
        self.assertIn("Размещаем корабль длиной 2", output)
        self.assertIn("Размещаем корабль длиной 3", output)

    @patch('builtins.input', side_effect=['0 0', '0 0',
                                          '1 1', '2 2', '3 3', '4 4'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_duplicate_mines(self, mock_stdout, mock_input):
        mines = set_up_mins(self.field)
        output = mock_stdout.getvalue()
        self.assertIn("Мина уже в игре. Попробуйте еще раз.", output)

    @patch('builtins.input', side_effect=['10 10', '0 0', '-1 0',
                                          '1 1', '2 2', '3 3', '4 4'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_out_of_bounds(self, mock_stdout, mock_input):
        mines = set_up_mins(self.field)
        output = mock_stdout.getvalue()
        self.assertIn("Введите 2 числа в пределах поля", output)

    @patch('builtins.input', side_effect=['1 1', 'вправо'])
    def test_move_ship_success(self, mock_input):
        field = [
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, SHIP, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, DAMAGED, EMPTY]
        ]
        result = move_ship(field)
        self.assertTrue(result)
        self.assertEqual(field[1][2], SHIP)
        self.assertEqual(field[1][1], EMPTY)

    @patch('builtins.input', side_effect=['1 1', 'вниз'])
    def test_move_ship_success2(self, mock_input):
        field = [
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, SHIP, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, SHIP, EMPTY]
        ]
        result = move_ship(field)
        self.assertFalse(result)
        self.assertEqual(field[1][1], SHIP)

    @patch('builtins.input', side_effect=['1 1', 'влево'])
    def test_move_ship_success3(self, mock_input):
        field = [
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, SHIP, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, SHIP, EMPTY]
        ]
        result = move_ship(field)
        self.assertTrue(result)

    @patch('builtins.input', side_effect=['1 1', 'вверх'])
    def test_move_ship_success4(self, mock_input):
        field = [
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, SHIP, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, SHIP, EMPTY]
        ]
        result = move_ship(field)
        self.assertTrue(result)

    @patch('builtins.input', side_effect=['1 1', 'неверное'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_invalid_direction(self, mock_stdout, mock_input):
        field = [
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, SHIP, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, SHIP, EMPTY]
        ]
        result = move_ship(field)
        self.assertFalse(result)

    @patch('builtins.input', side_effect=['0 0'])
    def test_move_ship_not_success(self, mock_input):
        field = [
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, SHIP, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, DAMAGED, EMPTY]
        ]
        result = move_ship(field)
        self.assertFalse(result)


class TestMainMenu(unittest.TestCase):
    @patch('builtins.input', side_effect=['0'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_menu_exit(self, mock_stdout, mock_input):
        main()
        self.assertIn("Спасибо за игру!", mock_stdout.getvalue())

    @patch('builtins.input', side_effect=['3', "10 10", ' ', '0'])
    @patch('sys.stdout', new_callable=StringIO)
    def test_main_menu_exit(self, mock_stdout, mock_input):
        main()
        self.assertIn("\nИзменение размера поля:", mock_stdout.getvalue())

    @patch('builtins.input', side_effect=['2', '', '0'])
    @patch('game.main.display_scores')
    def test_main_menu_scores(self, mock_scores, mock_input):
        main()
        mock_scores.assert_called_once()

    @patch('builtins.input', side_effect=['TestPlayer', '1', 'да'])
    @patch('game.main.print_field')
    @patch('game.main.is_hit_classic', return_value=False)
    @patch('game.main.player_move_classic', return_value=(0, 0))
    def test_game_flow(self, mock_move, mock_hit, mock_print, mock_input):
        with patch('game.main.game_over', side_effect=[False, False, True]):
            start_game((10, 10))
            self.assertTrue(mock_move.called)
            self.assertTrue(mock_hit.called)

    @patch('builtins.input', side_effect=['TestPlayer', '1', 'да'])
    @patch('game.main.print_field')
    @patch('game.main.is_hit_classic', return_value=False)
    @patch('game.main.player_move_classic', return_value=(0, 0))
    def test_game_flow_2(self, mock_move, mock_hit, mock_print, mock_input):
        with patch('game.main.game_over', side_effect=[True]):
            start_game((10, 10))
            self.assertTrue(mock_move.called)
            self.assertTrue(mock_hit.called)

    @patch('builtins.input', side_effect=[
        'Player1', 'Player2',
        '1', 'да',
        '0 0', '0 1', '0 2', '0 3', '0 4',
        '',
        '1', 'да',
        '0 0', '0 1', '0 2', '0 3', '0 4',
        '1',
        '0 0',
        '0 0',
        '3',
        ''
    ])
    @patch('game.main.player_move_1v1', return_value=[(0, 0)])
    @patch('game.main.check_mins', return_value=True)
    @patch('game.main.game_over', side_effect=[False, True])
    def test_1v1_flow(self, mock_over, mock_mins, mock_move, mock_input):
        run_1v1_game((10, 10))
        self.assertTrue(mock_mins.called)
        self.assertTrue(mock_move.called)

    @patch('builtins.input', side_effect=[
        'Player1', 'Player2',
        '1', 'да',
        '0 0', '0 1', '0 2', '0 3', '0 4',
        '',
        '1', 'да',
        '0 0', '0 1', '0 2', '0 3', '0 4',
        '1',
        '0 0',
        '0 0',
        '3',
        ''
    ])
    @patch('game.main.player_move_1v1', return_value=[])
    @patch('game.main.check_mins', return_value=True)
    @patch('game.main.game_over', side_effect=[False, True])
    def test_1v1_flow2(self, mock_over, mock_mins, mock_move, mock_input):
        run_1v1_game((10, 10))
        self.assertTrue(mock_mins.called)
        self.assertTrue(mock_move.called)


class TestPlayerMove1v1(unittest.TestCase):
    def setUp(self):
        self.player_field = [
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, SHIP, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY]
        ]

        self.enemy_field = [
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY],
            [EMPTY, EMPTY, EMPTY, EMPTY, EMPTY]
        ]

    @patch('builtins.input', side_effect=['1 1', '2 2'])
    @patch('random.choice', return_value=(2, 3))
    @patch('game.player_move.is_hit_1v1', return_value=True)
    @patch('sys.stdout', new_callable=StringIO)
    def test_successful_move(self, mock_stdout, mock_hit,
                             mock_random, mock_input):
        """Тест успешного хода с попаданием"""
        damaged = player_move_1v1(self.player_field, self.enemy_field)
        self.assertEqual(damaged, [(2, 2), (2, 3)])
        output = mock_stdout.getvalue()
        self.assertIn("Игрок выстрелил 2-палубным кораблем", output)

    @patch('builtins.input', side_effect=['10 10', '1 1', '2 2'])
    @patch('random.choice', return_value=(2, 3))
    @patch('sys.stdout', new_callable=StringIO)
    def test_invalid_ship_coordinates(self, mock_stdout,
                                      mock_random, mock_input):
        """Тест неверных координат корабля"""
        damaged = player_move_1v1(self.player_field, self.enemy_field)
        output = mock_stdout.getvalue()
        self.assertIn("Некорректные координаты корабля", output)

    @patch('builtins.input', side_effect=['0 0', '1 1', '2 2'])
    @patch('random.choice', return_value=(2, 3))
    @patch('sys.stdout', new_callable=StringIO)
    def test_no_ship_at_coordinates(self, mock_stdout,
                                    mock_random, mock_input):
        """Тест выбора клетки без корабля"""
        damaged = player_move_1v1(self.player_field, self.enemy_field)
        output = mock_stdout.getvalue()
        self.assertIn("нет вашего неподбитого корабля", output)

    @patch('builtins.input', side_effect=['1 1', '2 2'])
    @patch('random.choice', return_value=(2, 3))
    @patch('game.player_move.is_hit_1v1', side_effect=[True, False])
    def test_partial_hit(self, mock_hit, mock_random, mock_input):
        """Тест частичного попадания"""
        damaged = player_move_1v1(self.player_field, self.enemy_field)
        self.assertEqual(len(damaged), 1)

    @patch('builtins.input', side_effect=['1 1', '2 2'])
    @patch('random.choice', return_value=(2, 3))
    @patch('game.player_move.is_hit_1v1', return_value=False)
    def test_miss_all_shots(self, mock_hit, mock_random, mock_input):
        """Тест полного промаха"""
        damaged = player_move_1v1(self.player_field, self.enemy_field)
        self.assertEqual(damaged, [])

    @patch('builtins.input', side_effect=['1 1', 'a b', '2 2'])
    @patch('random.choice', return_value=(2, 3))
    @patch('sys.stdout', new_callable=StringIO)
    def test_invalid_shot_input(self, mock_stdout, mock_random, mock_input):
        """Тест неверного формата ввода выстрела"""
        damaged = player_move_1v1(self.player_field, self.enemy_field)
        output = mock_stdout.getvalue()
        self.assertIn("Ошибка. Введите два числа через пробел", output)


class TestPlayerMoveClassic(unittest.TestCase):
    def setUp(self):
        self.field = [
            [EMPTY, EMPTY, EMPTY],
            [EMPTY, SHIP, EMPTY],
            [EMPTY, EMPTY, EMPTY]
        ]

    @patch('builtins.input', side_effect=['1 1'])
    def test_valid_move(self, mock_input):
        result = player_move_classic(self.field)
        self.assertEqual(result, (1, 1))

    @patch('builtins.input', side_effect=['1 1', '0 0'])
    def test_already_taken_cell(self, mock_input):
        player_move_classic(self.field)
        result = player_move_classic(self.field)
        self.assertEqual(result, (0, 0))


if __name__ == '__main__':
    unittest.main()
