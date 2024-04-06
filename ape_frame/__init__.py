from ape import plugins

from .accounts import AccountContainer, FrameAccount
from .providers import FrameProvider

NETWORKS = {
    "ethereum": [
        "mainnet",
        "sepolia",
    ],
    "arbitrum": [
        "mainnet",
    ],
    "optimism": [
        "mainnet",
    ],
    "polygon": [
        "mainnet",
    ],
}


@plugins.register(plugins.AccountPlugin)
def account_types():
    return AccountContainer, FrameAccount


@plugins.register(plugins.ProviderPlugin)
def providers():
    for ecosystem, networks in NETWORKS.items():
        for network in networks:
            yield ecosystem, network, FrameProvider
