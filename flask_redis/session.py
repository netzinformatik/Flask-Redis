# -*- coding: UTF-8 -*-
"""
    flask.ext.redis.session
    ~~~~~~~~~~~~~~~~~~~~~~~

    Server-side sessions as proposed by `Flask Snippet 75
    <http://flask.pocoo.org/snippets/75/>`_.

    :copyright: (c) 2013 by netzinformatik UG.
    :author: Tobias Werner <mail@tobiaswerner.net>
    :license: BSD, see LICENSE for more details.
"""
import cPickle
import uuid
import hashlib
from datetime import timedelta

from werkzeug.datastructures import CallbackDict
from flask.sessions import SessionMixin, SessionInterface


class RedisSession(CallbackDict, SessionMixin):
    """Session data mapping"""

    def __init__(self, initial=None, sid=None, new=False):
        def on_update(obj):
            obj.modified = True

        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    """Session interface for providing redis-based session."""
    __serializer = cPickle
    __session_class = RedisSession

    def __init__(self, redis, prefix='session:'):
        """

        :param redis: :class:`redis.Strict`
        :param prefix: str
        """
        self.redis = redis
        self.prefix = prefix

    @staticmethod
    def generate_sid():
        """Generates a session ID.

        :returns: str
        """
        return hashlib.sha1(str(uuid.uuid4()) + str(uuid.uuid1())).hexdigest()

    @staticmethod
    def get_redis_expiration_time(app, session):
        """

        :param app: :class:`flask.Flask`
        :type app: flask.Flask
        :param session: :class:`flask.sessions.SessionMixin`
        :type session: SessionMixin
        :returns: :class:`datetime.timedelta`
        """
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        """Creates an instance of :class:`RedisSession` with corresponding
        data from the redis instance or a new and empty instance when no data
        exists. Also creates a new instance with generated ID on spoofed IDs
        preventing session fixation.

        :param app: :class:`flask.Flask`
        :type app: flask.Flask
        :param request: :class:`flask.Request`
        :type request: flask.Request
        :returns: RedisSession -- instance of :attr:`__session_class`
        """
        sid = request.cookies.get(app.session_cookie_name)
        if not sid or not self.redis.exists(self.prefix + sid + ':data'):
            sid = self.generate_sid()
            return self.__session_class(sid=sid, new=True)

        val = self.redis.get(self.prefix + sid + ':data')
        data = self.__serializer.loads(val)
        return self.__session_class(data, sid=sid)

    def save_session(self, app, session, response):
        """Saves session dict to redis and updating expiration time.
        Additionally deletes cookie when dict was emptied.

        :param app: :class:`flask.Flask`
        :type app: flask.Flask
        :param session: :class:`RedisSession`
        :type session: RedisSession
        :param response: :class:`flask.Response`
        :type response: flask.Response
        :returns: None
        """
        domain = self.get_cookie_domain(app)
        if not session:
            self.redis.delete(self.prefix + session.sid + ':data')
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        redis_exp = self.get_redis_expiration_time(app, session)
        cookie_exp = self.get_expiration_time(app, session)
        key = self.prefix + session.sid + ':data'
        seconds = int(redis_exp.total_seconds())
        value = self.__serializer.dumps(dict(session))
        self.redis.setex(key, seconds, value)
        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True,
                            domain=domain)