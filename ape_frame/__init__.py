from ape import plugins


NETWORKS = {
    "ethereum": [
        "mainnet",
        "sepolia",
    ],
    "arbitrum": [
        "mainnet",
        "sepolia",
    ],
    "base": [
        "mainnet",
        "sepolia",
    ],
    "optimism": [
        "mainnet",
        "sepolia",
    ],
    "polygon": [
        "mainnet",
        "amoy",
    ],
}


@plugins.register(plugins.AccountPlugin)
def account_types():
    from .accounts import AccountContainer, FrameAccount

    return AccountContainer, FrameAccount


@plugins.register(plugins.ProviderPlugin)
def providers():
    from .providers import FrameProvider

    for ecosystem, networks in NETWORKS.items():
        for network in networks:
            yield ecosystem, network, FrameProvider
