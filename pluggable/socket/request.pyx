# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True


cdef class SocketRequest(object):

    def __cinit__(self, session=None, params: dict = None, args: list = None):
        self.session = session
        self.params = params or {}
        self.args = args or []


class Py__SocketRequest(SocketRequest):
    pass
