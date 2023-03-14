#!/bin/env python3
# coding: utf8

import json
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
    refresh_token = '0.AXEAEaSLS6NOsk2V4JDzDPRjpzglw_RBmrFDglqYssVBHtpxADg.AgABAAEAAAD--DLA3VO7QrddgJg7WevrAgDs_wUA9P-P8qryn5bS2895_5kftpdXMnXDOX-mna4G7XTUYLlSXp9a0UuWoDRMWYXuvm8pws1jcB847UyiT6-E1J4_gXzdMFax_lewteervtkzIBp8p9qA7ROyiwD4a_bzTxTP7QZ9e92KHiVZuxoStnsXvtCeJpNIIBbmtEpFvsSiIrSEueuXnzH5x4XrCpLn-Ito0VZP_-8DZASdN2UpqEwIHr3HRm19PFDchz1xwXcGPuGQQn-1D3l3EgDqZL3elal3vKCgQmM_eKbRwtN4MC8nyqoz38naM4bC_OBjb7PU_yEF8grLy2UhzGUUMmE_IqevLF-7hvkVMCXSw3e2bvGpoGT7z-PN8lTJ72LtNPJhK7N_s370r5x7_6WkZ2ypEWRpS_hV-UHwzYgHxaLbv-WBfCMFddyn-mTXsEIPWHZNSiSO2srDrSuFx6BOGnOpaexihfh2vjI3GwFyNq04p-HivpI66gHNtFfdEOOobIUdiKI8YLjV4p6wqrgUh_rzG6tKScMGWW6udEOyrJ4fso7m3qFIDBH1twqi2z9wAXfBOrAihN5e1xfre2px0s5fG03-F6DVxXDCWKDXQyAuc1my1pVHRg6TM57gR_GViQbZao7-HI30EANZnje1VpBEXqjuxdSIqaDY_7sq-E8VnC9WmVek94ajuh7_fcIm4sLO2IpIh7lAM6fNlkaL3RXwUks561qwLpuRibAjYzMv8LMPOvw3YPxleCfacuaJY1Z5NOEC9a3iQt9hjhiNYJxJpR12wMUeFZcj7cHjo2W35qYid-y4DfJSXgEs8S5So_ctSiyKAuk8wa4pXOg6KLbblD42BvOK'
    o = Onedrive('f4c32538-9a41-43b1-825a-98b2c5411eda', 'CnU8Q~Az1sA5g.wn6E6vqSsbH0RZjbVqNas9ybWP')
    nt = o.msal_app.acquire_token_by_refresh_token(refresh_token=refresh_token, scopes=[])
    print(json.dumps(nt))
