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
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(obj):
            obj.modified = True

        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    __serializer = cPickle
    __session_class = RedisSession

    def __init__(self, redis, prefix='session:'):
        """

        :type redis: redis.StrictRedis
        :type prefix: str
        """
        self.redis = redis
        self.prefix = prefix

    @staticmethod
    def generate_sid():
        """

        :rtype: str
        """
        return hashlib.sha1(str(uuid.uuid4()) + str(uuid.uuid1())).hexdigest()

    @staticmethod
    def get_redis_expiration_time(app, session):
        """

        :type app: flask.Flask
        :type session: RedisSession
        :rtype: datetime.timedelta
        """
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=1)

    def open_session(self, app, request):
        """

        :type app: flask.Flask
        :type request: flask.Request
        :rtype: RedisSession
        """
        sid = request.cookies.get(app.session_cookie_name)
        if not sid or not self.redis.exists(self.prefix + sid + ':data'):
            sid = self.generate_sid()
            return self.__session_class(sid=sid, new=True)

        val = self.redis.get(self.prefix + sid + ':data')
        data = self.__serializer.loads(val)
        return self.__session_class(data, sid=sid)

    def save_session(self, app, session, response):
        """

        :type app: flask.Flask
        :type session: RedisSession
        :type response: flask.Response
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