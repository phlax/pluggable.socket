# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True
# cython: binding=True

from typing import Union

import rapidjson as json
import websockets

from .app cimport SocketApp
from .connection cimport SocketConnection
from .request cimport SocketRequest
from .utils cimport truncate
from .service cimport SocketService

cimport cython


cdef class SocketWrapper(object):
    ws = None

    def __cinit__(self, app: SocketApp):
        self.app = app
        self.connections = {}

    def __init__(self, app):
        self.listen()
        self.service = SocketService(app.config["ip"], app.config["port"])

    cpdef SocketConnection connect(
            self,
            websocket: websockets.WebSocketServerProtocol,
            str path):
        connection = SocketConnection(self, websocket, path)
        self.connections[hash(connection)] = dict(
            socket=connection.connection,
            connection=connection)
        self._log(connection, "connect")
        return connection

    cpdef disconnect(self, SocketConnection connection):
        del self.connections[hash(connection)]
        self._log(connection, "disconnect")

    cpdef listen(self):
        self.app.signals.listen(
            'auth.session.create',
            self.on_session_create)
        self.app.signals.listen(
            'auth.session.destroy',
            self.on_session_destroy)

    cpdef _log(self,
               connection: Union[SocketService, SocketConnection],
               str connection_type):
        self.log(['%s:' % connection_type, connection.ip, connection.port])
        self.app.signals.emit(
            'socket.%s' % connection_type,
            '%s:%s' % (connection.ip, connection.port))
        msg = (
            '%s (%s): %s %s'
            % (connection_type,
               hash(self),
               connection.ip,
               connection.port))
        self.app.loop.create_task(
            self.app.worker.tasks['log'].call(
                **dict(type="server", msg=msg)))

    cpdef serve(self):
        self._log(
            self.service,
            "listening")
        return websockets.serve(
            self.pipe,
            self.service.ip,
            self.service.port)

    cpdef log(self, list msgs):
        print('app.socket: ' + ' '.join([str(m) for m in msgs]))

    async def on_session_create(
            self,
            signal: str,
            session: str = None,
            connection: int = None) -> None:
        self.connections[connection]['session'] = session

    async def on_session_destroy(self, signal: str, connection: int) -> None:
        del self.connections[connection]['session']

    @cython.iterable_coroutine
    async def pipe(
            self,
            websocket: websockets.WebSocketServerProtocol,
            path: str) -> None:
        connection = self.connect(websocket, path)
        try:
            await connection.connect()
        except websockets.exceptions.ConnectionClosed:
            self.disconnect(connection)

    async def _send(
            self,
            websocket: websockets.WebSocketServerProtocol,
            msg: Union[dict, str, bytes]) -> None:
        msg = (
            msg
            if type(msg) in [str, bytes]
            else json.dumps(msg))
        await websocket.send(msg)
        ip, port = websocket.remote_address[:2]
        self.log(['send:', ip, port, truncate(str(msg))])

    async def send(
            self,
            msg: Union[dict, str, bytes],
            connections=None) -> None:
        if len(connections or []) > 0:
            for connection in connections:
                await self._send(self.connections[connection]['socket'], msg)
        elif len(self.connections) == 0:
            self.log(['failed sending, nothing connected!'])
        else:
            for connection in self.connections.values():
                await self._send(connection['socket'], msg)


class Py__SocketWrapper(SocketWrapper):
    pass
