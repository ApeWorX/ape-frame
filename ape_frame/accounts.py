from collections.abc import Callable, Iterator
from importlib.metadata import version
from typing import Any, Optional, cast

from ape.api import AccountAPI, AccountContainerAPI, ReceiptAPI, TransactionAPI
from ape.exceptions import ProviderError, SignatureError
from ape.types import AddressType, MessageSignature, SignableMessage
from eip712.messages import EIP712Message, extract_eip712_struct_message
from hexbytes import HexBytes
from web3 import HTTPProvider, Web3
from web3.exceptions import Web3RPCError


class AccountContainer(AccountContainerAPI):
    """
    The account container for Fsrame accounts in Ape.
    """

    name: str = "frame"

    @property
    def aliases(self) -> Iterator[str]:
        yield "frame"

    def __len__(self) -> int:
        return 1

    @property
    def accounts(self) -> Iterator[AccountAPI]:
        yield FrameAccount()


def wrap_sign(fn: Callable) -> Optional[bytes]:
    try:
        return fn()

    except Web3RPCError as err:
        if (
            not (rpc_error := cast(dict, err.rpc_response).get("error", {}))
            or not rpc_error.get("message", "") == "User declined transaction"
        ):
            raise  # The ValueError

        return None


class FrameAccount(AccountAPI):
    @property
    def web3(self) -> Web3:
        ape_version = version("eth-ape")
        plugin_version = version("ape-frame")
        headers = {
            "Origin": "Ape",
            "User-Agent": f"Ape-Frame/{plugin_version};Ape/{ape_version}",
            "Content-Type": "application/json",
        }
        return Web3(HTTPProvider("http://127.0.0.1:1248", request_kwargs={"headers": headers}))

    @property
    def alias(self) -> str:
        return "frame"

    @property
    def address(self) -> AddressType:
        return self.web3.eth.accounts[0]

    def sign_message(self, msg: Any, **signer_options) -> Optional[MessageSignature]:
        raw_signature = None

        if isinstance(msg, str):
            raw_signature = wrap_sign(lambda: self.web3.eth.sign(self.address, text=msg))
        elif isinstance(msg, int):
            raw_signature = wrap_sign(
                lambda: self.web3.eth.sign(self.address, hexstr=HexBytes(msg).hex())
            )
        elif isinstance(msg, bytes):
            raw_signature = wrap_sign(lambda: self.web3.eth.sign(self.address, hexstr=msg.hex()))
        elif isinstance(msg, SignableMessage):
            raw_signature = wrap_sign(lambda: self.web3.eth.sign(self.address, data=msg.body))
        elif isinstance(msg, EIP712Message):
            data = extract_eip712_struct_message(msg)
            raw_signature = wrap_sign(lambda: self.web3.eth.sign_typed_data(self.address, data))

        return (
            MessageSignature(
                v=int(raw_signature[64]),
                r=HexBytes(raw_signature[0:32]),
                s=HexBytes(raw_signature[32:64]),
            )
            if raw_signature
            else None
        )

    def sign_transaction(self, txn: TransactionAPI, **signer_options) -> Optional[TransactionAPI]:
        return None

    def call(self, txn: TransactionAPI, private: bool = False, **kwargs) -> ReceiptAPI:
        # NOTE: Need to override the default implementation since Frame does not support sign txn
        if private:
            raise ProviderError("Private Mempool not supported by Frame")

        txn_data = txn.model_dump(by_alias=True, mode="json", exclude={"sender"})
        if txn_hash := wrap_sign(lambda: self.web3.eth.send_transaction(txn_data)):
            return self.chain_manager.get_receipt(txn_hash)

        raise SignatureError("The transaction was not signed.", transaction=txn)
