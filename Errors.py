class AppError(Exception): pass


class AlreadyUsedNickname(Exception): pass


class AlreadyEnrolledAccount(Exception): pass


class TransferNotFinished(Exception): pass


class TransferFailAtTheEnd(Exception): pass


class GettingTokenError(Exception): pass


class ContinueForTokenError(Exception): pass


class TimeoutButAccountHasBeenSubscribe(Exception): pass


class WrongDataOrAccountAlreadySubscribe(Exception): pass


class OrderAsPaidError(Exception): pass


class NequiAccountError(Exception): pass


class BancolombiaError(Exception): pass


class ApiConnectionError(Exception): pass
