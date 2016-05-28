import random
import unittest

from game import DalaGame

from exceptions import *


class InitialGameSets(unittest.TestCase):
    def setUp(self):
        self.empty_game = get_empty_game()
        self.middle_game = get_middle_game()
        self.alt_middle_game = get_alt_middle_game()
        self.end_game = get_end_game()


class TestWinningCondition(InitialGameSets):
    pass


class TestProgress(InitialGameSets):
    def setUp(self):
        super().setUp()

        num_of_positions = DalaGame.size * DalaGame.size
        num_of_pieces = DalaGame.num_of_pieces * 2
        expected_drops = num_of_pieces * num_of_positions * 2
        expected_moves = num_of_pieces * 9 * num_of_positions * num_of_pieces

        self.maximum_num_of_step = (expected_drops + expected_moves) * 6

    def test_must_end(self):
        '''Game must end'''

        for _ in range(50):
            dgame = self.empty_game.copy()
            remains = [dgame.remains(0), dgame.remains(1)]
            lost = [dgame.lost(0), dgame.lost(1)]

            try:
                step = 0
                now_turn = 0
                while True:
                    step += 1
                    if step > self.maximum_num_of_step:
                        break

                    pos = random_position()
                    cpos = None

                    mode = dgame.game_mode()
                    if mode == DalaGame.drop_mode:

                        def one_step():
                            dgame.drop(now_turn, pos, cpos)

                            self.assertEqual(
                                dgame.remains(now_turn) + 1, remains[now_turn])
                            remains[now_turn] -= 1

                    elif mode == DalaGame.move_mode:
                        dpos = random_move(pos)
                        one_step = lambda: dgame.move(now_turn, pos, dpos, cpos)

                    try:
                        one_step()
                        now_turn = (now_turn + 1) % 2

                    except MustCaptureException:
                        while True:
                            step += 1
                            if step > self.maximum_num_of_step:
                                break

                            cpos = random_position()

                            try:
                                one_step()
                                now_turn = (now_turn + 1) % 2
                                self.assertEqual(
                                    dgame.lost(now_turn), lost[now_turn] + 1)
                                self.assertEqual(
                                    dgame._board[cpos[0]][cpos[1]],
                                    DalaGame.empty)
                                lost[now_turn] += 1
                                # break out of try capture loop
                                break

                            except GameOverException:
                                raise
                            except DalaException:
                                continue

                    except DalaException:
                        continue

                self.fail('game dose not end in {} iterations'.format(
                    self.maximum_num_of_step))

            except GameOverException:
                self.assertEqual(dgame.game_mode(), DalaGame.end_mode)

            except Exception as e:
                self.fail('unexpected Exception raised: {}!'.format(e))

    def test_no_change(self):
        '''Game configuration must not change when exceptions occur'''
        try:
            dgame = self.empty_game.copy()
            now_turn = dgame.whos_turn()

            while True:
                ngame = dgame.copy()

                pos = random_position()
                cpos = None

                mode = ngame.game_mode()
                if mode == DalaGame.drop_mode:
                    one_step = lambda: ngame.drop(now_turn, pos, cpos)

                elif mode == DalaGame.move_mode:
                    dpos = random_move(pos)
                    one_step = lambda: ngame.move(now_turn, pos, dpos, cpos)

                try:
                    one_step()
                    now_turn = (now_turn + 1) % 2
                    dgame = ngame

                except MustCaptureException:
                    self.assertEqual(ngame, dgame)

                    while True:
                        cpos = random_position()

                        try:
                            one_step()
                            now_turn = (now_turn + 1) % 2
                            dgame = ngame
                            # break out of try capture loop
                            break

                        except GameOverException:
                            raise
                        except DalaException:
                            self.assertEqual(ngame, dgame)
                            continue

                except DalaException:
                    continue

        except GameOverException:
            pass

        except Exception as e:
            self.fail('unexpected Exception raised: {}!'.format(e))


