#!/bin/env python3
"""
从环境变量: DOWNLOAD_BODY 中得到请求体并设置解析。

输入： 
env.DOWNLOAD_BODY

输出：
env.DOWNLOAD_LINK
env.DOWNLOAD_NAME
env.DOWNLOAD_TYPE

"""

import os
import re
from pathlib import Path
from urllib.parse import urlparse


body = os.getenv('DOWNLOAD_BODY')
github_env = os.getenv('GITHUB_ENV')

SUPPORT_PROTOCOLS = ('http://', 'https://', )
SUPPORT_DOWNTYPES = ('defualt', 'm3u8')

DOWNLOAD_LINK = None
DOWNLOAD_NAME = None
DOWNLOAD_TYPE = None

for line in body.splitlines():
    line: str
    for sup in SUPPORT_PROTOCOLS:
        if sup in line:
            DOWNLOAD_LINK = sup + line.split(sup)[-1]
            break
    
    for type_ in SUPPORT_DOWNTYPES:
        if 'type:' in line and type_ in line:
            DOWNLOAD_TYPE = type_
            break

    for protocol in SUPPORT_DOWNTYPES:  
        if 'name:' in line and protocol not in line:
            DOWNLOAD_NAME=line.split('name:')[-1].strip(' ', '').strip('\n', '')

if DOWNLOAD_LINK is None:
    exit(1)

if DOWNLOAD_TYPE is None:
    DOWNLOAD_TYPE = SUPPORT_DOWNTYPES[0]

if DOWNLOAD_NAME is None:
    DOWNLOAD_NAME = urlparse(DOWNLOAD_LINK).path().split('/')[-1]
        


with Path(github_env).open('a', encoding='utf8') as ff:
    if DOWNLOAD_LINK:
        ff.write(f'\n{DOWNLOAD_LINK=}')
    if DOWNLOAD_NAME:
        ff.write(f'\n{DOWNLOAD_NAME=}')
    if DOWNLOAD_TYPE:
        ff.write(f'\n{DOWNLOAD_TYPE=}')

print('Done. ')

    

