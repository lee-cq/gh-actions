#!/bin/env python3
# coding: utf8
"""从日志中发现恶意IP时, 更新JumpServer的黑名单.

get https://JumpServer/api/v1/settings/setting/?category=security  获取当前配置
patch https://JumpServer/api/v1/settings/setting/?category=security 更新当前配置

get https://JumpServer/api/v1/audits/login-logs/?date_from=DATA&date_to=DATA&offset=0&limit=100&display=1&draw=1 获取审计日志

"""

import logging
import requests
import json
import os
import datetime
from collections import defaultdict

HOST=os.getenv()
PTOKEN=os.getenv()

AUTH_HEADER = {
    'Authorization': f'Token {PTOKEN}',
    'X-JMS-ORG': '00000000-0000-0000-0000-000000000002'
}


def get_malicious_ips():
    """从审计日志中得到恶意的IP地址,
    获取上一天0点值今天0点的值。
    """
    url = HOST + '/api/v1/audits/login-logs/'
    today = datetime.datetime.now().date()
    last_day = today - datetime.timedelta(days=1)
    args = {
      'date_from': last_day.strftime('%Y-%m-%dT00:00:00.000Z'),
      'date_to': today.strftime('%Y-%m-%dT00:00:00.000Z'),
      'limit': -1,
      'status': 0
    }
    j = requests.get(url, params=args, headers=AUTH_HEADER)
    if j.status_code !=200:
        raise requests.exceptions.HTTPError()
    error_times = defaultdict(int)
    
    for i in j:
        error_times[i["ip"]] += 1
    
    return [k for k,v in error_times.items() if v >5]



      
