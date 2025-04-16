import logging
import os
from typing import Optional, Dict, Union, Literal

import colorlog

from models.logger import Logger


def get_logger(level: int = logging.INFO, name: str = "") -> logging.Logger:
    """获取配置好的日志记录器
    
    Args:
        level: 日志级别，默认为INFO
        name: 日志记录器名称，默认为空字符串（根记录器）
        
    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建logger对象
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 如果已经有处理器，则不重复添加
    if logger.handlers:
        return logger
    
    # 创建控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    
    # 定义颜色输出格式
    color_formatter = colorlog.ColoredFormatter(
        '%(log_color)s%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'red,bg_white',
        },
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 将颜色输出格式添加到控制台日志处理器
    console_handler.setFormatter(color_formatter)
    
    # 添加控制台处理器到logger
    logger.addHandler(console_handler)
    
    # 设置不向上层logger传播
    logger.propagate = False
    
    return logger


def setup_file_logger(logger: logging.Logger, log_file: str, 
                      level: int = logging.INFO) -> logging.Logger:
    """为给定的日志记录器添加文件处理器
    
    Args:
        logger: 已有的日志记录器
        log_file: 日志文件路径
        level: 文件日志级别，默认为INFO
        
    Returns:
        logging.Logger: 添加了文件处理器的日志记录器
    """
    # 确保日志目录存在
    os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    
    # 设置格式
    formatter = logging.Formatter(
        '%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    
    # 添加到logger
    logger.addHandler(file_handler)
    
    return logger


class LogModule(Logger):
    """日志模块实现类"""
    
    def __init__(self, level: int = logging.INFO):
        """初始化日志模块
        
        Args:
            level: 日志级别，默认为INFO
        """
        self.level = level
        self._logger = None

    @property
    def logger(self) -> logging.Logger:
        """获取日志记录器
        
        Returns:
            logging.Logger: 日志记录器
        """
        if self._logger is None:
            self._logger = get_logger(self.level)
        return self._logger

    def log(self, message: str, 
            log_type: Literal["debug", "info", "warning", "error", "critical"] = "info") -> None:
        """记录日志
        
        Args:
            message: 日志消息
            log_type: 日志类型，可选值：debug, info, warning, error, critical
        """
        if log_type == "debug":
            self.logger.debug(message)
        elif log_type == "info":
            self.logger.info(message)
        elif log_type == "warning":
            self.logger.warning(message)
        elif log_type == "error":
            self.logger.error(message)
        elif log_type == "critical":
            self.logger.critical(message)