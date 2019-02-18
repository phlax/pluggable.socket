# -*- coding: utf-8 -*-

from pluggable.socket.request import Py__SocketRequest as SocketRequest


def test_request():
    request = SocketRequest()
    assert request.session is None
    assert request.params == {}
    assert request.args == []


def test_request_session():
    request = SocketRequest(session="SESSION")
    assert request.session == "SESSION"
    assert request.params == {}
    assert request.args == []


def test_request_params():
    request = SocketRequest(params=dict(foo=7, bar=23))
    assert request.session is None
    assert request.params == dict(foo=7, bar=23)
    assert request.args == []
