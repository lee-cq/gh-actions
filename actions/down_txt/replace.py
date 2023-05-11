#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : replace.py
@Author     : LeeCQ
@Date-Time  : 2023/5/11 13:05
"""
import re

REMOVE_TEXT = r"""
《一周只更新一章，绝大部分时间写仙剑之星月神话，同时抽点时间续写斗破小天地，说真的，写了也白写，你们觉得精彩的话，等隔段时间请你们帮忙多加收藏仙剑之星月神话吧，恩，写仙剑去了。》
【.*?换源App.*?】
<br/*>
br>
"""

REPLACE_DICT = {
    'se': '色', 'xian': '现', 'xiao': '小', 'xue': '雪', 'xun': '寻', 'xuan': '玄', 'yan': '眼'
}


def replace(s: str):

    # remove
    s = re.sub(r'\n+', '\n', s)
    for line in REMOVE_TEXT.split('\n'):
        s = re.sub(line, '', s)

    # replace
    for k, v in REPLACE_DICT.items():
        s = re.sub(k, v, s)
    return s
