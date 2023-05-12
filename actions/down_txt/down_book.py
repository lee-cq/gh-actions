#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : down_book.py
@Author     : LeeCQ
@Date-Time  : 2023/5/7 19:15
"""
import asyncio
import json
import logging
import os
import sys
import threading
import time
from pathlib import Path
from queue import Queue, Empty

from dotenv import load_dotenv
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchWindowException, NoSuchElementException
from sqllib import MySqlAPI, SQLiteAPI, BaseSQLAPI

from chrome import chrome
from replace import replace, replace_from_sql

logger = logging.getLogger("gh-actions.down-txt")


class DownTxt:
    sql: BaseSQLAPI = None
    book_name: str = None

    def __init__(self, url, _sql=None):
        self.url = url
        logger.info('Download URL: %s' % url)
        self.browser = chrome(
            use_js=False,
            pic=False,
            notification=False,
            # is_headless=True,
            ua='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36 Edg/113.0.1774.35'
        )
        self.set_sql(_sql)
        self.body_queue = Queue()
        self.have_new_tab = True
        self.have_new_body = True

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

    def verify_bot(self):
        """验证机器人"""
        logger.info('验证机器人')
        self.browser.implicitly_wait(10)
        while True:
            if self.browser.title != 'Just a moment...':
                break
            time.sleep(1)
        logger.info('验证完成')

    # noinspection PyProtectedMember
    def create_metadata(self):
        """获取URL头"""
        self.browser.get(self.url)
        self.browser.implicitly_wait(10)
        if self.browser.title == 'Just a moment...':
            logger.warning('需要验证')
            self.verify_bot()
        self.book_name = f"{self.browser.find_element(By.CSS_SELECTOR, '#info > p:nth-child(2)').text.replace('作  者：', '')}-" \
                         f"{self.browser.find_element(By.CSS_SELECTOR, '#info > h1').text}-" \
                         f"{time.strftime('%Y%m', time.localtime())}"
        self.create_table()
        logger.info('Book Name: %s' % self.book_name)

        idd_s = [x[0] for x in self.sql.read_db(f"SELECT idd FROM `{self.book_name}`")]
        logger.info('已经写入的章节信息数量: %d' % len(idd_s))

        chs = self.browser.find_elements(By.CSS_SELECTOR, '#list > dl > dd > a')
        logger.info('最新章节数量: %d' % len(chs))

        if len(idd_s) == len(chs):
            logger.info('已经下载完成')
            return

        cursor = self.sql._sql.cursor()

        for i in self.browser.find_elements(By.CSS_SELECTOR, '#list > dl > dd > a'):
            _url = i.get_attribute('href')
            _id = _url.split('/')[-1].split('.')[0]
            _name = i.text
            if int(_id) in idd_s:
                continue
            logger.info(f'创建元数据章节：{_name}, {_url}')
            cursor.execute(f"INSERT INTO `{self.book_name}` (idd, url, title) VALUES ('{_id}', '{_url}', '{_name}')")

        self.sql._sql.commit()

    async def open_tab(self):
        """异步打开标签页"""

        urls = self.sql.read_db(f"SELECT url FROM `{self.book_name}` WHERE body IS NULL")

        if not urls:
            logger.info('全部Body下载完成 ...')
            self.have_new_tab = False
            return

        logger.info('未下载的章节数量: %d' % len(urls))

        for i, url in enumerate(urls):
            url = url[0]
            while len(self.browser.window_handles) >= 5 + 1:
                await asyncio.sleep(0.1)
            logger.info('Will Open %d %s' % (i, url))
            self.browser.switch_to.window(self.browser.window_handles[-1])
            self.browser.execute_script(f'window.open("{url}","_blank");')

        self.body_queue.join()  # 等待列队中的数据全部写入数据库
        await self.open_tab()  # 递归检查是否还有未下载的章节

    async def get_body(self, chapter_window):
        """获取正文

        :return:
        """

        while self.have_new_tab:
            for i in self.browser.window_handles:
                await asyncio.sleep(0.001)

                if i == chapter_window:
                    continue

                try:
                    self.browser.switch_to.window(i)

                    if self.browser.title == 'Just a moment...':
                        logger.warning('需要验证')
                        self.verify_bot()
                        continue

                    _body = '\n'.join(
                        i.text for i in self.browser.find_elements(
                            By.CSS_SELECTOR,
                            '#content > p')
                    )
                    _title = self.browser.title
                    _url = self.browser.current_url
                    self.browser.close()
                except (NoSuchWindowException, NoSuchElementException) as _e:
                    logger.info(f'EE: {type(_e)}')
                    continue

                if _body:
                    self.body_queue.put((_url, _title, replace(_body)))
                    logger.info(f'获取正文成功：{_title} 长度：{len(_body)}')
                else:
                    logger.error(f'获取正文失败：{_title}')
                    continue
        else:
            logger.info('获取正文完成 ...')
            self.have_new_body = False

    def write_body_sql(self):
        """写入正文到数据库"""
        while True:
            try:
                _url, _title, _body = self.body_queue.get(timeout=2)
                self.sql.write_db(f"UPDATE `{self.book_name}` SET body='{_body}' WHERE url='{_url}'")
                self.body_queue.task_done()
                logger.info('写入正文成功：%s' % _title)
            except Empty:
                if self.have_new_body is False:
                    logger.info('数据写入完成 ...')
                    break
                else:
                    logger.warning('等待新数据写入列队 ...')

    def async_write_body(self):
        """"""
        chapter_window = self.browser.window_handles[0]

        async def main():
            await asyncio.gather(
                self.open_tab(),
                self.get_body(chapter_window),
            )

        _w = threading.Thread(target=self.write_body_sql, daemon=True)
        _w.start()
        asyncio.run(main())
        logger.info('Async Loop Done ...')
        _w.join()
        self.browser.quit()

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

    def replace_from_sql(self):
        logger.info('开始清理SQL Body中的广告 ...')
        return replace_from_sql(self.sql, self.book_name)


def down_txt(url):
    a = DownTxt(url)
    a.set_sql(_sql=sql)
    a.create_metadata()
    a.async_write_body()

    if os.getenv('REPLACE_FROM_SQL', False):
        a.replace_from_sql()
    a.merge_txt()
    a.github_env()


def replace_sql(table_name):
    a = DownTxt('')
    a.set_sql(_sql=sql)
    a.book_name = table_name
    a.replace_from_sql()


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    load_dotenv(Path(__file__).parent / '.env')

    DOWNLOAD_LINK = os.getenv('DOWNLOAD_LINK')
    DOWNLOAD_NAME = os.getenv('DOWNLOAD_NAME', '')
    try:
        mysql_info = json.loads(os.getenv('MYSQL_INFO'))
        sql = MySqlAPI(
            **mysql_info,
            charset='gb18030',
            use_unicode=True,
            pool=True,
        )
        logger.info('使用mysql, Host: %s' % mysql_info['host'])
    except Exception as e:
        logger.warning('未配置数据库，使用sqlite')
        sql = None

    if DOWNLOAD_LINK:
        down_txt(DOWNLOAD_LINK)
    else:
        logger.warning('未配置下载链接')
