from typing import Iterator, Optional

from ape.api.accounts import AccountAPI, AccountContainerAPI, TransactionAPI
from ape.types import AddressType, MessageSignature, SignableMessage, TransactionSignature
from eth_account._utils.legacy_transactions import serializable_unsigned_transaction_from_dict
from eth_account.messages import _hash_eip191_message
from eth_utils.curried import keccak
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
        return Web3(HTTPProvider("http://127.0.0.1:1248"))

    @property
    def alias(self) -> str:
        return "frame"

    @property
    def address(self) -> AddressType:
        return self.web3.eth.accounts[0]

    def sign_message(self, msg: SignableMessage) -> Optional[MessageSignature]:
        try:
            raw_signature = self.web3.eth.sign(self.address, hexstr=_hash_eip191_message(msg).hex())
        except ValueError as e:
            if not e.args[0]["message"] == "User declined transaction":
                raise

            return None

        return MessageSignature(  # type: ignore[call-arg]
            v=raw_signature[64],  # type: ignore[arg-type]
            r=raw_signature[0:32],  # type: ignore[arg-type]
            s=raw_signature[32:64],  # type: ignore[arg-type]
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
