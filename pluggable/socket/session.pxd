

cdef class SocketSessions:
    cdef app
    cdef _backend

    cpdef get(self, k)
    