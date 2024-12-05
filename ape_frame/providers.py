from collections.abc import Iterable
from typing import Any, Optional

from ape.api import UpstreamProvider
from ape.exceptions import ProviderError
from ape_ethereum.provider import Web3Provider
from eth_utils import to_hex
from requests import HTTPError
from web3 import HTTPProvider, Web3
from web3.gas_strategies.rpc import rpc_gas_price_strategy

try:
    from web3.middleware import ExtraDataToPOAMiddleware  # type: ignore
except ImportError:
    from web3.middleware import geth_poa_middleware as ExtraDataToPOAMiddleware  # type: ignore

from ape_frame.exceptions import FrameNotConnectedError, FrameProviderError


class FrameProvider(Web3Provider, UpstreamProvider):
    _original_chain_id: int = -1

    @property
    def uri(self) -> str:
        # TODO: Add config for this
        return "http://127.0.0.1:1248"

    @property
    def connection_str(self) -> str:
        return self.uri

    def connect(self):
        headers = {
            "Origin": "Ape/ape-frame/provider",
            "User-Agent": "ape-frame/0.1.0",
            "Content-Type": "application/json",
        }
        self._web3 = Web3(HTTPProvider(self.uri, request_kwargs={"headers": headers}))

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
        ethereum_sepolia = 11155111
        optimism = (10, 11155420)
        polygon = (137, 80002)
        try:
            if self._web3.eth.chain_id in (ethereum_sepolia, *optimism, *polygon):
                self._web3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)

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

    def make_request(self, rpc: str, parameters: Optional[Iterable] = None) -> Any:
        parameters = parameters or []
        try:
            return super().make_request(rpc, parameters=parameters)
        except HTTPError as err:
            response_data = err.response.json() if err.response else {}
            if "error" not in response_data:
                raise FrameProviderError(str(err)) from err

            error_data = response_data["error"]
            message = (
                error_data.get("message", str(error_data))
                if isinstance(error_data, dict)
                else error_data
            )
            raise FrameProviderError(message) from err
