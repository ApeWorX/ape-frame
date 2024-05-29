from ape_frame.accounts import AccountContainer, FrameAccount


class TestAccountContainer:
    def test_account_container(self):
        # TODO: Actually setup accounts first.
        container = AccountContainer(account_type=FrameAccount)
        for acct in container.accounts:
            assert type(acct) is FrameAccount
