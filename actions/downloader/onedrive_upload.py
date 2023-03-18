#!/bin/env python3
# coding: utf8

import json
import os
import re
import subprocess
import logging
import urllib.parse
from abc import ABC
from pathlib import Path
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

    @property
    def env_token_name(self):
        raise NotImplemented

    def load_token(self, _):
        """加载Token"""
        try:
            self.token_cache.deserialize(_)
            logger.info('Load Token From deserialize Success.')
            return self
        except json.JSONDecodeError:
            logger.warning('反序列化失败，尝试从Refresh Token获取。')

        loaded = self.msal_app.acquire_token_by_refresh_token(refresh_token=_, scopes=self.scope)
        if 'error' in loaded:
            raise TokenError(f'Error={loaded.get("error")}\n'
                             f'Description={loaded.get("error_description")}')
        logger.info('Load Token From Refresh Token Success.')
        return self

    def save_cache(self):
        """将Token保存到 GitHub Secret"""
        env_file = Path('.env')
        if self.token_cache.has_state_changed:
            if env_file.exists():
                env_text = env_file.read_text()
                new_token = self.get_refresh_token()['secret']
                old_token = re.findall(r'MSAL_ONEDRIVE_TOKEN=(.*?)\n', env_text)[0]
                if old_token and new_token:
                    env_file.write_text(env_text.replace(old_token, new_token))
            else:
                subprocess.run(['gh', 'secret', 'set', 'MSAL_ONEDRIVE_TOKEN'],
                               input=self.token_cache.serialize().encode(),
                               check=True
                               )
                logger.info('Update OneDrive Token to Github Actions Secret Success.')

    def get_refresh_token(self):
        """"""
        return self.token_cache.find('RefreshToken')

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

        return requests.request(method=method, url=url, headers=headers, **kwargs).json()


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

    def ls(self, path='') -> dict:
        """列出驱动器文件

        :param path: 驱动器中目录的绝对路径，只能是一个目录的路径。
        :rtype dict 该路径中的文件属性
        """
        quote_path = f':{urllib.parse.quote(path)}:' if path else ''

        url = self.api_point + '/root' + quote_path + '/children'
        return self.request('GET', url)

    def mkdir(self, dirname, parent_path='', exist='rename'):
        """创建一个目录

        :param parent_path: 父路径
        :param dirname: 新的DirName
        :param exist: 当dir已经存在时，如何处理？
        :return:
        """
        quote_path = f':{urllib.parse.quote(parent_path)}:' if parent_path else ''

        url = self.api_point + '/root' + quote_path + '/children'
        data = {
            "name": dirname,
            "folder": {},
            "@microsoft.graph.conflictBehavior": exist
        }
        return self.request('POST', url, json=data)

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


    def jsonify(data: dict):
        return json.dumps(
            data, ensure_ascii=False, indent=2
        )


    refresh_token = os.getenv('MSAL_ONEDRIVE_TOKEN')
    CLIENT_ID = os.getenv('MSAL_CLIENT_ID')
    CLIENT_SEC = os.getenv('MSAL_CLIENT_SECRET')
    o = Onedrive(CLIENT_ID, CLIENT_SEC, os.getenv('MSAL_DRIVE_TYPE'), os.getenv('MSAL_DRIVE_ID_TEST'))
    o.load_token(refresh_token)
    print(o.get_refresh_token())
    print(jsonify(o.mkdir('test', '/test')))