class TestIllegalMoves(InitialGameSets):
    def test_turn(self):
        '''Game must alternate turns properly'''
        dgame = self.empty_game.copy()
        self.assertEqual(dgame.whos_turn(),
                         0,
                         msg='Game does not start with player 0')

        q = DalaGame.size // 2
        p = q - 1

        # test first two drops
        dgame.drop(0, (q, q))
        self.assertEqual(dgame.whos_turn(), 1)

        dgame.drop(1, (p, p))
        self.assertEqual(dgame.whos_turn(), 0)

        # test capture drops
        dgame = self.middle_game.copy()
        self.assertEqual(dgame.whos_turn(), 0)

        dgame.drop(0, (p, q + 1), (q, q))
        self.assertEqual(dgame.whos_turn(), 1)

        dgame.drop(1, (q, q))
        self.assertEqual(dgame.whos_turn(), 0)

        # test move
        dgame = self.end_game.copy()
        self.assertEqual(dgame.whos_turn(), 0)

        dgame.move(0, (3, 1), (3, 0))
        self.assertEqual(dgame.whos_turn(), 1)

        dgame.move(1, (0, 2), (0, 1))
        self.assertEqual(dgame.whos_turn(), 0)

    def test_initial_drops(self):
        '''Central pieces must be occupied first'''
        dgame = self.empty_game.copy()

        four_steps = [(i, j) for i in range(2, 4) for j in range(2, 4)]
        random.shuffle(four_steps)

        now_turn = dgame.whos_turn()

        for it in range(4):
            for i in range(DalaGame.size):
                for j in range(DalaGame.size):

                    def illegal_move():
                        dgame.drop(now_turn, (i, j))

                    if 2 <= i <= 3 and 2 <= j <= 3:
                        continue
                    else:
                        # must drop at central positions
                        self.assertRaises(CentralNotOccupiedException,
                                          illegal_move)
            try:
                dgame.drop(now_turn, four_steps[it])
            except Exception as e:
                self.fail('unexpected Exception raised: {}!'.format(e))

            now_turn = (now_turn + 1) % 2

        total_capture_exceptions = 0
        for i in range(DalaGame.size):
            for j in range(DalaGame.size):
                ngame = dgame.copy()

                def legal_move():
                    ngame.drop(now_turn, (i, j))

                if 2 <= i <= 3 and 2 <= j <= 3:
                    self.assertRaises(AlreadyOccupiedException, legal_move)
                else:
                    try:
                        ngame.drop(now_turn, (i, j))

                    except MustCaptureException as e:
                        total_capture_exceptions += 1

                    except Exception as e:
                        self.fail('unexpected Exception raised: {}!'.format(e))

        self.assertIn(total_capture_exceptions, (0, 2))

    def test_drop_out_of_scope(self):
        '''Pieces must not be dropped out of scope'''
        dgame = self.middle_game.copy()

        for i in range(-1, DalaGame.size + 1):
            for j in range(-1, DalaGame.size + 1):

                def drop():
                    dgame.drop(0, (i, j))

                if 0 <= i < DalaGame.size and 0 <= j < DalaGame.size:
                    try:
                        ngame = dgame.copy()
                        ngame.drop(0, (i, j))

                    except MustCaptureException:
                        pass

                    except AlreadyOccupiedException:
                        pass

                    except Exception as e:
                        self.fail('unexpected Exception raised: {}!'.format(e))

                else:
                    self.assertRaises(IllegalPositionException, drop)

    def test_drop_occupied(self):
        '''Pieces must not be dropped on other pieces'''
        dgame = self.alt_middle_game.copy()

        for i in range(DalaGame.size):
            for j in range(DalaGame.size):
                ngame = dgame.copy()

                if 2 <= i <= 3 and 2 <= j <= 3:

                    def drop():
                        ngame.drop(0, (i, j))

                    self.assertRaises(AlreadyOccupiedException, drop)

                else:
                    ngame.drop(0, (i, j))

                    def drop():
                        ngame.drop(1, (i, j))

                    # Illegal 2nd drop
                    self.assertRaises(AlreadyOccupiedException, drop)

                    # Legal 2nd drops
                    for k in range(DalaGame.size):
                        for l in range(DalaGame.size):
                            if ngame._board[k][l] == DalaGame.empty:
                                mgame = ngame.copy()

                                try:
                                    mgame.drop(1, (k, l))

                                except MustCaptureException:
                                    pass

                                except Exception as e:
                                    self.fail(
                                        'unexpected Exception raised: {}!'.format(
                                            e))

    def test_premature_move(self):
        '''Moves must occur after all pieces are dropped'''
        dgame = self.middle_game.copy()

        q = DalaGame.size // 2
        p = q - 1

        def move():
            dgame.move(0, (p, p), (p, p - 1))

        self.assertRaises(IllegalMoveException, move)

    def test_illegal_move(self):
        '''Move positions must be checked'''
        dgame = self.end_game.copy()

        for i in range(DalaGame.size):
            for j in range(DalaGame.size):
                for k in range(-2, 3):
                    for l in range(-2, 3):
                        ngame = dgame.copy()

                        ni = i + k
                        nj = j + l

                        def move():
                            ngame.move(0, (i, j), (ni, nj))

                        if 0 <= ni < DalaGame.size and 0 <= nj < DalaGame.size:
                            is_occupied = ngame._board[ni][
                                nj] != DalaGame.empty
                            does_not_have_piece = ngame._board[i][j] != 0
                            does_not_move = ni == i and nj == j
                            is_too_far = (k != 0 and
                                          l != 0) or abs(k) > 1 or abs(l) > 1

                            if is_occupied:
                                self.assertRaises(AlreadyOccupiedException,
                                                  move)
                            elif does_not_have_piece or does_not_move or is_too_far:
                                self.assertRaises(IllegalMovementException,
                                                  move)
                            else:
                                try:
                                    move()
                                except Exception as e:
                                    self.fail(
                                        'unexpected Exception raised: {}!'.format(
                                            e))

                        else:
                            self.assertRaises(IllegalPositionException, move)

    def test_illegal_capture(self):
        '''Capture positions must be checked'''
        dgame = self.middle_game.copy()
        egame = self.end_game.copy()
        egame.move(0, (2, 4), (2, 5))

        q = DalaGame.size // 2
        p = q - 1

        def could_not_capture():
            dgame.drop(0, (p - 1, p), (q, p))

        self.assertRaises(MustNotCaptureException, could_not_capture)

        def could_not_capture_on_move():
            egame.move(1, (0, 4), (0, 5), (0, 3))

        self.assertRaises(MustNotCaptureException, could_not_capture_on_move)

        for i in range(-1, DalaGame.size + 1):
            for j in range(-1, DalaGame.size + 1):
                out_of_scope = i < 0 or i >= DalaGame.size or j < 0 or j >= DalaGame.size
                if out_of_scope or dgame._board[i][j] != 1:

                    def illegal_capture():
                        dgame.drop(0, (p, q + 1), (i, j))

                    self.assertRaises(IllegalCapturePositionException,
                                      illegal_capture)

                if out_of_scope or egame._board[i][j] != 0:

                    def illegal_capture_on_move():
                        egame.move(1, (2, 3), (2, 4), (i, j))

                    self.assertRaises(IllegalCapturePositionException,
                                      illegal_capture_on_move)


