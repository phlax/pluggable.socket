# -*- coding: utf-8 -*-

import json
from unittest.mock import patch, MagicMock

import websockets

import pytest

from aioworker.worker import Worker

from pluggable.socket.app import SocketApp
from pluggable.socket.connection import (
    Py__SocketConnection as SocketConnection)
from pluggable.socket.socket import SocketWrapper

from .base import AsyncMock, nested


class _MockWorker(Worker):
    pass


def MockWorker():
    return _MockWorker("BROKER")


class _MockApp(SocketApp):
    worker = 7
    config = dict(
        ip='MOCKIP',
        port=999)

    def __init__(self, *args, **kwargs):
        self.runner = MagicMock()
        self.loop = MagicMock()


def MockApp():
    return _MockApp(MockWorker(), {})


class _MockSocketWrapper(SocketWrapper):

    def __init__(self, app):
        self.send = AsyncMock()


def MockSocketWrapper():
    return _MockSocketWrapper(MockApp())


def test_connection_signature():
    with pytest.raises(TypeError):
        SocketConnection()


def test_connection():
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, "CONNECTION", "PATH")
    assert connection.socket is socket
    assert connection.path == "PATH"
    assert connection.connection == "CONNECTION"
    assert hash(connection) == hash(connection.connection)


def test_connection_app(mocker):
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, "CONNECTION", "PATH")
    assert connection.app is socket.app


def test_connection_ip(mocker):
    socket = MockSocketWrapper()
    _connection = mocker.MagicMock()
    connection = SocketConnection(socket, _connection, "PATH")
    assert (
        connection.ip
        == _connection.remote_address.__getitem__.return_value)
    assert (
        [c[0] for c in _connection.remote_address.__getitem__.call_args_list]
        == [(0,)])


def test_connection_port(mocker):
    socket = MockSocketWrapper()
    _connection = mocker.MagicMock()
    connection = SocketConnection(socket, _connection, "PATH")
    assert (
        connection.port
        == _connection.remote_address.__getitem__.return_value)
    assert (
        [c[0] for c in _connection.remote_address.__getitem__.call_args_list]
        == [(1,)])


@patch("pluggable.socket.connection.json")
def test_connection_parse_request(json_m):
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, "CONNECTION", "PATH")
    json_m.loads.return_value = {"FOO": 23}
    response = connection.parse_request("MESSAGE")
    assert response == json_m.loads.return_value
    assert (
        [c[0] for c in json_m.loads.call_args_list]
        == [('MESSAGE', )])


def test_connection_handle_request(mocker):
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, "CONNECTION", "PATH")
    connection.handle_request("SESSION", {"msg": "MESSAGE"})
    assert (
        [c[0] for c in connection.app.loop.create_task.call_args_list]
        == [(connection.app.runner.run.return_value, )])

    assert (
        [c[0] for c in connection.app.runner.run.call_args_list]
        == [(connection, )])
    assert (
        [c[1] for c in connection.app.runner.run.call_args_list]
        == [{'msg': 'MESSAGE'}])


called = 0


@pytest.mark.asyncio
async def test_connection_connect(mocker):
    _connection_m = AsyncMock()
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, _connection_m, "PATH")

    def _recv():
        global called
        if called > 2:
            raise websockets.exceptions.ConnectionClosed(
                999, "Got bored")
        called += 1
        return json.dumps({"msg": 23})

    _connection_m.recv.side_effect = _recv

    _patches = nested(
        patch(
            "pluggable.socket.connection."
            "Py__SocketConnection.handle_connection",
            new_callable=AsyncMock),
        patch(
            "pluggable.socket.connection."
            "Py__SocketConnection.parse_request"),
        patch(
            "pluggable.socket.connection."
            "Py__SocketConnection.log_request"),
        patch(
            "pluggable.socket.connection."
            "Py__SocketConnection.handle_session",
            new_callable=AsyncMock),
        patch(
            "pluggable.socket.connection."
            "Py__SocketConnection.handle_request"))
    with _patches as (connect_m, parse_m, log_m, session_m, request_m):
        parse_m.return_value = {"MSG": 723}
        try:
            await connection.connect()
        except websockets.exceptions.ConnectionClosed:
            pass
        assert (
            [c[0] for c in connect_m.call_args_list]
            == [()])
        assert (
            [c[0] for c in parse_m.call_args_list]
            == [('{"msg": 23}', ), ('{"msg": 23}', ), ('{"msg": 23}', )])
        assert (
            [c[0] for c in log_m.call_args_list]
            == [(parse_m.return_value, ),
                (parse_m.return_value, ),
                (parse_m.return_value, )])
        assert (
            [c[0] for c in session_m.call_args_list]
            == [(), (), ()])
        assert (
            [c[0] for c in request_m.call_args_list]
            == [(session_m.return_value, {'MSG': 723}),
                (session_m.return_value, {'MSG': 723}),
                (session_m.return_value, {'MSG': 723})])


@pytest.mark.asyncio
async def test_connection_handle_connection(mocker):
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, "CONNECTION", "PATH")

    _patches = nested(
        patch(
            "pluggable.socket.connection."
            "Py__SocketConnection.validate_connection",
            new_callable=AsyncMock),
        patch(
            "pluggable.socket.connection."
            "Py__SocketConnection.handle_session",
            new_callable=AsyncMock))

    with _patches as (connection_m, session_m):
        session_m.return_value = None
        await connection.handle_connection()
        assert (
            session_m.call_args_list
            == [()])
        assert (
            connection_m.call_args_list
            == [()])
        assert (
            connection.socket.send.call_args_list
            == [])

        session_m.return_value = "BINGO"

        await connection.handle_connection()
        assert (
            session_m.call_args_list
            == [(), ()])

        assert (
            connection_m.call_args_list
            == [(), ()])
        assert (
            [c[0] for c in connection.socket.send.call_args_list]
            == [({'user': 'BINGO', 'msg': 'connected'},
                 [hash(connection)])])


@pytest.mark.asyncio
async def test_connection_log_request(mocker, capsys):
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, mocker.MagicMock(), "PATH")
    connection.log_request({"foo": 113, "bar": 117})
    assert (
        capsys.readouterr().out.strip()
        == " ".join([
            'app.socket.recv',
            str(connection.connection.remote_address['ip']),
            str(connection.connection.remote_address['port']),
            str({"foo": 113, "bar": 117})]))


@pytest.mark.asyncio
async def test_socket_handle_session(mocker):
    socket = MockSocketWrapper()
    connection = SocketConnection(socket, "CONNECTION", "PATH")
    _patch = patch(
        "pluggable.socket.connection.Py__SocketConnection._get_session",
        new_callable=AsyncMock)
    with _patch as session_m:
        _session = [AsyncMock(), mocker.MagicMock()]
        session_m.return_value = _session
        result = await connection.handle_session()
        assert (
            [c[0] for c in _session[0].load.call_args_list]
            == [(_session[1], )])
        assert result == _session[1]
    _patch = patch(
        "pluggable.socket.connection.Py__SocketConnection._get_session",
        new_callable=AsyncMock)
    with _patch as session_m:
        _session = [AsyncMock(), None]
        session_m.return_value = _session
        result = await connection.handle_session()
        assert not _session[0].load.called
        assert result is None
