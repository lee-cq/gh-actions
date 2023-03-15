#!/bin/env python3
# coding: utf8

import json
import os
import subprocess
import logging

import msal

logger = logging.getLogger('gh-actions.actions.onedrive-upload')

AUTHORITY = "https://login.microsoftonline.com/common"


class TokenError(Exception):
    """"""


class Onedrive:
    scope = ['Files.ReadWrite.All', ]

    def __init__(self, client_id, client_secret, authority=None):
        if not client_id:
            raise ValueError(f'Client ID mast NOT None. {client_id=}')
        if not client_secret:
            raise ValueError(f'Client Secret must NOT None. {client_secret}')

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
            return self
        except json.JSONDecodeError:
            logger.warning('反序列化失败，尝试从Refresh Token获取。')

        a = self.msal_app.acquire_token_by_refresh_token(_, scopes=self.scope)
        if 'error' in a:
            raise TokenError(f'Error={a.get("error")}\n'
                             f'Description={a.get("error_description")}')
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
            raise ValueError()

    def request(self, method, url, headers=None, body=None, **kwargs):
        """

        :param method:
        :param url:
        :param headers:
        :param body:
        :param kwargs
        :return:
        """


if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()

    refresh_token = os.getenv('MSAL_ONEDRIVE_TOKEN')
    o = Onedrive('f4c32538-9a41-43b1-825a-98b2c5411eda', 'CnU8Q~Az1sA5g.wn6E6vqSsbH0RZjbVqNas9ybWP')
    nt = o.msal_app.acquire_token_by_refresh_token(refresh_token=refresh_token, scopes=[])
    print(json.dumps(nt))
