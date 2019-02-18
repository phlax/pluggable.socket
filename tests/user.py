# -*- coding: utf-8 -*-

import pytest

from pluggable.socket.user import SocketUser


def test_user_signature():
    with pytest.raises(TypeError):
        SocketUser()


def test_user():
    user = SocketUser(23)
    assert user.connection == 23
