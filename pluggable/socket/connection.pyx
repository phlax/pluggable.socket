# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True
# cython: binding=True

from typing import Union

import websockets

import rapidjson as json

from .app cimport SocketApp
from .socket cimport SocketWrapper
from .user cimport SocketUser


cdef class SocketConnection(object):

    def __cinit__(
            self,
            SocketWrapper socket,
            connection: websockets.WebSocketServerProtocol,
            str path):
        self.socket = socket
        self.connection = connection
        self.path = path

    def __hash__(self) -> int:
        return hash(self.connection)

    @property
    def app(self) -> SocketApp:
        return self.socket.app

    @property
    def ip(self) -> str:
        return self.connection.remote_address[0]

    @property
    def port(self) -> int:
        return self.connection.remote_address[1]

    cpdef handle_request(self, session, dict msg):
        self.session = session
        self.app.loop.create_task(
            self.app.runner.run(self, **msg))

    cpdef log_request(self, dict msg):
        print(
            ' '.join([
                str(m) for m
                in ['app.socket.recv', self.ip, self.port, msg]]))

    cpdef dict parse_request(self, str msg):
        return json.loads(msg)

    async def connect(self) -> None:
        # print("got connection")
        await self.handle_connection()
        while True:
            msg = self.parse_request(await self.connection.recv())
            # print("got message")
            self.log_request(msg)
            self.handle_request(await self.handle_session(), msg)

    async def _get_session(self):
        if "session" in self.app.socket.connections[hash(self)]:
            return (
                SocketUser(hash(self)),
                self.app.socket.connections[hash(self)]["session"])
        session_key = self.connection.request_headers.get(
            'Sec-Websocket-Protocol')
        return (
            SocketUser(hash(self)),
            (await self.socket.sessions.get(session_key)
             if session_key
             else None))

    async def handle_session(self) -> Union[str, None]:
        user, session = await self._get_session()
        if not session:
            return
        await user.load(session)
        return session

    async def handle_connection(self) -> None:
        await self.validate_connection()
        session = await self.handle_session()
        if session:
            # notify user of success
            await self.socket.send(
                {'msg': 'connected', 'user': session},
                [hash(self)])

    async def validate_connection(self):
        # check nonce or somesuch ?
        pass


class Py__SocketConnection(SocketConnection):
    pass
