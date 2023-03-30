import json
import subprocess

import msal
from requests import Session
from requests.auth import AuthBase
from urllib.parse import quote_from_bytes

AUTHORITY = "https://login.microsoftonline.com/common"


class AuthBearer(AuthBase):
    def __init__(self, tenant_id, client_id, client_secret, refresh_token):
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

    def __call__(self, r):
        r.headers['Authorization'] = f'Bearer '
        return r


class MsClient(Session):
    def __init__(self, tenant_id, client_id, client_secret, refresh_token):
        super().__init__()
        self.tenant_id = tenant_id
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token

        self.headers.update({
            'Content-Type': 'application/json'
        })
        self.prepare_request

    def get_access_token(self, soc=[]):
        """"""
        path = f'/{self.tenant_id}/oauth2/v2.0/token'
        end_point = 'https://login.microsoftonline.com'

        body = dict(
            client_id=self.client_id,
            scope=' '.join(soc),
            refresh_token=self.refresh_token,
            grant_type='refresh_token',
            client_secret=self.client_secret
        )
        body = '&'.join(
            [f'{quote_from_bytes(k.encode())}={quote_from_bytes(v.encode())}'
             for k, v in body.items()]
        )

        _resp = self.post(
            end_point + path,
            data=body,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded'
            }

        )

        _d = _resp.json()
        self.refresh_token = _d['refresh_token']
        self.headers.update(dict('A'))

        return _d['access_token']


if __name__ == '__main__':
    pass
