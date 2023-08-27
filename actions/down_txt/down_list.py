#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : down_list.py
@Author     : LeeCQ
@Date-Time  : 2023/5/12 20:26
"""

import logging
from multiprocessing import Pool
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

from down_book import down_txt

__all__ = ['down_list']

logger = logging.getLogger('gh-actions.down-txt.down-list')

辰东 = ['https://www.biququ.info/html/48260', 'https://www.biququ.info/html/27746', 'https://www.biququ.info/html/4234',
        'https://www.biququ.info/html/27743', 'https://www.biququ.info/html/36094', 'https://www.biququ.info/html/27765',
        'https://www.biququ.info/html/27937']
忘语 = ['https://www.biququ.info/html/1756', 'https://www.biququ.info/html/81678', 'https://www.biququ.info/html/35912',
        'https://www.biququ.info/html/28936', 'https://www.biququ.info/html/44573', 'https://www.biququ.info/html/8245']
风凌天下 = ['https://www.biququ.info/html/57569', 'https://www.biququ.info/html/32877', 'https://www.biququ.info/html/9814',
            'https://www.biququ.info/html/27794', 'https://www.biququ.info/html/36606', 'https://www.biququ.info/html/6770']


def multi_thread_down():
    """下载列表"""
    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(down_txt, 风凌天下)


def multi_process_down():
    """下载列表"""
    with Pool(5) as p:
        p.map(down_txt, 风凌天下)


if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    load_dotenv(Path(__file__).parent / '.env')

    multi_thread_down()
