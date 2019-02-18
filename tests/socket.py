# -*- coding: utf-8 -*-

from unittest.mock import patch, MagicMock

import websockets

import pytest

from aioworker.worker import Worker

from pluggable.socket.app import SocketApp
from pluggable.socket.connection import SocketConnection
from pluggable.socket.socket import Py__SocketWrapper as SocketWrapper

from .base import AsyncMock, nested


class _MockWorker(Worker):
    pass


def MockWorker():
    return _MockWorker("BROKER")


class _MockApp(SocketApp):
    config = dict(
        ip='MOCKIP',
        port=999)


def MockApp():
    return _MockApp(MockWorker(), {})


class _MockConnection(SocketConnection):

    def __init__(self, socket, *args, **kwargs):
        self.socket = socket
        self.connection = MagicMock()
        self.handle_session = AsyncMock(return_value=True)
        self.handle_connection = AsyncMock()
        self.connect = AsyncMock()


def MockConnection(socket):
    return _MockConnection(socket, 'y', 'z')


def test_socket_signature():
    with pytest.raises(TypeError):
        SocketWrapper()


@patch('pluggable.socket.socket.Py__SocketWrapper.listen')
def test_socket(listen_m):
    app = MockApp()
    socket = SocketWrapper(app)
    assert listen_m.called
    assert socket.app == app
    assert socket.connections == {}


@patch('sys.stdout.write')
@patch('pluggable.socket.socket.Py__SocketWrapper.listen')
def test_socket_log(listen_m, print_m):
    app = MockApp()
    socket = SocketWrapper(app)
    assert listen_m.called
    assert socket.app is app
    expected = []
    for args in [[''], ['foo'], ['foo', 'bar', 'baz']]:
        socket.log(args)
        expected.append(("app.socket: %s" % (' '.join(args)), ))
        expected.append(("\n", ))
    assert [list(a)[0] for a in print_m.call_args_list] == expected


def test_socket_listen(mocker):
    app = MockApp()
    app.signals = mocker.Mock()
    socket = SocketWrapper(app)
    assert len(app.signals.listen.call_args_list) == 2
    assert (
        app.signals.listen.call_args_list[0][0]
        == ('auth.session.create', socket.on_session_create))
    assert (
        app.signals.listen.call_args_list[1][0]
        == ('auth.session.destroy', socket.on_session_destroy))


@pytest.mark.asyncio
async def test_socket_on_session_create():
    app = MockApp()
    with patch('pluggable.socket.socket.Py__SocketWrapper.listen'):
        socket = SocketWrapper(app)
    socket.connections = {"CONNECTION": {}}
    await socket.on_session_create(
        'on.session.create',
        session="SESSION",
        connection="CONNECTION")
    assert (
        socket.connections
        == {'CONNECTION': {'session': "SESSION"}})


@pytest.mark.asyncio
async def test_socket_on_session_destroy():
    app = MockApp()
    with patch('pluggable.socket.socket.Py__SocketWrapper.listen'):
        socket = SocketWrapper(app)
    socket.connections = {
        "CONNECTION1": {"session": 7},
        "CONNECTION2": {"session": 23}}
    await socket.on_session_destroy(
        'auth.session.destroy',
        connection="CONNECTION1")
    assert (
        socket.connections
        == {'CONNECTION1': {},
            "CONNECTION2": {"session": 23}})


@patch('pluggable.socket.socket.Py__SocketWrapper.listen')
@patch('pluggable.socket.socket.Py__SocketWrapper._log')
@patch('pluggable.socket.socket.websockets.serve')
def test_socket_serve(ws_m, log_m, listen_m):
    app = MockApp()
    socket = SocketWrapper(app)
    socket.serve()
    assert (
        [c[0] for c in log_m.call_args_list]
        == [(socket.service, 'listening')])
    assert (
        [c[0] for c in ws_m.call_args_list]
        == [(socket.pipe, socket.app.config["ip"], socket.app.config["port"])])


@patch('pluggable.socket.socket.Py__SocketWrapper.listen')
@patch('pluggable.socket.socket.Py__SocketWrapper._log')
def test_socket_connect(log_m, listen_m):
    app = MockApp()
    socket = SocketWrapper(app)
    connection = socket.connect('WS', 'PATH')
    assert (
        [c[0] for c in log_m.call_args_list]
        == [(connection, 'connect')])
    assert (
        socket.connections
        == {hash(connection):
            {'connection': connection,
             'socket': connection.connection}})


@patch('pluggable.socket.socket.Py__SocketWrapper.listen')
@patch('pluggable.socket.socket.Py__SocketWrapper._log')
def test_socket_disconnect(log_m, listen_m):
    app = MockApp()
    socket = SocketWrapper(app)
    connection1 = SocketConnection(socket, 'SOCKETX', 'PATH')
    connection2 = SocketConnection(socket, 'SOCKETY', 'PATH')
    socket.connections[hash(connection1)] = 7
    socket.connections[hash(connection2)] = 23
    socket.disconnect(connection1)
    assert (
        socket.connections
        == {hash(connection2): 23})
    assert (
        [c[0] for c in log_m.call_args_list]
        == [(connection1, 'disconnect')])


@pytest.mark.asyncio
async def test_socket_pipe(mocker):
    app = MockApp()
    with patch('pluggable.socket.socket.Py__SocketWrapper.listen'):
        socket = SocketWrapper(app)
    _patches = nested(
        patch('pluggable.socket.socket.Py__SocketWrapper.disconnect'),
        patch('pluggable.socket.socket.Py__SocketWrapper.connect'))
    with _patches as (disconnect_m, connect_m):
        connection = MockConnection(socket)
        connect_m.return_value = connection
        await socket.pipe('WS', 'PATH')
        assert (
            [c[0] for c in connection.connect.call_args_list]
            == [()])
        assert (
            [c[0] for c in connect_m.call_args_list]
            == [('WS', 'PATH')])

        class FailingSocketConnection(SocketConnection):
            async def connect(self, *args, **kwargs):
                raise websockets.exceptions.ConnectionClosed(404, 'had enough')
        connect_m.return_value = FailingSocketConnection(
            socket, 'SOCKETX', 'PATH')
        await socket.pipe('WS', 'PATH')
        assert (
            [c[0] for c in connect_m.call_args_list]
            == [('WS', 'PATH'), ('WS', 'PATH')])
        assert (
            [c[0] for c in disconnect_m.call_args_list]
            == [(connect_m.return_value, )])
