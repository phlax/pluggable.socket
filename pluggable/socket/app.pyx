# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True
# cython: binding=True

from importlib import import_module

import websockets

from .socket cimport SocketWrapper
from .runner cimport SocketRunner
from .local cimport LocalRunner

from pluggable.core.app cimport App


default_config = (
    ('plugins', ()),
    ('ip', '0.0.0.0'),
    ('port', '7777'),
    ('worker', 'redis://redis/3'),
    ('caches', dict(
        session="redis://redis/1",
        l10n="redis://redis/2")))


cdef class SocketApp(App):

    @property
    def default_config(self):
        return default_config

    cpdef create_hooks(self):
        self.hooks['auth.sessions'] = self.create_hook()
        self.hooks['tasks.worker'] = self.create_hook()
        self.hooks['tasks.local'] = self.create_hook()
        self.hooks['caches'] = self.create_hook(dict(sync=False))
        self.hooks['worker'] = self.create_hook()

    cpdef serve(self):
        self.socket = self._wrapper()
        self.runner = self._runner()
        self.loop.create_task(self.connect())

    cpdef SocketWrapper _wrapper(self):
        return SocketWrapper(self)

    cpdef SocketRunner _runner(self):
        return SocketRunner(self)

    cpdef LocalRunner _local_runner(self):
        return LocalRunner(self)

    async def connect(self) -> websockets.WebSocketServerProtocol:
        return await self.socket.serve()

    async def on_start(self) -> None:
        await self.hooks["caches"].gather(self.caches)
        self.sessions = self.hooks['auth.sessions'].get(self)
        for task in self.hooks['tasks.worker'].gather().values():
            import_module(task)
        self.commands = self.hooks['tasks.local'].gather()
        self.local = self._local_runner()
        self.serve()

    def log(self, *msgs) -> None:
        print('app: ' + ' '.join(str(m) for m in msgs))


class Py__SocketApp(SocketApp):
    pass
