from ape.utils import create_tempdir

from ape_frame.accounts import AccountContainer, FrameAccount


class TestAccountContainer:
    def test_account_container(self):
        with create_tempdir() as data_path:
            container = AccountContainer(data_folder=data_path, account_type=FrameAccount)
            for acct in container.accounts:
                assert type(acct) is FrameAccount
