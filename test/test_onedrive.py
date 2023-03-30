# coding: utf8
import logging
import os
import time
import unittest

from actions.downloader.onedrive_upload import Onedrive

from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level='DEBUG')

unittest_dirname = 'unittest_dirname'


class TestOnedrive(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        refresh_token = os.getenv('MSAL_ONEDRIVE_TOKEN')
        client_id = os.getenv('MSAL_CLIENT_ID')
        client_sec = os.getenv('MSAL_CLIENT_SECRET')
        onedrive = Onedrive(client_id, client_sec, os.getenv('MSAL_DRIVE_TYPE'), os.getenv('MSAL_DRIVE_ID_TEST'))
        onedrive.load_token(refresh_token)
        if unittest_dirname not in [i.get('name') for i in onedrive.ls().get('value', [])]:
            onedrive.mkdir(unittest_dirname)

        cls.onedrive = onedrive
        cls.unittest_dirname = '/' + unittest_dirname

    @classmethod
    def tearDownClass(cls) -> None:
        cls.onedrive.rm(cls.unittest_dirname)

    def test_ls_root(self):
        """测试ls"""
        items = self.onedrive.ls()
        self.assertNotIn('error', items)
        self.assertIsInstance(items.get('value'), list)

    def test_ls_test_dir(self):
        items = self.onedrive.ls(self.unittest_dirname)
        self.assertNotIn('error', items)
        self.assertIsInstance(items.get('value'), list)

    def test_mkdir(self):
        """创建目录"""
        dirname = f'test_{time.time()}'
        res = self.onedrive.mkdir(dirname, parent_path=self.unittest_dirname)
        self.assertNotIn('error', res)
        self.assertEqual(res.get('name'), dirname)
        return res['name']

    def test_upload_file_small(self):
        """上传小文件"""
        file_name = f'test_file_{time.time()}.txt'
        res = self.onedrive.upload_stream(file_name, parent_path=self.unittest_dirname, data=file_name.encode())
        self.assertNotIn('error', res)
        self.assertEqual(res.get('name'), file_name)
        return res['name']

    def test_rm_file(self):
        name = self.test_upload_file_small()
        res = self.onedrive.rm(self.unittest_dirname + f'/{name}')
        self.assertEqual(res, 204)

    def test_rm_dir(self):
        name = self.test_mkdir()
        res = self.onedrive.rm(self.unittest_dirname + f'/{name}')
        self.assertEqual(res, 204)
