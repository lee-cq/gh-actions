#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : down_book.py
@Author     : LeeCQ
@Date-Time  : 2023/5/7 19:15
"""
import json
import logging
import os
import sys
import time
from pathlib import Path

from selenium.webdriver.common.by import By
from sqllib import MySqlAPI, SQLiteAPI, BaseSQLAPI

from chrome import chrome
from replace import replace

logger = logging.getLogger("gh-actions.down-txt")


class DownTxt:
    sql: BaseSQLAPI = None
    book_name: str = None

    def __init__(self, url, _sql=None):
        self.url = url
        self.browser = chrome(use_js=False, pic=False, notification=False)
        self.set_sql(_sql)

    def set_sql(self, _sql: BaseSQLAPI = None):
        if _sql:
            self.sql = _sql
            return
        self.sql = SQLiteAPI('cache/down_txt.db')

    def create_table(self):
        """创建数据库"""
        if not self.book_name:
            raise Exception('请先获取书籍名称')
        _c = (f"CREATE TABLE IF NOT EXISTS `{self.book_name}` ( "
              f"idd     INT(10)     NOT NULL    UNIQUE, "
              f"url     VARCHAR(50)     NOT NULL    UNIQUE, "
              f"title   VARCHAR(99), "
              f"body    VARCHAR(16000)"
              f" ) ")
        return self.sql.write_db(_c)

    def create_metadata(self):
        """获取URL头"""
        self.browser.get(self.url)
        self.browser.implicitly_wait(10)
        title = self.browser.find_element(By.CSS_SELECTOR, '#info > h1').text
        author = self.browser.find_element(By.CSS_SELECTOR, '#info > p:nth-child(2)').text.replace('作  者：', '')
        self.book_name = f"{author}-{title}-{time.strftime('%Y%m', time.localtime())}"
        self.create_table()
        logger.info('Book Name: %s' % title)
        idd_s = [x[0] for x in self.sql.read_db(f"SELECT idd FROM `{self.book_name}`")]
        for i in self.browser.find_elements(By.CSS_SELECTOR, '#list > dl > dd > a'):
            _url = i.get_attribute('href')
            _id = _url.split('/')[-1].split('.')[0]
            _name = i.text
            if int(_id) in idd_s:
                continue
            logger.info(f'创建元数据章节：{_name}, {_url}')
            self.sql.write_db(f"INSERT INTO `{self.book_name}` (idd, url, title) VALUES ('{_id}', '{_url}', '{_name}')")

    def write_body(self):
        for idd, url in self.sql.read_db(f"SELECT idd, url FROM `{self.book_name}` WHERE body IS NULL"):
            self.sql.write_db(f"UPDATE `{self.book_name}` SET body='{self.get_body(url)}' WHERE idd='{idd}'")

    def get_body(self, url):
        """获取正文"""
        logger.info(f'获取正文：{url}')
        self.browser.get(url)
        self.browser.implicitly_wait(10)
        _body = '\n'.join(i.text for i in self.browser.find_elements(By.CSS_SELECTOR, '#content > p'))
        if _body:
            _body = replace(_body)
            _body = _body.replace('<br>', '\n').replace('\r', '')
            logger.info(f'获取正文成功：{self.browser.title} 长度：{len(_body)}')

        else:
            logger.error(f'获取正文失败：{url}')
        return _body

    @property
    def save_path(self) -> Path:
        return Path() / 'cache' / f'{self.book_name}.txt'

    # 合并为txt
    def merge_txt(self):
        """合并为txt"""
        logger.info('合并为txt')
        _body = '\n\n'.join(f'{t}\n{b}' for t, b in self.sql.read_db(f"SELECT title, body FROM `{self.book_name}`"))
        self.save_path.write_text(_body, encoding='gb18030')
        logger.info('合并为txt完成')

    def github_env(self):
        if os.getenv('GITHUB_ENV'):
            logger.info('写入环境变量到 GITHUB_ENV')
            with open(os.getenv('GITHUB_ENV'), 'a', encoding='utf-8') as f:
                f.write(f"BOOK_NAME={self.book_name}.txt\n")
                f.write(f"BOOK_PATH={self.save_path.absolute()}\n")
        else:
            logger.warning('未配置 GITHUB_ENV')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    DOWNLOAD_LINK = os.getenv('DOWNLOAD_LINK')
    DOWNLOAD_NAME = os.getenv('DOWNLOAD_NAME', '')
    try:
        mysql_info = json.loads(os.getenv('MYSQL_INFO'))
        sql = MySqlAPI(
            **mysql_info,
            charset='gb18030',
        )
        logger.info('使用mysql, Host: %s' % mysql_info['host'])
    except Exception as e:
        logger.warning('未配置数据库，使用sqlite')
        sql = None

    a = DownTxt(DOWNLOAD_LINK)
    a.set_sql(_sql=sql)
    a.create_metadata()
    a.write_body()
    a.merge_txt()
    a.github_env()
