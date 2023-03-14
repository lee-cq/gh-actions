#!/bin/env python3
# coding: utf8
"""

"""
import os
import sys
import logging
from pathlib import Path

ACTIONS_DIR = Path(__file__).parent.parent.parent
sys.path.append(str(ACTIONS_DIR))

logger = logging.getLogger('actions.bin.upload_onedrive_token')
logging.basicConfig(level='DEBUG')

from actions.downloader.onedrive_upload import Onedrive


def set_env(file: Path):
    """"""
    for line in file.read_text(encoding='utf8').split('\n'):
        if '=' in line:
            k, v = line.split('=')
            logger.info('SET ENV %s  --> %s', k, v)
            os.environ.update({k: v})


if Path('.env').exists():
    set_env(Path('.env'))

CLIENT_ID = os.getenv('MSAL_CLIENT_ID')
CLIENT_SECRET = os.getenv('MSAL_CLIENT_SECRET')
TOKEN = os.getenv('MSAL_ONEDRIVE_TOKEN')

if not (CLIENT_ID and CLIENT_SECRET and TOKEN):
    raise ValueError("未找到OneDrive环境变量。")

one = Onedrive(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, ).load_token(TOKEN)
print('New Token is ', one.get_token_from_cache()[:20])
one.save_cache()
