#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : chrome.py
@Author     : LeeCQ
@Date-Time  : 2023/5/11 14:55
"""
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver.chrome.service import Service

__all__ = ['chrome']


def chrome(executable_path='chromedriver',
           window_sizes: tuple = None,
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
    :param window_sizes: 窗口大小
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

    __service = Service(executable_path=executable_path

                        )

    browser = Chrome(service=__service,
                     options=__opt,
                     )
    if window_sizes:
        browser.set_window_size(*window_sizes)
    return browser


def _option(headless, maximized, incognito, js, ua, pic, notifications, **kwargs):
    option = ChromeOptions()
    # 设置
    _pre = dict()

    if headless is True:
        option.add_argument('--headless')  # 隐藏窗口
    if maximized is True:
        option.add_argument('--start-maximized')  # 最大化
    if incognito is True:
        option.add_argument('–-incognito')  # 基本没什么用
    if ua:
        option.add_argument(f'user-agent={ua}')  # 设置UA
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
    option.add_experimental_option('excludeSwitches', ['enable-automation'])
    option.add_argument("--disable-blink-features=AutomationControlled")  # 这里添加一些启动的参数
    return option
