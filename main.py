import argparse
import time

import pygame

from display import Display
from exceptions import *
from game import DalaGame


class MouseButtons(object):
    left = 1
    middle = 2
    right = 3


class QuitException(Exception):
    pass


class RestartException(Exception):
    pass


class Dala(object):
    def __init__(self, debug=False, headless=False):
        self.debug = debug
        self.game = DalaGame()
        self.headless = headless
        self.updated = True
        pygame.init()

        self.clock = pygame.time.Clock()
        if not self.headless:
            self._init_display()

    def _init_display(self):
        self.display = Display(title='Dala', clock=self.clock)

    def _update_display(self):
        if self.updated or True:
            self.display.update(self.game)
            self.updated = False

    def reset(self):
        pass

    def main(self):
        self.display.display_opening()

        while True:
            event = pygame.event.wait()

            self._process_restart(event)
            self._process_quit(event)

            if self._is_mouse_up(event):
                pos = pygame.mouse.get_pos()
                position = self.display.get_board_position(pos)

                if position is not None:
                    if self.game.game_mode() == DalaGame.drop_mode:
                        if not self._drop_loop(position):
                            self.display.board.clear_candidates()

                    elif self.game.game_mode() == DalaGame.move_mode:
                        if not self._move_loop(position):
                            self.display.board.clear_candidates()

            elif event.type == pygame.MOUSEMOTION:
                position = self.display.get_board_position(
                    pygame.mouse.get_pos())
                if self.game.game_mode() == DalaGame.drop_mode:
                    self.display.board.update_drop_candidate(self.game,
                                                             position)
                elif self.game.game_mode() == DalaGame.move_mode:
                    self.display.board.update_source_candidate(self.game,
                                                               position)

            self._update_display()

    def _is_mouse_up(self, event, button=MouseButtons.left):
        return event.type == pygame.MOUSEBUTTONUP and event.button == button

    def _move_loop(self, source):
        r, c = source

        if self.game._board[r][c] == self.game.whos_turn():
            self.display.board.update_source_candidate(self.game, source)

            while True:
                event = pygame.event.wait()

                self._process_restart(event)
                self._process_quit(event)

                if event.type == pygame.MOUSEMOTION:
                    pos = pygame.mouse.get_pos()
                    dest = self.display.get_board_position(pos)
                    self.display.board.update_destination_candidate(self.game,
                                                                    dest)

                elif self._is_mouse_up(event, MouseButtons.right):
                    return False

                elif self._is_mouse_up(event):
                    pos = pygame.mouse.get_pos()
                    dest = self.display.get_board_position(pos)

                    try:
                        if dest is not None:
                            self.game.move(self.game.whos_turn(), source, dest)
                            return True

                    except MustCaptureException:
                        self.display.board.update_destination_candidate(
                            self.game, dest)

                        def action(dala_game, capture):
                            dala_game.move(dala_game.whos_turn(), source, dest,
                                           capture)

                        if self._capture_loop(action):
                            return True

                        else:
                            self.display.board.update_destination_candidate(
                                self.game, None)

                    except IllegalMoveException as e:
                        print(e)

                self._update_display()

        else:
            return False

    def _drop_loop(self, position):
        try:
            self.game.drop(self.game.whos_turn(), position)

        except MustCaptureException:
            self.display.board.update_drop_candidate(self.game, position)

            def action(dala_game, capture):
                dala_game.drop(dala_game.whos_turn(), position, capture)

            return self._capture_loop(action)

        except IllegalMoveException as e:
            print(e)

    def _capture_loop(self, action):
        while True:
            event = pygame.event.wait()

            self._process_restart(event)
            self._process_quit(event)

            if event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                capture = self.display.get_board_position(pos)
                self.display.board.update_capture_candidate(self.game, capture)

            elif self._is_mouse_up(event, MouseButtons.right):
                return False

            elif self._is_mouse_up(event):
                pos = pygame.mouse.get_pos()
                capture = self.display.get_board_position(pos)

                if capture is not None:
                    try:
                        action(self.game, capture)
                        self.display.board.clear_candidates()
                        return True

                    except IllegalMoveException as e:
                        print(e)

            self._update_display()

    def _process_quit(self, event):
        if self._is_quit_event(event):
            raise QuitException()

    def _process_restart(self, event):
        if event.type == pygame.KEYUP and event.key == pygame.K_F5:
            raise RestartException()

    def _is_quit_event(self, event):
        return event.type == pygame.QUIT or event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE


if __name__ == '__main__':
    while True:
        dala = Dala()
        try:
            dala.main()
            break

        except QuitException:
            break

        except RestartException:
            pass

        except GameOverException as e:
            print(e)
