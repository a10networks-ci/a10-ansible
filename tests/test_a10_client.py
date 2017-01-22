from a10_ansible.a10_client import A10ClientBase

import unittest


class TestA10ClientBase(unittest.TestCase):
    self.client_args = {"host": "10.10.10.10", "version": 2.1,
                        "username": "admin", "password": "a10", "port": 443}
    self.target = A10ClientBase(**self.client_args)

    def test_connect(self):
        self.target.connect()

    def test_disconnect(self):
        self.target.disconnect()
