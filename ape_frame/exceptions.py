from ape.exceptions import AccountsError, ProviderError, ProviderNotConnectedError


class FrameNotConnectedError(ProviderNotConnectedError):
    pass


class FrameProviderError(ProviderError):
    """
    An error raised by the Frame provider plugin.
    """


class FrameAccountException(AccountsError):
    """
    An error that occurs in the ape Frame plugin.
    """


class FrameSigningError(FrameAccountException):
    """
    An error that occurs when signing a message or transaction
    using the Frame plugin.
    """
