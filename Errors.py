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


class ApiConnectionError(Exception): pass


class WrongAccountData(Exception): pass


class BankColombiaIsDown(Exception): pass


class AccountCantHandleTheMoney(Exception): pass


class ConnectionError(Exception): pass
