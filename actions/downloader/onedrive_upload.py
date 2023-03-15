#!/bin/env python3
# coding: utf8

import json
import os
import subprocess
import logging
import urllib.parse
from abc import ABC
from typing import List

import msal
import requests

logger = logging.getLogger('gh-actions.actions.onedrive-upload')

AUTHORITY = "https://login.microsoftonline.com/common"


class TokenError(Exception):
    """"""


class Ms365Client(ABC):
    API_POINT_V1 = 'https://graph.microsoft.com/v1.0'
    API_POINT_BETA = 'https://graph.microsoft.com/beta'

    def __init__(self, client_id, client_secret, scope: List, bate_api=False, authority=None):
        if not client_id:
            raise ValueError(f'Client ID mast NOT None. {client_id=}')
        if not client_secret:
            raise ValueError(f'Client Secret must NOT None. {client_secret}')

        self.scope = scope
        self.api_point = self.API_POINT_BETA if bate_api else self.API_POINT_V1

        self.token_cache = msal.SerializableTokenCache()
        self.msal_app = msal.ConfidentialClientApplication(
            client_id=client_id,
            authority=authority or AUTHORITY,
            client_credential=client_secret,
            token_cache=self.token_cache
        )

    def load_token(self, _):
        """加载Token"""
        try:
            self.token_cache.deserialize(_)
            logger.info('Load Token From deserialize Success.')
            return self
        except json.JSONDecodeError:
            logger.warning('反序列化失败，尝试从Refresh Token获取。')

        a = self.msal_app.acquire_token_by_refresh_token(refresh_token=_, scopes=self.scope)
        if 'error' in a:
            raise TokenError(f'Error={a.get("error")}\n'
                             f'Description={a.get("error_description")}')
        logger.info('Load Token From Refresh Token Success.')
        return self

    def save_cache(self):
        """将Token保存到 GitHub Secret"""
        if self.token_cache.has_state_changed:
            subprocess.run(['gh', 'secret', 'set', 'MSAL_ONEDRIVE_TOKEN'],
                           input=self.token_cache.serialize().encode(),
                           check=True
                           )

    def get_token_from_cache(self):
        """

        :return: Access Token
        """
        accounts = self.msal_app.get_accounts()
        if accounts:
            result = self.msal_app.acquire_token_silent(self.scope, account=accounts[0])
            self.save_cache()
            return result['access_token']
        else:
            raise ValueError('Can not get Account.')

    def request(self, method, url, headers=None, **kwargs):
        """

        :param method:
        :param url:
        :param headers:
        :param kwargs
        :return:
        """
        if not headers:
            headers = dict()

        headers.setdefault('Authorization', f'Bearer {self.get_token_from_cache()}')

        return requests.request(method=method, url=url, headers=headers, **kwargs)


class Onedrive(Ms365Client):
    scope = ['Files.ReadWrite.All', 'Sites.ReadWrite.All']

    def __init__(self, client_id, client_secret, drive_type, drive_id=None):
        self.drive_id = drive_id
        self.drive_type = drive_type

        super().__init__(client_id, client_secret, self.scope)

        self.api_point += self.base_uri

    @property
    def base_uri(self) -> str:
        _enum = {
            'drive': f'/drives/{self.drive_id}',
            'group': f'/groups/{self.drive_id}/drive',
            'me': '/me/drive',
            'site': f'/sites/{self.drive_id}/drive',
            'user': f'/users/{self.drive_id}/drive',
        }

        if _base_url := _enum.get(self.drive_type):
            return _base_url
        raise TypeError(f'Not Support Drive. {self.drive_type}')

    def ls(self, path='/'):
        """列出驱动器文件"""
        url = self.api_point + '/root:' + urllib.parse.quote(path) + ':/children'
        return self.request('get', url)

    def upload_stream(self, parent_id, data: bytes):
        """

        :param parent_id: OneDrive Path
        :param data: 数据内容
        :return:
        """
        url = self.api_point + '/items'

    def create_upload_session(self) -> str:
        """"""


if __name__ == '__main__':
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(level='DEBUG')

    refresh_token = os.getenv('MSAL_ONEDRIVE_TOKEN')
    CLIENT_ID = os.getenv('MSAL_CLIENT_ID')
    CLIENT_SEC = os.getenv('MSAL_CLIENT_SECRET')
    o = Onedrive(CLIENT_ID, CLIENT_SEC, os.getenv('MSAL_DRIVE_TYPE'), os.getenv('MSAL_DRIVE_ID_TEST'))
    o.load_token(refresh_token)
    print(o.ls())
