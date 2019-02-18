# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True

from typing import List

from .connection cimport SocketConnection


cdef class LocalRunner(object):

    def __cinit__(self, app):
        self.app = app

    @property
    def commands(self) -> List[str]:
        return self.app.commands.keys()

    async def run(
            self,
            connection: int,
            uuid: str,
            command: str,
            **kwargs) -> None:
        returns = await self.app.commands[command](
            connection, uuid, **kwargs)
        if not returns:
            return
        await self.app.socket.send(
            ('{"uuid": "%s", "response": %s}' % (uuid, returns.decode("utf8"))
             if type(returns) == bytes
             else dict(uuid=uuid, **returns)),
            [connection])


class Py__LocalRunner(LocalRunner):
    pass
