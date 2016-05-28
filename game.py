from exceptions import *


class DalaGame(object):
    size = 6
    num_of_pieces = 12
    lost_condition = num_of_pieces - 2
    initial_condition = num_of_pieces - 2
    empty = -1

    drop_mode, move_mode, end_mode = range(3)

    def __init__(self, board=None, remains=None, lost=None, turn=None):
        if board is None:
            board = [[DalaGame.empty] * DalaGame.size
                     for _ in range(DalaGame.size)]
        else:
            board = [list(l) for l in board]

        if remains is None:
            remains = [DalaGame.num_of_pieces, DalaGame.num_of_pieces]
        else:
            remains = list(remains)

        if lost is None:
            lost = [0, 0]
        else:
            lost = list(lost)

        if turn is None:
            turn = 0

        self._board = board
        self._remains = remains
        self._lost = lost
        self._turn = turn

    def copy(self):
        return DalaGame(board=self._board,
                        remains=self._remains,
                        lost=self._lost,
                        turn=self._turn)

    def __eq__(self, other):
        if isinstance(other, DalaGame):
            return (self._board == other._board and
                    self._remains == other._remains and
                    self._lost == other._lost and self._turn == other._turn)

        else:
            return False

    def print_game(self):
        '''print game status for debugging'''

        num_to_symbol = {DalaGame.empty: ' ', 0: 'O', 1: 'X'}

        print('  = Dala Game =\n')
        print('   ' + ' '.join(str(i) for i in range(DalaGame.size)) + ' ')

        wall = '  *' + '*'.join('-' * DalaGame.size) + '*'
        print(wall)
        for i in range(DalaGame.size):
            status = '|'.join(num_to_symbol[x] for x in self._board[i])
            print('{} |{}|'.format(i, status))
            print(wall)

        print()
        for i in range(2):
            print('{} : {} pieces remain / {} pieces lost'.format(
                num_to_symbol[i], self._remains[i], self._lost[i]))
        print()
        if self.whos_turn() != DalaGame.empty:
            print('{}\'s turn'.format(num_to_symbol[self._turn]))

    def whos_turn(self):
        return self._turn

    def remains(self, player):
        return self._remains[player]

    def lost(self, player):
        return self._lost[player]

    def board(self):
        return [list(l) for l in self._board]

    def game_mode(self):
        if self.winner() is not None:
            return DalaGame.end_mode
        elif self._remains[self.whos_turn()] > 0:
            return DalaGame.drop_mode
        else:
            return DalaGame.move_mode

    def winner(self):
        for i in range(2):
            if self._lost[i] >= DalaGame.lost_condition:
                return self._compute_next_turn(i)
        return None

    def drop(self, player, position, capture=None):
        self._check_turn(player)

        initial_condition = self._remains[player] > DalaGame.initial_condition
        self._check_position(position, initial_condition=initial_condition)

        if self._remains[player] <= 0:
            raise IllegalMoveException('No pieces left')

        r, c = position

        self._board[r][c] = player
        original_remain = self._remains[player]
        self._remains[player] = original_remain - 1

        captured = self._is_drop_capture(player, position)

        try:
            self._check_capture(player, captured, capture)

            if captured:
                self._capture(player, capture)

        except GameOverException:
            self._next_turn(DalaGame.empty)
            raise

        except:
            self._board[r][c] = DalaGame.empty
            self._remains[player] = original_remain
            raise

        self._next_turn()

    def move(self, player, source, destination, capture=None):
        self._check_turn(player)
        self._check_position(source, check_occupied=False)
        self._check_position(destination)
        self._check_movable(player, source, destination)

        if self._remains[player] > 0:
            raise IllegalMoveException('Must drop first')

        self._board[source[0]][source[1]] = DalaGame.empty
        self._board[destination[0]][destination[1]] = player

        captured = self._is_move_capture(player, source, destination)

        try:
            self._check_capture(player, captured, capture)

            if captured:
                self._capture(player, capture)

        except GameOverException:
            self._next_turn(DalaGame.empty)
            raise

        except:
            self._board[source[0]][source[1]] = player
            self._board[destination[0]][destination[1]] = DalaGame.empty
            raise

        self._next_turn()

    def _capture(self, player, capture):
        self._board[capture[0]][capture[1]] = DalaGame.empty

        next_turn = self._compute_next_turn(player)
        self._lost[next_turn] += 1

        if self._lost[next_turn] >= DalaGame.lost_condition:
            raise GameOverException('player {} wins!'.format(player))

    def _next_turn(self, next_turn=None):
        if next_turn is None:
            self._turn = self._compute_next_turn(self._turn)
        else:
            self._turn = next_turn

    def _is_move_capture(self, player, source, destination):
        if self._is_drop_capture(player, destination):
            return True

        r, c = source

        row = self._board[r]
        col = [self._board[i][c] for i in range(DalaGame.size)]

        def check_capture(xs, i):
            '''check if there are three connected pieces'''
            left, right = self._compute_left_right(player, xs, i)

            return left == 3 or right == 3

        return check_capture(row, c) or check_capture(col, r)

    def _is_drop_capture(self, player, position):
        r, c = position

        row = self._board[r]
        col = [self._board[i][c] for i in range(DalaGame.size)]

        def check_capture(xs, i):
            '''check if there are three connected pieces'''
            left, right = self._compute_left_right(player, xs, i)

            return left + right + 1 == 3

        return check_capture(row, c) or check_capture(col, r)

    def _check_turn(self, player):
        if player != self._turn or player not in (0, 1):
            raise NotYourTurnException('Not your turn')

    def _check_capture(self, player, captured, position):
        if captured:
            if position is None:
                raise MustCaptureException('Must capture')
            else:
                r, c = position

                try:
                    self._check_position(position, check_occupied=False)

                except IllegalPositionException:
                    raise IllegalCapturePositionException(
                        'Illegal position: ({}, {})'.format(r, c))

                if self._board[r][c] != self._compute_next_turn(player):
                    raise IllegalCapturePositionException(
                        'Opponent\'s piece doesn\'t exist in capture position: ({}, {})'.format(
                            r, c))

        elif position is not None:
            raise MustNotCaptureException('Must not capture')

    def _check_position(self,
                        position,
                        check_occupied=True,
                        initial_condition=False):
        r, c = position
        if r >= DalaGame.size or r < 0 or c >= DalaGame.size or c < 0:
            raise IllegalPositionException(
                'Position out of scope: ({}, {})'.format(r, c))

        if check_occupied and self._board[r][c] != -1:
            raise AlreadyOccupiedException(
                'Position aleary occupied: ({}, {})'.format(r, c))

        if initial_condition:
            upper = DalaGame.size // 2
            lower = upper - 1
            if r > upper or r < lower or c > upper or c < lower:
                raise CentralNotOccupiedException(
                    'Central positions must be occupied first')

    def _check_movable(self, player, source, destination):
        r, c = source
        dr, dc = destination

        if self._board[r][c] != player:
            raise IllegalMovementException(
                'Not pieces to move at ({}, {})'.format(r, c))

        if source == destination:
            raise IllegalMovementException('Could not stay at the same place')

        if abs(r - dr) + abs(c - dc) != 1:
            raise IllegalMovementException('Could not move that far')

    def _compute_left_right(self, player, xs, i):
        '''check if there are connected pieces'''

        left = right = 0
        for j in range(i + 1, DalaGame.size):
            if xs[j] == player:
                right += 1
            else:
                break

        for j in range(i - 1, -1, -1):
            if xs[j] == player:
                left += 1
            else:
                break
        return left, right

    def _compute_next_turn(self, n):
        return (n + 1) % 2
