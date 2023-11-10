import tempfile
from pathlib import Path

from ape_frame.accounts import AccountContainer, FrameAccount


class TestAccountContainer:
    def test_account_container(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            data_path = Path(temp_dir)
            container = AccountContainer(data_folder=data_path, account_type=FrameAccount)
            for acct in container.accounts:
                assert type(acct) is FrameAccount
