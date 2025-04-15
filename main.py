import logging

import toml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from box import Box

from collector import Collector
from logger import get_logger


def load_config(config_path: str):
    with open(config_path, 'r', encoding='utf-8') as toml_file:
        config_dict = toml.load(toml_file)

    return Box(config_dict)


def save_config(config, config_path: str):
    with open(config_path, 'w', encoding='utf-8') as toml_file:
        toml.dump(config.to_dict(), toml_file)



if __name__ == '__main__':
    from crawlers.leijing import LeiJing
    from filters.sqlite import SQLiteFilter
    from parsers.openai import OpenAIParser
    from storages.cloud189 import Cloud189Storage


    config_path = "data/config.toml"
    config = load_config(config_path)

    def run():
        config_path = "data/config.toml"
        config = load_config(config_path)
        logger = get_logger(level=logging.INFO)
        collector = Collector(config, logger, Cloud189Storage, LeiJing, OpenAIParser, SQLiteFilter)
        new_config = collector.collect((1, 10))
        save_config(new_config, config_path)


    scheduler = BlockingScheduler()
    if config.cron:
        scheduler.add_job(run, trigger=CronTrigger.from_crontab(config.cron))
        print("定时任务已设置", flush=True)
    else:
        print("没有设置定时任务, 将直接运行", flush=True)
        run()
    scheduler.start()
