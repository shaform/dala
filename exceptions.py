class DalaException(Exception):
    pass


class IllegalMoveException(DalaException):
    pass


class NotYourTurnException(IllegalMoveException):
    pass


class IllegalMovementException(IllegalMoveException):
    pass


class IllegalPositionException(IllegalMoveException):
    pass


class CentralNotOccupiedException(IllegalMoveException):
    pass


class AlreadyOccupiedException(IllegalMoveException):
    pass


class CaptureException(IllegalMoveException):
    pass


class MustNotCaptureException(CaptureException):
    pass


class MustCaptureException(CaptureException):
    pass


class IllegalCapturePositionException(CaptureException):
    pass


class GameOverException(DalaException):
    pass
