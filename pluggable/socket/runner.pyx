# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True
# cython: binding=True

from typing import Dict

from aioworker.worker cimport Worker

from .connection cimport SocketConnection
from .request cimport SocketRequest

from pluggable.core.exceptions cimport UnrecognizedCommand


cdef class SocketRunner(object):
    max_request_rate = 60

    def __init__(self, app):
        self.app = app

    @property
    def worker(self) -> Worker:
        return self.app.worker

    async def run_worker(
            self,
            str command,
            SocketConnection connection,
            str uuid,
            **kwargs) -> None:
        response = await self.worker.tasks[command].call(
            SocketRequest(
                connection=hash(connection),
                params=kwargs))
        await self.app.socket.send(
            dict(uuid=uuid,
                 response=response), [hash(connection)])

    async def run(
            self,
            SocketConnection connection,
            uuid: str = None,
            cmd: str = None,
            command: str = None,
            params: dict = None) -> None:
        command = command or cmd
        params = params or {}
        if command in self.app.local.commands:
            await self.app.local.run(hash(connection), uuid, command, **params)
        elif command in self.worker.tasks:
            await self.run_worker(command, connection, uuid, **params)
        else:
            raise UnrecognizedCommand(command)


class Py__SocketRunner(SocketRunner):
    pass
