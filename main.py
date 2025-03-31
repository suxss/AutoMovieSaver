import logging

import toml
from box import Box

from collector import Collector
from logger import LogModule

if __name__ == '__main__':
    from crawlers.leijing import LeiJing
    from filters.mysql import MySQLFilter
    from parsers.openai import OpenAIParser
    from storages.cloud189 import Cloud189Storage


    with open('config.toml', 'r') as toml_file:
        config_dict = toml.load(toml_file)

    config = Box(config_dict)
    logger = LogModule(level=logging.INFO)
    collector = Collector(config, logger, Cloud189Storage, LeiJing, OpenAIParser, MySQLFilter)
    collector.collect((1, 10))
