
from pluggable.core.app cimport App

from .socket cimport SocketWrapper
from .runner cimport SocketRunner
from .local cimport LocalRunner


cdef class SocketApp(App):
    cdef public local
    cdef public socket
    cdef public runner
    cpdef serve(self)
    cpdef SocketWrapper _wrapper(self)
    cpdef SocketRunner _runner(self)
    cpdef LocalRunner _local_runner(self)
