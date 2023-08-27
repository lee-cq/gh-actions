#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
@File Name  : config.py.py
@Author     : LeeCQ
@Date-Time  : 2023/7/1 13:01
"""
import logging
from dataclasses import dataclass


@dataclass
class BookCss:
    BOOK_NAME: str
    BOOK_AUTHOR: str
    BOOK_LIST: str
    BOOK_CONTENT: str
    BOOK_LIST_NEXT: str = None
    BOOK_CONTENT_NEXT: str = None


CSS_CONFIG = {
    "www.biququ.la": {
        "BOOK_NAME": "#info > h1",
        "BOOK_AUTHOR": "#info > p:nth-child(2)",
        "BOOK_LIST": "#list > dl > dd > a",
        "BOOK_CONTENT": "#content",
    },
    "qushu.org": {
        "BOOK_NAME": "body > div.container.autoheight > div.list-chapter > h1 > a",
        "BOOK_AUTHOR": "body > div.container.autoheight > div.list-chapter > h2 > a:nth-child(2)",
        "BOOK_LIST": "body > div.container.autoheight > div.list-chapter > div.booklist > ul > li > a",
        "BOOK_LIST_NEXT": "body > div.container.autoheight > div.list-chapter > div.booklist > div:nth-child(2) > span.right > a",
        "BOOK_CONTENT": "#chaptercontent",
        "BOOK_CONTENT_NEXT": "#chaptercontent > p > a",
    }
}


def css_finder(domain: str) -> BookCss:
    return BookCss(**CSS_CONFIG.get(domain))


LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
    },
    # "filters": {},
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "simple",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "simple",
            "filename": "down_book.log",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
            "encoding": "utf-8"
        },

    },
    "loggers": {
        "gh-actions": {
            "level": "DEBUG",
            "handlers": ["console"],
            "propagate": False,
        },
    },
    "root": {
        "level": "DEBUG",
        "handlers": ["file"],
    },

}
