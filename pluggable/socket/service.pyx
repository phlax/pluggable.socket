# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True
# cython: binding=True


cdef class SocketService(object):

    def __cinit__(self, str ip, int port):
        self.ip = ip
        self.port = port


class Py__SocketService(SocketService):
    pass
