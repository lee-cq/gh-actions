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

logger = logging.getLogger('actions.jumpserver.upload_blacklist')

HOST=os.getenv('HOST')
PTOKEN=os.getenv('PTOKEN')

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
        logger.error('Get Settings Error %d, \ndata=%s',j.status_code, j.text())
        raise requests.exceptions.HTTPError()
    error_times = defaultdict(int)
    
    for i in j:
        if i['city'] == '深圳':
            continue
        error_times[i["ip"]] += 1
    
    return [k for k,v in error_times.items() if v >5]


def get_settings():
    """获取配置字典
    """
    url = HOST + '/api/v1/settings/setting/?category=security'
    j = requests.get(url, headers=AUTH_HEADERS)
    if j.status_code != 200:
        logger.error('Get Settings Error %d, \ndata=%s',j.status_code, j.text())
        raise requests.exceptions.HTTPError()
    
    return j.json()


def upload_settings(settings):
    """更新配置字典"""
    url = HOST + '/api/v1/settings/setting/?category=security'
    j = requests.patch(url, json=settings,headers=AUTH_HEADERS)
    return j.status_code

def main():
    blacklist = get_malicious_ips()
    settings:list = get_settings()
    old_list:list= settings.get("SECURITY_LOGIN_IP_BLACK_LIST", [])
    new_list = list(set(old_list.extend(settings)))
    settings["SECURITY_LOGIN_IP_BLACK_LIST"] = new_list
    
    resp = upload_settings(settings=settings)
    if resp == 200:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    fmt = logging.Formatter(
        '%(asctime)s  [%(levelname)s] %(msg)s' 
    )
    a = logging.FileHandler(filename='~/jump_update_blacklist.log')
    a.setFormatter(fmt=fmt)
    a.setLevel('DEBUG')
    logger.addHandler(a)

    main()

