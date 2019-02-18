
from .app cimport SocketApp
from .connection cimport SocketConnection
from .service cimport SocketService


cdef class SocketWrapper(object):
    cdef public SocketApp app
    cdef public dict connections
    cdef public service
    cpdef public SocketConnection connect(self, websocket, str path)
    cpdef public disconnect(self, SocketConnection connection)
    cpdef public log(self, list msgs)
    cpdef public _log(self, connection, str connection_type)
    cpdef public listen(self)
    cpdef public serve(self)
