# -*- coding: UTF-8 -*-
"""
    tests.session_test
    ~~~~~~~~~~~~~~~~~~

    Testing sessions

    :copyright: (c) 2013 by netzinformatik UG.
    :author: Tobias Werner <mail@tobiaswerner.net>
    :license: BSD, see LICENSE for more details.
"""

import datetime
import cPickle

import mock

from flask_redis.session import RedisSession, RedisSessionInterface
from tests import FlaskRedisTestCase


class RedisSessionTest(FlaskRedisTestCase):
    def _setUp(self):
        initial = dict(a='test1', b='test2')
        self.session_object = RedisSession(sid='test123', initial=initial)

    def test_init(self):
        self.assertIsNotNone(self.session_object)
        self.assertFalse(self.session_object.new)

    def test_modify(self):
        self.assertFalse(self.session_object.modified)
        self.session_object['foo'] = 'foo'
        self.assertTrue(self.session_object.modified)

    def test_initial_data(self):
        self.assertEqual('test1', self.session_object.get('a'))
        self.assertEqual('test2', self.session_object['b'])

    def test_set_data(self):
        self.assertNotIn('data', self.session_object)
        test_data = u'test_data'
        self.session_object['data'] = test_data
        self.assertIn('data', self.session_object)
        self.assertEqual(test_data, self.session_object.get('data'))


class RedisSessionInterfaceTest(FlaskRedisTestCase):
    def _setUp(self):
        self.redis_instance = mock.MagicMock(name='redis_instance')
        self.session_interface = RedisSessionInterface(
            redis=self.redis_instance)
        self.session_object = mock.MagicMock(name='redis_session')

    def test_generate_sid(self):
        sid = RedisSessionInterface.generate_sid()
        self.assertIsInstance(sid, str)
        self.assertTrue(not len(sid) < 16)
        self.assertNotEqual(sid, self.session_interface.generate_sid())

    def test_open_new_session(self):
        request = mock.Mock(name='request')
        cookies_get = mock.Mock(name='cookies.get', return_value=None)
        request.cookies.get = cookies_get

        generate_sid = mock.Mock(name='generate_sid', return_value='new__sid')
        self.session_interface.generate_sid = generate_sid

        session = self.session_interface.open_session(self.app, request)

        self.assertIsInstance(session, RedisSession)
        self.assertEqual('new__sid', session.sid)
        self.assertTrue(session.new)

    def test_open_session_with_spoofed_sid(self):
        request = mock.Mock(name='request')
        cookies_get = mock.Mock(name='cookies.get', return_value='spoofed_sid')
        request.cookies.get = cookies_get

        self.redis_instance.exists.return_value = False

        generate_sid = mock.Mock(name='generate_sid',
                                 return_value='secure__sid')
        self.session_interface.generate_sid = generate_sid

        session = self.session_interface.open_session(self.app, request)

        self.redis_instance.exists.assert_called_with(
            'session:spoofed_sid:data')
        self.assertIsInstance(session, RedisSession)
        self.assertEqual('secure__sid', session.sid)

    def test_open_existing_session(self):
        request = mock.Mock(name='request')
        cookies_get = mock.Mock(name='cookies.get', return_value='known_sid')
        request.cookies.get = cookies_get

        self.redis_instance.exists.return_value = True

        rv = cPickle.dumps(dict(a='test_A', b='test_B'))
        self.redis_instance.get.return_value = rv

        session = self.session_interface.open_session(self.app, request)

        cookies_get.assert_called_with(self.app.session_cookie_name)
        self.redis_instance.exists.assert_called_with('session:known_sid:data')
        self.redis_instance.get.assert_called_with('session:known_sid:data')

        self.assertIn('a', session)
        self.assertEqual('test_A', session['a'])
        self.assertIn('b', session)
        self.assertEqual('test_B', session['b'])

    def test_get_redis_expiration_time(self):
        self.assertTrue(self.session_object.permanent)
        lifetime = RedisSessionInterface.get_redis_expiration_time(
            self.app,
            self.session_object
        )

        self.assertIs(self.app.permanent_session_lifetime, lifetime)

    def test_get_redis_expiration_time_not_permanent(self):
        self.session_object.permanent = False
        self.assertFalse(self.session_object.permanent)

        lifetime = RedisSessionInterface.get_redis_expiration_time(
            self.app,
            self.session_object
        )

        self.assertIsInstance(lifetime, datetime.timedelta)
        self.assertEqual(1, lifetime.days)

    def test_save_session_sets_cookie(self):
        get_cookie_domain = mock.Mock(name='get_cookie_domain')
        get_cookie_domain.return_value = 'example.com'
        self.session_interface.get_cookie_domain = get_cookie_domain

        get_expiration_time = mock.Mock(name='get_expiration_time')
        _datetime = mock.Mock(name='datetime')
        get_expiration_time.return_value = _datetime

        self.session_interface.get_expiration_time = get_expiration_time

        response = mock.Mock(name='response')

        self.session_object.sid = '__123__'

        self.assertFalse(not self.session_object)

        self.session_interface.save_session(self.app, self.session_object,
                                            response)

        get_expiration_time.assert_called_with(self.app, self.session_object)

        response.set_cookie.assert_called_with('session', '__123__',
                                               domain='example.com',
                                               expires=_datetime,
                                               httponly=True)

    def test_save_session_deletes_cookie(self):
        get_cookie_domain = mock.Mock(name='get_cookie_domain')
        get_cookie_domain.return_value = 'example.com'
        self.session_interface.get_cookie_domain = get_cookie_domain

        response = mock.Mock(name='response')

        self.session_object.sid = '__123__'
        self.session_object.modified = True

        self.session_object.__nonzero__.return_value = False
        self.assertTrue(not self.session_object)

        self.session_interface.save_session(self.app, self.session_object,
                                            response)

        response.delete_cookie.assert_called_with('session',
                                                  domain='example.com')

        self.redis_instance.delete.assert_called_with('session:__123__:data')