#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : main.py.py
@Author     : LeeCQ
@Date-Time  : 2023/5/29 21:04
"""
import logging
from pathlib import Path

from dotenv import load_dotenv

from down_book import down_txt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

load_dotenv(Path(__file__).parent / '.env')
down_txt('https://www.biququ.info/html/4593/')
