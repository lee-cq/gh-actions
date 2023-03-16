#!/bin/env python3
# coding: utf8
"""

"""
import logging
import os
import unittest
import sys
from pathlib import Path

sys.path.append(os.getcwd())

from actions.downloader.onedrive_upload import Onedrive

logging.basicConfig(level='DEBUG')


def set_env(file: Path):
    """"""
    for line in file.read_text(encoding='utf8').split('\n'):
        if '=' in line:
            k, v = line.split('=')
            os.environ.update({k: v})


class TestOnedrive(unittest.TestCase):
    """"""

    @classmethod
    def setUpClass(cls) -> None:
        _env_path = Path(__file__).parent.joinpath('.env')

        if _env_path.exists():
            set_env(_env_path)

        cls.client_id = os.getenv('MSAL_CLIENT_ID')
        cls.client_secret = os.getenv('MSAL_CLIENT_SECRET')
        cls.token = os.getenv('MSAL_ONEDRIVE_TOKEN')

        if not cls.client_id and not cls.client_secret:
            raise ValueError()

        cls.onedrive = Onedrive(client_id=cls.client_id, client_secret=cls.client_secret)

    def test_0_load_token(self):
        """"""
        _token = self.token

        if not _token:
            raise ValueError()

        self.onedrive.load_token(_token)

    def test_1_save_token(self):
        """"""
        cache = self.onedrive.get_token_from_cache()
        self.assertNotEqual(cache, '')
        self.onedrive.save_cache()
        print(cache)

# unittest.main()
