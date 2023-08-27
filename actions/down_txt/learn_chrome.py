#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : learn_chrome.py
@Author     : LeeCQ
@Date-Time  : 2023/5/7 21:25
"""

import logging
import threading
import time
import asyncio

from selenium.common import NoSuchWindowException, NoSuchElementException
from selenium.webdriver.common.by import By

from chrome import chrome

logger = logging.getLogger("gh-actions.down-txt.sql")


class Learn:

    def __init__(self):
        self.browser = chrome(use_js=False,
                              # pic=False,
                              # notification=False,
                              # is_headless=True
                              )

    def new_tab(self):
        def _open_tab(_urls):
            for url in _urls:
                # url = url[0]
                if len(self.browser.window_handles) >= 10 + 1:
                    time.sleep(1)
                    continue
                logger.info('Will Open %s' % url)
                self.browser.switch_to.window(self.browser.window_handles[-1])
                a = self.browser.execute_script(f'window.open("{url}","_blank");')

        urls = ['https://qq.com' for _ in range(100)]
        list_window = self.browser.window_handles[0]
        threading.Thread(target=_open_tab, args=(urls,), daemon=True).start()
        time.sleep(2)

        while len(self.browser.window_handles) >= 1:
            for i in self.browser.window_handles:
                if i == list_window:
                    continue

                try:
                    _body = '\n'.join(i.text for i in self.browser.find_elements(By.CSS_SELECTOR,
                                                                                 'body > div.global > div:nth-child(7) > div.col.col-2.fl > div > div.title.nst'))
                    _url = self.browser.current_url
                    _title = self.browser.title
                    self.browser.close()
                except (NoSuchWindowException, NoSuchElementException):
                    continue

                if _body:
                    logger.info(f'获取正文成功：{_title} 长度：{len(_body)}')
                else:
                    logger.error(f'获取正文失败：{_title}')
                    continue

                print(_body)
        logger.info('Done.')

    async def open_tab(self, _urls):
        for i, url in enumerate(_urls):
            # url = url[0]
            if len(self.browser.window_handles) >= 9 + 1:
                logger.debug('sleep 0.1')
                await asyncio.sleep(0.1)
                continue
            logger.info('Will Open %03d %s' % (i, url))
            self.browser.switch_to.window(self.browser.window_handles[-1])
            self.browser.execute_script(f'window.open("{url}","_blank");')

    async def get_body(self):
        list_window = self.browser.window_handles[0]

        while len(self.browser.window_handles) >= 2:
            for i in self.browser.window_handles:
                logger.debug('await 切换')
                await asyncio.sleep(0.001)
                if i == list_window:
                    continue
                try:
                    self.browser.switch_to.window(i)
                    _body = '\n'.join(i.text for i in self.browser.find_elements(
                        By.CSS_SELECTOR,
                        'body > div.global > div:nth-child(7) > div.col.col-2.fl > div > div.title.nst'))
                    _title = self.browser.title
                    self.browser.close()
                except (NoSuchWindowException, NoSuchElementException) as e:
                    logger.info(f'EE: {e}')
                    continue

                if _body:
                    logger.info(f'获取正文成功：{_title} 长度：{len(_body)}')
                else:
                    logger.error(f'获取正文失败：{_title}')
                    continue

                print(_body)
        logger.info('Done.')

    async def main(self):
        task1 = asyncio.create_task(
            self.open_tab(['https://qq.com' for _ in range(100)])
        )

        task2 = asyncio.create_task(
            self.get_body()
        )
        await task1
        await task2


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(module)s - %(levelname)s - %(message)s'
                        )
    _l = Learn()
    asyncio.run(_l.main())
