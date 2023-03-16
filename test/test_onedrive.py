# coding: utf8
import logging
import os

import pytest

from actions.downloader.onedrive_upload import Onedrive

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level='DEBUG')


def test_ls():
    """测试ls"""
    refresh_token = os.getenv('MSAL_ONEDRIVE_TOKEN')
    client_id = os.getenv('MSAL_CLIENT_ID')
    client_sec = os.getenv('MSAL_CLIENT_SECRET')
    o = Onedrive(client_id, client_sec, os.getenv('MSAL_DRIVE_TYPE'), os.getenv('MSAL_DRIVE_ID_TEST'))
    o.load_token(refresh_token)
    print(o.ls())
