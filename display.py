import os
import random

import pygame

from game import DalaGame


class Colors(object):
    black = (0, 0, 0)
    white = (255, 255, 255)
    yellow = (255, 250, 105)
    green = (0, 240, 0)
    lite_black = (40, 40, 40)
    lite_white = (215, 215, 215)
    board_background = (213, 165, 77)
    board_wall = (109, 71, 0)
    game_title = white
    game_background = black

    piece_colors = [black, white]
    drop_candidate_colors = [lite_black, lite_white]
    capture_candidate_colors = [yellow, yellow]
    source_candidate_colors = [green, green]


class Display(object):
    board_x = 40
    board_y = 40

    def __init__(self, title, clock):
        self.surface = pygame.display.set_mode((600, 400))
        self.title = title

        pygame.display.set_caption(title)

        self.clock = clock
        self.board = Board()

        self.surface.fill(Colors.game_background)
        pygame.display.update()

    def get_board_position(self, coordinate):
        if coordinate is not None:
            x, y = coordinate
            pos = (x - Display.board_x, y - Display.board_y)
            return self.board.get_position(pos)

        else:
            return None

    def display_opening(self):
        title = Title(self.title)
        title.draw(self.surface, clock=self.clock)

    def draw_board(self, dala_game):
        self.board.update(dala_game)
        self.board.draw(self.surface, (Display.board_x, Display.board_y))

    def update(self, dala_game):
        self.draw_board(dala_game)
        pygame.display.update()


class RemainPieces(object):
    piece_size = 10
    margin_size = 2
    width = (piece_size + margin_size) * DalaGame.num_of_pieces
    height = piece_size * 2 + margin_size

    def __init__(self):
        self.surface = pygame.Surface((RemainPieces.width, RemainPieces.height
                                       )).convert()

    def update(self, dala_game):
        self.surface.fill(Colors.game_background)
        pygame.draw.circle(self.surface, color, (x, y), radius)


class Title(object):
    '''Draw Game Opening'''

    font_size = 200

    def __init__(self, title='Dala'):
        font = pygame.font.Font('freesansbold.ttf', Title.font_size)
        self.title = font.render(title, True, Colors.game_title,
                                 Colors.game_background)

    def draw(self, surface, clock, fps=40):
        rect = self.title.get_rect()
        rect.center = surface.get_rect().center

        # fade in
        for i in range(0, 255, 20):
            self.title.set_alpha(i)
            surface.fill(Colors.game_background)
            surface.blit(self.title, rect)
            pygame.display.update()
            clock.tick(fps)

        clock.tick(fps / 40)

        # fade out
        for i in range(240, 20, -20):
            self.title.set_alpha(i)
            surface.fill(Colors.game_background)
            surface.blit(self.title, rect)
            pygame.display.update()
            clock.tick(fps)

        surface.fill(Colors.game_background)
        pygame.display.update()
        clock.tick(fps)


class Board(object):
    position_size = 40
    wall_size = 2
    size = DalaGame.size * (position_size + wall_size) + wall_size
    step_size = position_size + wall_size

    def __init__(self):
        self.surface = pygame.Surface((Board.size, Board.size)).convert()
        self.drop_candidate = None
        self.source_candidate = None
        self.destination_candidate = None
        self.capture_candidate = None

    def clear_candidates(self):
        self.drop_candidate = None
        self.source_candidate = None
        self.destination_candidate = None
        self.capture_candidate = None

    def draw(self, surface, position):
        surface.blit(self.surface, position)

    def update(self, dala_game):
        board = dala_game._board

        self._draw_background()
        self._draw_grid(board)
        self._draw_pieces(board)
        self._draw_candidates(dala_game)

    def update_destination_candidate(self, game, position=None):
        self.destination_candidate = None

        if position is not None:
            r, c = position
            if game.game_mode() == DalaGame.move_mode:
                if game._board[r][c] == DalaGame.empty:
                    self.destination_candidate = position

    def update_source_candidate(self, game, position=None):
        self.source_candidate = None
        self.destination_candidate = None

        if position is not None:
            r, c = position
            if game.game_mode() == DalaGame.move_mode:
                if game._board[r][c] == game.whos_turn():
                    self.source_candidate = position

    def update_drop_candidate(self, game, position=None):
        self.drop_candidate = None

        if position is not None:
            r, c = position
            if game.remains(game.whos_turn(
            )) <= DalaGame.initial_condition or game.is_central_position(
                    position):
                if game._board[r][c] == DalaGame.empty:
                    self.drop_candidate = position

    def update_capture_candidate(self, game, position=None):
        self.capture_candidate = None

        if position is not None:
            r, c = position
            if game._board[r][c] == game.next_turn():
                self.capture_candidate = position

    def get_position(self, coordinate):
        x, y = coordinate

        def in_position(i):
            return Board.wall_size <= i % Board.step_size and Board.wall_size <= i <= Board.size - Board.wall_size

        if in_position(x) and in_position(y):
            return (y // Board.step_size, x // Board.step_size)
        else:
            return None

    def _draw_a_piece(self, position, color):
        radius = Board.position_size // 3
        r, c = position
        x = Board.step_size * c + Board.wall_size + Board.position_size // 2
        y = Board.step_size * r + Board.wall_size + Board.position_size // 2
        pygame.draw.circle(self.surface, color, (x, y), radius)

    def _draw_candidates(self, dala_game):
        position = self.drop_candidate or self.destination_candidate
        if position is not None:
            r, c = position
            if dala_game._board[r][c] == DalaGame.empty:
                self._draw_a_piece(
                    position,
                    Colors.drop_candidate_colors[dala_game.whos_turn()])

        position = self.capture_candidate
        if position is not None:
            r, c = position
            if dala_game._board[r][c] == dala_game.next_turn():
                self._draw_a_piece(
                    position,
                    Colors.capture_candidate_colors[dala_game.next_turn()])

        position = self.source_candidate
        if position is not None:
            r, c = position
            if dala_game._board[r][c] == dala_game.whos_turn():
                self._draw_a_piece(
                    position,
                    Colors.source_candidate_colors[dala_game.whos_turn()])

    def _draw_pieces(self, board):
        for r in range(DalaGame.size):
            for c in range(DalaGame.size):
                if board[r][c] != DalaGame.empty:
                    self._draw_a_piece(
                        (r, c), Colors.piece_colors[board[r][c]])

    def _draw_background(self):
        self.surface.fill(Colors.board_background)

    def _draw_grid(self, board):
        color = Colors.board_wall

        pygame.draw.rect(self.surface, color, (0, 0, Board.size, Board.size),
                         Board.wall_size)

        for x in range(Board.step_size, Board.size, Board.step_size):
            pygame.draw.line(self.surface, color, (x, 0), (x, Board.size),
                             Board.wall_size)
            pygame.draw.line(self.surface, color, (0, x), (Board.size, x),
                             Board.wall_size)