def get_empty_game():
    return DalaGame()


def get_middle_game():
    middle_game = DalaGame()
    q = DalaGame.size // 2
    p = q - 1
    middle_game._board[p][p] = 0
    middle_game._board[p][q] = 0
    middle_game._board[q][p] = 1
    middle_game._board[q][q] = 1
    middle_game._remains = [DalaGame.initial_condition,
                            DalaGame.initial_condition]
    return middle_game


def get_alt_middle_game():
    middle_game = DalaGame()
    q = DalaGame.size // 2
    p = q - 1
    middle_game._board[p][p] = 0
    middle_game._board[q][q] = 0
    middle_game._board[q][p] = 1
    middle_game._board[p][q] = 1
    middle_game._remains = [DalaGame.initial_condition,
                            DalaGame.initial_condition]
    return middle_game


def get_end_game():
    _ = DalaGame.empty

    board = [
        [_, _, 1, 0, 1, _],
        [_, 1, 0, 0, 1, _],
        [1, 0, 0, 1, 0, _],
        [_, 0, 1, 0, 0, 1],
        [_, 1, 0, 0, 1, _],
        [_, 1, 0, 1, _, _]
    ] # yapf: disable

    end_game = DalaGame(board=board, remains=[0, 0])

    return end_game


def random_position():
    return (random.randint(0, DalaGame.size), random.randint(0, DalaGame.size))


def random_move(source):
    r, c = source

    dr = r + random.randint(-1, 1)
    dc = c + random.randint(-1, 1)

    return (dr, dc)


if __name__ == '__main__':
    unittest.main(verbosity=2)
