# distutils: define_macros=CYTHON_TRACE_NOGIL=1
# cython: linetrace=True


cdef class SocketUser(object):

    def __init__(self, connection):
        self.connection = connection

    @property
    def is_anon(self):
        return not self.session or not self.session.user

    @property
    def session(self):
        return self._session

    async def load(self, session):
        self._session = session
