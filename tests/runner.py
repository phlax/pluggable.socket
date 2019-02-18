# -*- coding: utf-8 -*-

from unittest.mock import patch, MagicMock

import pytest

from aioworker.worker import Worker

from pluggable.socket.app import SocketApp
from pluggable.core.exceptions import UnrecognizedCommand
from pluggable.socket.connection import SocketConnection
from pluggable.socket.runner import (
    Py__SocketRunner as SocketRunner)
from pluggable.socket.socket import SocketWrapper

from .base import AsyncMock


class _MockWorker(Worker):
    pass


def MockWorker():
    return _MockWorker("BROKER")


class MockApp(object):
    worker = 7


class _MockApp(SocketApp):
    pass


class MockSocketWrapper(SocketWrapper):

    def __init__(self, app):
        self.app = app


class _MockConnection(SocketConnection):

    def __init__(self, socket, *args, **kwargs):
        self.socket = socket
        self.connection = MagicMock()
        self.handle_session = AsyncMock(return_value=True)
        self.handle_connection = AsyncMock()
        self.connect = AsyncMock()


def MockConnection(runner):
    app = _MockApp(MockWorker(), {})
    app.runner = runner
    app.socket = MockSocketWrapper(app)
    return _MockConnection(app.socket, 'y', 'z')


def test_runner_signature():
    with pytest.raises(TypeError):
        SocketRunner()


def test_runner():
    app = MockApp()
    runner = SocketRunner(app)
    assert runner.app is app


@pytest.mark.asyncio
async def test_runner_run(mocker):
    app = mocker.MagicMock()
    runner = SocketRunner(app)
    app.worker.tasks = {"FOO": 7, "BAR": 13}
    app.local.commands = {"LOCAL_FOO": 7, "LOCAL_BAR": 13}
    connection = MockConnection(runner)

    with pytest.raises(TypeError):
        await runner.run('CONNECTION')
    with pytest.raises(UnrecognizedCommand):
        await runner.run(connection, uuid="UUID")
    with pytest.raises(UnrecognizedCommand):
        await runner.run(connection, uuid="UUID", command="BAZ")
    _patch = patch(
        "pluggable.socket.runner.Py__SocketRunner.run_worker",
        new_callable=AsyncMock)
    with _patch as worker_m:
        await runner.run(connection, uuid="UUID", command="FOO")
        assert (
            [c[0] for c in worker_m.call_args_list]
            == [('FOO', connection, 'UUID')])

        await runner.run(
            connection,
            uuid="UUID",
            command="FOO",
            params=dict(something=23, andanother=73))
        assert (
            [c[0] for c in worker_m.call_args_list]
            == [('FOO', connection, 'UUID')] * 2)
        assert (
            [c[1] for c in worker_m.call_args_list]
            == [{}, {'something': 23, 'andanother': 73}])

    app.local.run = AsyncMock()
    await runner.run(connection, uuid="UUID", command="LOCAL_FOO")
    assert (
        [c[0] for c in app.local.run.call_args_list]
        == [(hash(connection), 'UUID', 'LOCAL_FOO')])
    await runner.run(
        connection, uuid="UUID", command="LOCAL_FOO",
        params=dict(something=23, andanother=73))
    assert (
        [c[0] for c in app.local.run.call_args_list]
        == [(hash(connection), 'UUID', 'LOCAL_FOO')] * 2)
    assert (
        [c[1] for c in app.local.run.call_args_list]
        == [{}, {'andanother': 73, 'something': 23}])
