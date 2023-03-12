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
    # a = MsClient(
    #     tenant_id='4b8ba411-4ea3-4db2-95e0-90f30cf463a7',
    #     client_id='f4c32538-9a41-43b1-825a-98b2c5411eda',
    #     client_secret='CnU8Q~Az1sA5g.wn6E6vqSsbH0RZjbVqNas9ybWP',
    #     refresh_token='0.AXEAEaSLS6NOsk2V4JDzDPRjpzglw_RBmrFDglqYssVBHtpxADg.AgABAAEAAAD--DLA3VO7QrddgJg7WevrAgDs_wUA9P_E5UqO9mCYUamnVMnH4Lg6DAfnta2-OHoMfVEYfusfpOC7BRYk_7L3zAz3myG26zc6KJ5YlbXSk8mkf9VfVcfDNjIAGUZbPwzQ38XBVC0TdlDAeOdVYpldXo_EFS9xtcBfAIMD8Vpfr_LHXvYCLeFf2IjWisbBU5Zyho7hyQfh1W7Lk4h7b25C8hpjOeANfd5ucYCgfjy4_-uEr8xwggrihO9lykWwabieAwFeyBslDDnrG5izFgiA4nUcfCWCytVLHJxyYJFTnm0JdMD909GNEHC6XKQIMtfn55RpI6g9WMwtEmZ8-GN3PvzF5WEMYNDqFcvrleMEr-VKosX_Y6Zv0D3q_X8hrcP2S2vO6YMS4YPstx1Nvks1RHSh_PWwDnryLR8oihFdFQ4j21S-1KwDDZvjGWB-xOUPINq8tBXadXtL4l2tPWfb8HvAswqsjAXroF17vst9VxMZ-fBQseyRdLVA4rqbJTMhew0Q8Xj0rsjBtqaLdq8DOBVW7FV2iDgyS2kOxGEwh2u54DIZN9OxdIznIoV91CX5Okz0F0WO8-zxcasejZbz-mAHQ1eeTh5O74RM43nyrcATKFZTQVaRjyuZVPijhrThi58Q4zjnGjqlYEPdtqQ_YIDMn69zcmCF0lJP9AUh5sP-xbddorIPFdh6lu-JRXGGZPyHxZ_8Wu0X_ayMkDS2NbovN99hxe5HzVEQDFDFm7ILo0pX5hjxL4t6rmc2qtZ7CWS6V4qHHYRSZSYJqdcPiPyrlm4mWmvV3yUkOuBnO5uam08hGtdsySRtPXxoCEsvUSCvb3dnqnwW-k3pE_6achm4angw'
    # )
    # print(a.get_access_token())
