# -*- coding: UTF-8 -*-
"""
    flask.ext.redis
    ~~~~~~~~~~~~~~~

    Utilise Redis in your Flask application

    :copyright: (c) 2013 by netzinformatik UG.
    :author: Tobias Werner <mail@tobiaswerner.net>
    :license: BSD, see LICENSE for more details.
"""
import redis

try:
    from flask import _app_ctx_stack as connection_stack
except ImportError:
    from flask import _request_ctx_stack as connection_stack


__version__ = '0.1-dev'


class Redis(object):
    """This is the main extension class. Pass your :class:`flask.Flask`
    instance to the constructor or call :meth:`init_app` later when no
    instance is around at the moment::

        import flask
        import flask.ext.redis

        app = flask.Flask(__name__)
        redis = redis.Redis(app)
    """
    def __init__(self, app=None):
        """

        :type app: flask.Flask
        :rtype: None
        """
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Use this method directly when :class:`Redis` was instantiated
        without an app object::

            import flask
            import flask.ext.redis

            app = flask.Flask(__name__)
            redis = redis.Redis()

            redis.init_app(app)

        This method sets the default configuration, expecting a Redis-instance
        listening on 127.0.0.1:6379 using DB index 0 when not specified
        differently.

        Additionally applies server-side sessions when REDIS_SESSION is set
        to True in the configuration. See :mod:`flask.ext.redis.session`
        for more info.

        :type app: flask.Flask
        """
        app.config.setdefault('REDIS_HOST', 'localhost')
        app.config.setdefault('REDIS_PORT', 6379)
        app.config.setdefault('REDIS_DB', 0)
        app.config.setdefault('REDIS_PASSWORD', None)
        app.config.setdefault('REDIS_SOCKET_TIMEOUT', None)
        app.config.setdefault('REDIS_CONNECTION_POOL', None)
        app.config.setdefault('REDIS_CHARSET', 'utf-8')
        app.config.setdefault('REDIS_ERRORS', 'strict')
        app.config.setdefault('REDIS_DECODE_RESPONSES', False)
        app.config.setdefault('REDIS_UNIX_SOCKET_PATH', None)

        app.config.setdefault('REDIS_SESSION', False)

        if app.config.get('REDIS_SESSION'):
            from session import RedisSessionInterface
            app.session_interface = RedisSessionInterface(self)

        if hasattr(app, 'teardown_appcontext'):
            app.teardown_appcontext(self._teardown)
        else:
            app.teardown_request(self._teardown)

    def _teardown(self, exception):
        """Closes redis connection on application teardown.

        :param exception:
        :return:
        """
        context = connection_stack.top
        if context is not None:
            if hasattr(context, 'redis'):
                context.redis.connection_pool.disconnect()

    def _connect(self):
        """

        :rtype: redis.StrictRedis
        """
        return redis.StrictRedis(
            host=self.app.config['REDIS_HOST'],
            port=self.app.config['REDIS_PORT'],
            db=self.app.config['REDIS_DB'],
            password=self.app.config['REDIS_PASSWORD'],
            socket_timeout=self.app.config['REDIS_SOCKET_TIMEOUT'],
            connection_pool=self.app.config['REDIS_CONNECTION_POOL'],
            charset=self.app.config['REDIS_CHARSET'],
            errors=self.app.config['REDIS_ERRORS'],
            decode_responses=self.app.config['REDIS_DECODE_RESPONSES'],
            unix_socket_path=self.app.config['REDIS_UNIX_SOCKET_PATH']
        )

    @property
    def _connection(self):
        """Calls :meth:`connect` to create a redis instance and stores it
        to the application context on first use.

        :rtype: redis.StrictRedis
        """
        context = connection_stack.top
        if context is not None:
            if not hasattr(context, 'redis'):
                context.redis = self._connect()
            return context.redis

    def __getattr__(self, item):
        """Proxy method for redis instance. Allows us to use `self` as
        replacement for :class:`redis.StrictRedis`

        :type item:
        :rtype:
        """
        return getattr(self._connection, item)
