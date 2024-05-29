from collections.abc import Callable, Iterator
from typing import Any, Optional, Union

from ape.api.accounts import AccountAPI, AccountContainerAPI, TransactionAPI
from ape.exceptions import AccountsError
from ape.types import AddressType, MessageSignature, SignableMessage, TransactionSignature
from eip712.messages import EIP712Message
from eth_account import Account
from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
from eth_account.messages import encode_defunct
from eth_utils.curried import keccak
from hexbytes import HexBytes
from web3 import HTTPProvider, Web3


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

    except ValueError as err:
        if not err.args[0]["message"] == "User declined transaction":
            raise  # The ValueError

        return None


class FrameAccount(AccountAPI):
    @property
    def web3(self) -> Web3:
        headers = {
            "Origin": "Ape/ape-frame/account",
            "User-Agent": "ape-frame/0.1.0",
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
            raw_signature = wrap_sign(
                lambda: self.web3.eth.sign_typed_data(self.address, msg._body_)
            )

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
        # TODO: need a way to deserialized from raw bytes
        txn_data = txn.model_dump(by_alias=True, mode="json", exclude={"sender"})
        unsigned_txn = serializable_unsigned_transaction_from_dict(txn_data)
        raw_signature = wrap_sign(
            lambda: self.web3.eth.sign(self.address, hexstr=keccak(unsigned_txn).hex())
        )
        txn.signature = (
            TransactionSignature(
                v=int(raw_signature[64]),
                r=HexBytes(raw_signature[0:32]),
                s=HexBytes(raw_signature[32:64]),
            )
            if raw_signature
            else None
        )
        return txn

    def check_signature(
        self,
        data: Union[SignableMessage, TransactionAPI, str, EIP712Message, int, bytes],
        signature: Optional[MessageSignature] = None,  # TransactionAPI doesn't need it
        recover_using_eip191: bool = True,
    ) -> bool:
        if isinstance(data, str):
            data = encode_defunct(text=data)
        elif isinstance(data, bytes) and (len(data) != 32 or recover_using_eip191):
            data = encode_defunct(data)
        elif isinstance(data, EIP712Message):
            data = data.signable_message
        elif isinstance(data, bytes) and len(data) == 32 and not recover_using_eip191:
            return self.address == Account._recover_hash(data, vrs=signature)
        else:
            raise AccountsError(f"Unsupported message type: {type(data)}.")

        return super().check_signature(data, signature)
