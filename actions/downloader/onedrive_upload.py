#!/bin/env python3
# coding: utf8

import json
import os
import re
import subprocess
import logging
import urllib.parse
from abc import ABC
from collections import defaultdict
from pathlib import Path, PurePosixPath
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

        self.WORKDIR = '/'

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

    def request(self, method, url, headers=None, **kwargs) -> requests.Response:
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
    exception_char = r'\/|&?><;:\'"$'

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

    def quote_path(self, path) -> str:
        """对 OneDrive 对路径进行编码

        :param path:
        :return:
        """
        if path == '/':
            path = ''

        if path and not path.startswith('/'):
            raise ValueError('path 必须是绝对路径，所以需要以 / 开始。')

        return self.api_point + '/root' + (f':{urllib.parse.quote(path)}:' if path else '')

    @staticmethod
    def assert_name(name) -> bool:
        """判断itemName是否合法"""
        for char in r'\/&|':
            if char in name:
                return False
        return True

    def ls(self, path='') -> dict:
        """列出驱动器文件

        :param path: 驱动器中目录的绝对路径，只能是一个目录的路径。
        :rtype dict 该路径中的文件属性
        """

        url = self.quote_path(path) + '/children'
        return self.request('GET', url).json()

    def mkdir(self, dirname, parent_path='', conflict='fail') -> dict:
        """创建一个目录

        :param parent_path: 父路径
        :param dirname: 新的DirName
        :param conflict: 当dir已经存在时，如何处理？ fail (default) | replace | rename
        :return:
        """
        if not self.assert_name(dirname):
            raise ValueError(f"dirname is error, can not have {self.exception_char}")

        url = self.quote_path(parent_path) + '/children'
        data = {
            "name": dirname,
            "folder": {},
            "@microsoft.graph.conflictBehavior": conflict
        }
        return self.request('POST', url, json=data).json()

    def rm(self, path) -> int:
        """"""
        url = self.quote_path(path)
        return self.request('DELETE', url).status_code

    def rename(self):
        """rename"""

    def mv(self):
        """mv"""

    def cp(self):
        """CP"""

    def upload_stream(self, file_name, parent_path='/', data: bytes = None) -> dict:
        """

        :param file_name:
        :param parent_path: OneDrive Path
        :param data: 数据内容
        :return:
        """
        if not self.assert_name(file_name):
            raise ValueError

        path = PurePosixPath(parent_path).joinpath(file_name).as_posix()

        url = self.quote_path(path) + '/content'
        return self.request('PUT', url, data=data).json()

    def create_upload_session(self,
                              file_name,
                              parent_path='/',
                              conflict='fail',
                              defer_commit=False,
                              description=''
                              ) -> 'OnedriveUploadSession':
        """创建一个上传大文件的Session

        :param file_name: 文件名
        :param parent_path: 父路径
        :param conflict: 冲突处理，fail (default) | replace | rename
        :param defer_commit: 延迟创建，在文件上传完之前，不创建文件。
        :param description: 描述
        """
        url = self.quote_path(parent_path + f'{file_name}') + '/createUploadSession'

        _session = OnedriveUploadSession(self, session_url=url, )
        _session.set_remote_name(name=file_name)
        _session.set_remote_conflict(conflict)
        _session.set_remote_description(description)
        _session.set_remote_defer(defer_commit)

        return _session


