from typing import Any, Iterator, Optional, Union

from ape.api.accounts import AccountAPI, AccountContainerAPI, TransactionAPI
from ape.types import AddressType, MessageSignature, SignableMessage, TransactionSignature
from eip712.messages import EIP712Message
from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
from eth_account.messages import encode_defunct
from eth_utils.curried import keccak
from hexbytes import HexBytes
from web3 import HTTPProvider, Web3


class AccountContainer(AccountContainerAPI):
    @property
    def aliases(self) -> Iterator[str]:
        yield "frame"

    def __len__(self) -> int:
        return 1

    @property
    def accounts(self) -> Iterator[AccountAPI]:
        yield FrameAccount()


class FrameAccount(AccountAPI):
    @property
    def web3(self) -> Web3:
        headers = {
            "Origin": "Ape",
            "User-Agent": "ape-frame/0.1.0",
            "Content-Type": "application/json"
        }
        return Web3(HTTPProvider("http://127.0.0.1:1248", request_kwargs={"headers": headers}))

    @property
    def alias(self) -> str:
        return "frame"

    @property
    def address(self) -> AddressType:
        return self.web3.eth.accounts[0]

    def sign_message(self, msg: Any) -> Optional[MessageSignature]:
        raw_signature = None

        if isinstance(msg, str):
            # encode string messages as Ethereum Signed Messages
            try:
                raw_signature = self.web3.eth.sign(self.address, text=msg)
            except ValueError as e:
                if not e.args[0]["message"] == "User declined transaction":
                    raise
                return None
        if isinstance(msg, int):
            try:
                raw_signature = self.web3.eth.sign(self.address, hexstr=HexBytes(msg).hex())
            except ValueError as e:
                if not e.args[0]["message"] == "User declined transaction":
                    raise
                return None
        if isinstance(msg, bytes):
            try:
                raw_signature = self.web3.eth.sign(self.address, hexstr=msg.hex())
            except ValueError as e:
                if not e.args[0]["message"] == "User declined transaction":
                    raise
                return None

        if isinstance(msg, SignableMessage):
            try:
                raw_signature = self.web3.eth.sign(self.address, data=msg.body)
            except ValueError as e:
                if not e.args[0]["message"] == "User declined transaction":
                    raise
                return None

        if isinstance(msg, EIP712Message):
            try:
                raw_signature = self.web3.eth.sign_typed_data(self.address, msg._body_)
            except ValueError as e:
                if not e.args[0]["message"] == "User declined transaction":
                    raise
                return None

        return (
            MessageSignature(  # type: ignore[call-arg]
                v=raw_signature[64],
                r=raw_signature[0:32],
                s=raw_signature[32:64],
            )
            if raw_signature
            else None
        )

    def sign_transaction(self, txn: TransactionAPI, **signer_options) -> Optional[TransactionAPI]:
        # TODO: need a way to deserialized from raw bytes
        # raw_signed_txn_bytes = self.web3.eth.sign_transaction(txn.dict())
        txn_data = txn.dict(exclude={"sender"})
        unsigned_txn = serializable_unsigned_transaction_from_dict(txn_data)
        try:
            raw_signature = self.web3.eth.sign(self.address, hexstr=keccak(unsigned_txn).hex())
        except ValueError as e:
            if not e.args[0]["message"] == "User declined transaction":
                raise

            return None

        txn.signature = TransactionSignature(  # type: ignore[call-arg]
            v=raw_signature[64],  # type: ignore[arg-type]
            r=raw_signature[0:32],  # type: ignore[arg-type]
            s=raw_signature[32:64],  # type: ignore[arg-type]
        )
        return txn

    def check_signature(
        self,
        data: Union[SignableMessage, TransactionAPI, EIP712Message, str],
        signature: Optional[MessageSignature] = None,
    ) -> bool:
        if isinstance(data, str):
            data = encode_defunct(text=data)
        elif isinstance(data, bytes):
            data = encode_defunct(primitive=data)
        if isinstance(data, EIP712Message):
            data = data.signable_message
        return super().check_signature(data, signature)
