#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : se.py
@Author     : LeeCQ
@Date-Time  : 2023/5/7 19:15
"""

import logging
import sys

from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.common.by import By
from sqllib import SQLiteAPI, BaseSQLAPI

logger = logging.getLogger("gh-actions.down-txt")


def chrome(executable_path='chromedriver.exe',
           is_headless: bool = False, headless=None,
           is_maximized: bool = False, maximized=None,
           is_incognito: bool = False, incognito=None,
           use_js: bool = True, js: bool = None,
           custom_ua: str = None, ua: str = None,
           display_pic: bool = True, pic=True,
           display_notifications: bool = True, notification=None,
           **kwargs
           ):
    """参数说明：

    :param ua:
    :param js:
    :param maximized: 窗口最大化
    :param notification: 通知
    :param pic: 显示图片
    :param headless: 最小化
    :param incognito: 影身
    :param executable_path: chromedriver可执行程序的位置。
    :param is_headless: 隐藏窗口
    :param is_maximized: 窗口最大化
    :param is_incognito: 使用无痕模式
    :param use_js: 是否使用JS
    :param custom_ua: 使用给定的浏览器UA
    :param display_pic: 是否加载图片
    :param display_notifications: 是否加载弹窗
    """
    is_headless = is_headless if headless is None else headless
    is_maximized = is_maximized if maximized is None else maximized
    is_incognito = is_incognito if incognito is None else incognito
    custom_ua = custom_ua if ua is None else ua
    use_js = use_js if js is None else js
    display_pic = display_pic if pic is None else pic
    display_notifications = display_notifications if notification else notification

    __opt = _option(headless=is_headless,
                    maximized=is_maximized,
                    js=use_js, ua=custom_ua,
                    incognito=is_incognito,
                    pic=display_pic,
                    notifications=display_notifications, **kwargs
                    )
    browser = Chrome(executable_path=executable_path,
                     options=__opt
                     )
    return browser


def _option(headless, maximized, incognito, js, ua, pic, notifications, **kwargs):
    option = ChromeOptions()
    # 设置
    _pre = dict()

    option.headless = headless
    if maximized is True:
        option.add_argument('--start-maximized')  # 最大化
    if incognito is True:
        option.add_argument('–-incognito')  # 基本没什么用
    if ua:
        option.add_argument(f'user-agent="{ua}"')  # 设置UA
    if js is False:
        _pre.update({'javascript': 2})  # 设置JS
    if pic is False:
        _pre.update({'images': 2})  # 设置pic
    if notifications is False:
        _pre.update({'notifications': 2})  # 设置通知
    # 可拓展
    if 'argument' in kwargs.keys():
        option.add_argument(kwargs.get('argument') if isinstance(kwargs.get('argument'), str) else '')
    if 'arguments' in kwargs.keys():
        for _ in kwargs.get('arguments') if isinstance(kwargs.get('arguments'), str) else []:
            option.add_argument(_ if isinstance(_, str) else '')

    option.add_experimental_option('prefs', {'profile.default_content_setting_values': _pre})
    return option


class DownTxt:
    sql: BaseSQLAPI = None
    book_name: str = None

    def __init__(self, url, sql=None):
        self.url = url
        self.browser = chrome(use_js=False, pic=False, notification=False)
        self.set_sql(sql)

    def set_sql(self, *args, **kwargs):
        # self.sql = MySqlAPI(*args, **kwargs)
        self.sql = SQLiteAPI('down_txt.db', **kwargs)

    def create_table(self, table_name):
        """创建数据库"""
        _c = (f"CREATE TABLE IF NOT EXISTS `{table_name}` ( "
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
        title = self.browser.find_element(By.TAG_NAME, 'title').text
        self.create_table(title)
        self.book_name = title
        logger.info('Book Name: %s' % title)
        for i in self.browser.find_elements(By.CSS_SELECTOR, '#list > dl > dd > a'):
            _url = i.get_attribute('href')
            _id = _url.split('/')[-1].split('.')[0]
            _name = i.text
            logger.info(f'创建元数据章节：{_name}, {_url}')
            self.sql.write_db(f"INSERT INTO `{title}` (idd, url, title) VALUES ('{_id}', '{_url}', '{_name}')")

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
            _body = _body.replace('<br>', '\n').replace('\r', '')
            logger.info(f'获取正文成功：{self.browser.title} 长度：{len(_body)}')
        else:
            logger.error(f'获取正文失败：{url}')
        return _body

    # 合并为txt
    def merge_txt(self, save_name=None):
        """合并为txt"""
        logger.info('合并为txt')
        _body = '\n\n'.join(f'{t}\n{b}' for t, b in self.sql.read_db(f"SELECT title, body FROM `{self.book_name}`"))
        with open(f'{save_name or self.book_name}.txt', 'w', encoding='gb18030') as f:
            f.write(_body)
        logger.info('合并为txt完成')


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    a = DownTxt('https://www.biququ.info/html/3486/')
    a.set_sql()
    # a.create_metadata()
    a.book_name = ''
    # a.write_body()
    a.merge_txt('大主宰')