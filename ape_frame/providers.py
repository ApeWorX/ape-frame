from typing import Any

from ape.api import UpstreamProvider, Web3Provider
from ape.exceptions import ProviderError
from eth_utils import to_hex
from requests import HTTPError  # type: ignore[import]
from web3 import HTTPProvider, Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.middleware import geth_poa_middleware

from .exceptions import FrameNotConnectedError, FrameProviderError


class FrameProvider(Web3Provider, UpstreamProvider):
    _original_chain_id: int = -1

    @property
    def uri(self) -> str:
        # TODO: Add config for this
        return "http://127.0.01:1248"

    @property
    def connection_str(self) -> str:
        return self.uri

    def connect(self):
        self._web3 = Web3(HTTPProvider(self.uri))

        if "Frame" not in self._web3.client_version:
            raise FrameNotConnectedError()

        self._original_chain_id = self._web3.eth.chain_id

        # NOTE: Make sure Frame is on the right network
        if self.network.chain_id != self._original_chain_id:
            self._make_request(
                "wallet_switchEthereumChain",
                [{"chainId": to_hex(self.network.chain_id)}],
            )

        # Any chain that *began* as PoA needs the middleware for pre-merge blocks
        ethereum_goerli = 5
        optimism = (10, 420)
        polygon = (137, 80001)
        try:

            if self._web3.eth.chain_id in (ethereum_goerli, *optimism, *polygon):
                self._web3.middleware_onion.inject(geth_poa_middleware, layer=0)

            self._web3.eth.set_gas_price_strategy(rpc_gas_price_strategy)
        except Exception as err:
            raise ProviderError(f"Failed to connect to Frame.\n{repr(err)}") from err

    def disconnect(self):
        # NOTE: Make sure Frame is on the original network
        self._make_request(
            "wallet_switchEthereumChain",
            [{"chainId": to_hex(self._original_chain_id)}],
        )

        self._web3 = None

    def _make_request(self, endpoint: str, parameters: list) -> Any:
        try:
            return super()._make_request(endpoint, parameters)
        except HTTPError as err:
            response_data = err.response.json()
            if "error" not in response_data:
                raise FrameProviderError(str(err)) from err

            error_data = response_data["error"]
            message = (
                error_data.get("message", str(error_data))
                if isinstance(error_data, dict)
                else error_data
            )
            raise FrameProviderError(message) from err
