
from .user cimport SocketUser


cdef class SocketConnection:
     cdef public socket
     cdef public connection
     cdef public str path
     cpdef public user
     cpdef public session
     cpdef handle_request(self, session, dict msg)
     cpdef log_request(self, dict msg)
     cpdef dict parse_request(self, str msg)
