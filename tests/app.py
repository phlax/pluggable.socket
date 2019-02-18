# -*- coding: utf-8 -*-

from unittest.mock import patch, MagicMock

import pytest

from aioworker.worker import Worker

from pluggable.core.hooks import Hook
from pluggable.socket.app import (
    default_config,
    Py__SocketApp as SocketApp)
from pluggable.socket.local import LocalRunner
from pluggable.socket.runner import SocketRunner
from pluggable.socket.socket import SocketWrapper

from .base import AsyncMock, nested


def test_app_signature():
    with pytest.raises(TypeError):
        SocketApp()


class _MockWorker(Worker):
    pass


def MockWorker():
    return _MockWorker("BROKER")


class MockSocketWrapper(SocketWrapper):

    def __init__(self, app):
        self.app = app


class MockSocketRunner(SocketRunner):

    def __init__(self, app):
        self.app = app


class MockLocalRunner(LocalRunner):

    def __init__(self, app):
        self.app = app


@patch('pluggable.socket.app.Py__SocketApp.configure')
def test_app(configure_m):
    worker = MockWorker()
    app = SocketApp(worker, {})
    assert (
        [c[0] for c in configure_m.call_args_list]
        == [({},)])
    assert app.config == {}
    assert app.caches == {}
    assert app.hooks == {}
    assert app.plugins == {}
    assert app._plugins == []


@patch('pluggable.socket.app.Py__SocketApp.configure')
def test_app_create_config(configure_m, mocker):
    worker = MockWorker()
    app = SocketApp(worker, {})
    app.create_config({"foo": 7, "bar": 23})
    config = dict(default_config)
    config.update({"foo": 7, "bar": 23})
    assert app.config == config


@patch('pluggable.socket.app.Py__SocketApp.create_hook')
@patch('pluggable.socket.app.Py__SocketApp.configure')
def test_app_create_hooks(configure_m, hook_m):
    worker = MockWorker()
    hook_m.return_value = Hook()
    app = SocketApp(worker, {})
    app.hooks = dict(foo=23)
    app.create_hooks()
    assert (
        [c[0] for c in hook_m.call_args_list]
        == [({},), ({},), ({},), ({'sync': False},), ({},)])
    expected = {'foo': 23}
    expected.update({
        t: hook_m.return_value
        for t
        in ['tasks.local', 'tasks.worker',
            'auth.sessions', 'caches', 'worker']})
    assert app.hooks == expected


@pytest.mark.asyncio
async def test_app_connect():
    worker = MockWorker()

    with patch('pluggable.socket.app.Py__SocketApp.configure'):
        app = SocketApp(worker, {})

    app.socket = AsyncMock()
    await app.connect()
    assert (
        [c[0] for c in app.socket.serve.call_args_list]
        == [()])


@patch('pluggable.socket.app.Py__SocketApp._wrapper')
@patch('pluggable.socket.app.Py__SocketApp._runner')
@patch('pluggable.socket.app.Py__SocketApp.connect')
@patch('pluggable.socket.app.Py__SocketApp.configure')
def test_app_serve(configure_m, connect_m, runner_m, wrapper_m):
    worker = MockWorker()
    app = SocketApp(worker, {})
    app.loop = MagicMock()
    runner_m.return_value = MockSocketRunner(app)
    wrapper_m.return_value = MockSocketWrapper(app)
    app.serve()
    assert (
        [c[0] for c in connect_m.call_args_list]
        == [()])
    assert (
        [c[0] for c in runner_m.call_args_list]
        == [()])
    assert (
        [c[0] for c in wrapper_m.call_args_list]
        == [()])
    assert app.socket == wrapper_m.return_value
    assert app.runner == runner_m.return_value
    assert (
        [c[0] for c in app.loop.create_task.call_args_list]
        == [(connect_m.return_value, )])


@pytest.mark.asyncio
async def test_app_on_start():
    worker = MockWorker()
    with patch('pluggable.socket.app.Py__SocketApp.configure'):
        app = SocketApp(worker, {})
    app.caches = dict(foo=7, bar=23)
    app.hooks = {
        "caches": AsyncMock(),
        "auth.sessions": MagicMock(),
        "tasks.local": MagicMock(),
        "tasks.worker": MagicMock()}
    app.hooks[
        "tasks.worker"].gather.return_value.values.return_value = [17, 113]
    _patches = nested(
        patch('pluggable.socket.app.Py__SocketApp._local_runner'),
        patch('pluggable.socket.app.import_module'),
        patch('pluggable.socket.app.Py__SocketApp.serve'))
    with _patches as (local_m, import_m, serve_m):
        local_m.return_value = MockLocalRunner(app)
        await app.on_start()
        gathered_worker_tasks = app.hooks[
            "tasks.worker"].gather.return_value
        assert (
            [c[0] for c in local_m.call_args_list]
            == [()])
        assert (
            [c[0] for c in app.hooks["caches"].gather.call_args_list]
            == [({'bar': 23, 'foo': 7}, )])
        assert (
            [c[0] for c in app.hooks["auth.sessions"].get.call_args_list]
            == [(app, )])
        assert (
            [c[0] for c in app.hooks["tasks.local"].gather.call_args_list]
            == [()])
        assert (
            [c[0]
             for c
             in gathered_worker_tasks.values.call_args_list]
            == [()])
        assert (
            [c[0] for c in import_m.call_args_list]
            == [(17, ), (113, )])
        assert (
            [c[0] for c in serve_m.call_args_list]
            == [()])
