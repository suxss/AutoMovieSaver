import logging
import os
import sys
from pathlib import Path
from typing import List

import toml
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger

from collector import Collector
from logger import get_logger
from models.config import Config, AccountInfo, DBInfo


def load_config(config_path: str) -> Config:
    """加载配置文件
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        Config: 配置对象
        
    Raises:
        FileNotFoundError: 配置文件不存在
        ValueError: 配置文件格式错误
    """
    try:
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
        with open(config_path, 'r', encoding='utf-8') as toml_file:
            config_dict = toml.load(toml_file)
        
        # 转换账户信息
        accounts = []
        for account in config_dict.get("accounts", []):
            accounts.append(AccountInfo(
                username=account.get("username", ""),
                password=account.get("password", ""),
                root_folder=account.get("root_folder", "")
            ))
        
        # 转换数据库信息
        db_info = DBInfo(
            username=config_dict.get("db_info", {}).get("username", ""),
            password=config_dict.get("db_info", {}).get("password", ""),
            database=config_dict.get("db_info", {}).get("database", "")
        )
        
        # 创建Config对象
        return Config(
            accounts=accounts,
            folder_rename_pattern=config_dict.get("folder_rename_pattern", ""),
            file_rename_pattern=config_dict.get("file_rename_pattern", ""),
            api_url=config_dict.get("api_url", ""),
            model=config_dict.get("model", ""),
            token=config_dict.get("token", ""),
            cron=config_dict.get("cron", ""),
            db_info=db_info
        )
    except toml.TomlDecodeError as e:
        raise ValueError(f"配置文件格式错误: {e}")


def save_config(config: Config, config_path: str) -> None:
    """保存配置到文件
    
    Args:
        config: 配置对象
        config_path: 配置文件路径
    """
    # 确保目录存在
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    
    # 转换Config对象为字典
    config_dict = {
        "folder_rename_pattern": config.folder_rename_pattern,
        "file_rename_pattern": config.file_rename_pattern,
        "api_url": config.api_url,
        "model": config.model,
        "token": config.token,
        "cron": config.cron,
        "accounts": [
            {
                "username": account.username,
                "password": account.password,
                "root_folder": account.root_folder
            } for account in config.accounts
        ],
        "db_info": {
            "username": config.db_info.username,
            "password": config.db_info.password,
            "database": config.db_info.database
        }
    }
    
    with open(config_path, 'w', encoding='utf-8') as toml_file:
        toml.dump(config_dict, toml_file)


def run_collector(config_path: str, log_level: int) -> None:
    """运行收集器
    
    Args:
        config_path: 配置文件路径
        log_level: 日志等级
    """
    try:
        from crawlers.leijing import LeiJing
        from filters.sqlite import SQLiteFilter
        from parsers.openai import OpenAIParser
        from storages.cloud189 import Cloud189Storage
        
        # 加载配置
        config = load_config(config_path)
        logger = get_logger(level=log_level)
        
        # 初始化收集器
        collector = Collector(config, logger, Cloud189Storage, LeiJing, OpenAIParser, SQLiteFilter)
        
        # 运行收集过程
        logger.info("开始收集电影信息...")
        new_config = collector.collect((1, 10))
        
        # 保存更新后的配置
        save_config(new_config, config_path)
        logger.info("电影收集完成，配置已更新")
        
    except Exception as e:
        logger = get_logger(level=logging.ERROR)
        logger.error(f"运行过程中发生错误: {e}")
        sys.exit(1)


def main(config_path: str = "data/config.toml", log_level: int = logging.INFO):
    """主程序入口"""
    
    try:
        # 加载配置
        config = load_config(config_path)
        
        # 设置调度器
        scheduler = BlockingScheduler()
        
        if config.cron:
            # 添加定时任务
            scheduler.add_job(
                lambda: run_collector(config_path), 
                trigger=CronTrigger.from_crontab(config.cron)
            )
            print(f"定时任务已设置: {config.cron}", flush=True)
            # 启动调度器
            scheduler.start()
        else:
            # 直接运行
            print("没有设置定时任务, 将直接运行", flush=True)
            run_collector(config_path, log_level)
            
    except KeyboardInterrupt:
        print("程序被用户中断", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"程序初始化失败: {e}", flush=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