class OnedriveUploadSession:
    MS_STEP_LEN = 327680 * 10  # 3MB 左右

    def __init__(self, drive_client: Onedrive, session_url):
        self.onedrive = drive_client
        self.url = session_url
        self.session_body = dict()

        self.session = None
        self._session_created = False
        self._session_success = False

        self.upload_url = None
        self.upload_expiration_time = None
        self.upload_size = 0
        self.reload_data = dict()
        self.reload_times = defaultdict(int)

    def set_remote_conflict(self, conflict):
        """定义远程冲突"""
        if self._session_created:
            raise
        self.session_body['@microsoft.graph.conflictBehavior'] = conflict

    def set_remote_name(self, name):
        """定义远程名字"""
        if self._session_created:
            raise
        if not self.onedrive.assert_name(name):
            raise ValueError
        protocol, base_url, remote_path, ss = self.url.split(':')
        remote_path = urllib.parse.unquote(remote_path)
        self.url = self.onedrive.quote_path(Path(remote_path).with_name(name).as_posix()) + ss
        self.session_body['name'] = name

    def set_remote_defer(self, defer):
        """定义是否需要在全部上传完成后再创建文件"""
        if self._session_created:
            raise
        self.session_body['deferCommit'] = defer

    def set_remote_size(self, size):
        """定于 上传文件的大小"""
        if self._session_created:
            raise
        self.upload_size = size
        self.session_body['fileSize'] = size

    def set_remote_description(self, desc):
        """定义远程描述"""
        if self._session_created:
            raise
        self.session_body['description'] = desc

    def add_reload(self, data, start_range):
        self.reload_data.setdefault(start_range, data)
        self.reload_times[start_range] += 1

    def remove_reload(self, start_range):
        self.reload_data.pop(start_range, None)
        self.reload_times.pop(start_range, None)

    def create_session(self, size=None):
        """"""
        if size:
            self.set_remote_size(size)

        res: requests.Response = self.onedrive.request('POST', self.url, json=self.session_body)

        if res.status_code != 200:
            _j = res.json()
            raise Exception(
                f'code: {res.status_code}\n'
                f'Error: {_j["error"]}'
            )  # TODO

        self._session_created = True
        res: dict = res.json()

        self.upload_url = res.get("uploadUrl")
        self.session = requests.Session()
        self.session.hooks = dict(response=self.verify)

        self.upload_expiration_time = res.get('expirationDateTime')

    def created(self):
        """传输Session已经完成"""
        logger.info('File %s is uploaded Success.', self.session_body.get('name'))

    def verify(self, resp: requests.Response, *args, **kwargs):
        """用于 Request Hooks 的验证方法"""

        ranges = resp.request.headers.get('Content-Range')

        if resp.status_code // 100 != 2:  # 返回非2**时，重载数据
            logger.warning(f'upload Range %s With Error HTTP Status %d',
                           ranges, resp.status_code)
            self.add_reload(resp.request.body, int(ranges.replace('bytes ', '').split('-')[0]))
            resp.upload_status = 'continue'

        elif resp.status_code in [200, 201]:  # 上传完成
            logger.debug('Upload Session Return 200.')
            resp_data: dict = resp.json()

            if resp_data.get('name') == self.session_body['name'] and \
                    resp_data.get('size') == self.session_body['size']:
                self.created()
                logger.debug('Uploaded Range %s', ranges)
                resp.upload_status = 'success'
            else:
                logger.warning('%s Load Fail.', self.session_body.get('name'))
                resp.upload_status = 'fild'

        return resp

    def put_data(self, data: bytes, start_range: int = 0, error_callback=None):
        """Upload Data"""
        len_data = len(data)
        end_range = start_range + len_data - 1
        if len_data < self.MS_STEP_LEN and len_data // self.MS_STEP_LEN != 0:
            raise  # TODO
        if error_callback is None:
            error_callback = self.add_reload

        header = {'Content-Range': f'bytes {start_range}-{end_range}/{self.upload_size}'}
        try:
            return self.session.put(self.upload_url, headers=header, data=data)

        except requests.RequestException as _e:
            logger.warning('Upload Range %d-%d With Network Error as %s', start_range, end_range, _e)
            self.add_reload(data, start_range)

    def cancel(self):
        """取消上传"""
        requests.delete(self.upload_url)
        self.upload_url = None
        self.reload_times = defaultdict(int)
        self.reload_data = dict()

    def reload(self):
        """在允许的重试次数内，重新上载失败的部分。"""
        while True:
            try:
                start_range, data = self.reload_data.popitem()
                if self.reload_times[start_range] > 5:  # TODO Args
                    self.cancel()
                    raise
                self.put_data(data, start_range)
            except KeyError:
                logger.info('Reload all Completed.')
                break

    def from_file(self, file, remote_name=None):
        file = Path(file)
        if not file.is_file():
            raise  # TODO

        size = file.stat().st_size
        if not remote_name or not self.session_body.get('name'):  #
            self.set_remote_name(remote_name)

        self.create_session(size)

        with file.open('rb') as ff:
            start_range = 0
            step = self.MS_STEP_LEN
            while True:
                data = ff.read(step)
                if not data:
                    logger.debug('Break, ')
                    break
                res = self.put_data(data, start_range=start_range)
                start_range += step

        self.reload()

    def from_url(self, url, remote_name=None, **kwargs):
        """从URL上载一个文件"""
        if not remote_name or not self.session_body.get('name'):  #
            self.set_remote_name(remote_name)
        requests.get(url, **kwargs)

    def from_stdin(self, remote_name=None):
        """从标准输入获取数据"""
        if not remote_name or not self.session_body.get('name'):  #
            self.set_remote_name(remote_name)

    def from_qbit(self, ):
        """从QBit获取数据"""


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
    print(o.get_token_from_cache())
    # print(jsonify(o.upload_stream('a.txt', data='s'.encode())))
    session = o.create_upload_session('test.mp4')
    session.from_file('/Users/lcq/Downloads/1_1_48ed6325509e3d97c2b6eed7eabd821dc61c7518.mp4')
    session
