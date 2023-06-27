from ape.exceptions import ProviderError, ProviderNotConnectedError


class FrameNotConnectedError(ProviderNotConnectedError):
    pass


class FrameProviderError(ProviderError):
    """
    An error raised by the Frame provider plugin.
    """
