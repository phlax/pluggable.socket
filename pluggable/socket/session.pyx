

cdef class SocketSessions(object):

    def __cinit__(self, app):
        self.app = app
        self._backend = {}

    def __getitem__(self, k):
        return self._backend[k]

    def __setitem__(self, k, v):
        self._backend[k] = v

    def __delitem__(self, k):
        del self._backend[k]

    def __iter__(self):
        for k, v in self._backend.items():
            yield k, v

    cpdef get(self, k):
        return self._backend[k]
