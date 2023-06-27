from ape import plugins

from .providers import FrameProvider

NETWORKS = {
    "ethereum": [
        "mainnet",
        "goerli",
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


@plugins.register(plugins.ProviderPlugin)
def providers():
    for ecosystem, networks in NETWORKS.items():
        for network in networks:
            yield ecosystem, network, FrameProvider
