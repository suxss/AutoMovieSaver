import logging

import colorlog

from models.logger import Logger


def get_logger(level=logging.INFO):
    # 创建logger对象
    logger = logging.getLogger()
    logger.setLevel(level)
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
        }
    )
    # 将颜色输出格式添加到控制台日志处理器
    console_handler.setFormatter(color_formatter)
    # 移除默认的handler
    for handler in logger.handlers:
        logger.removeHandler(handler)
    # 将控制台日志处理器添加到logger对象
    logger.addHandler(console_handler)
    return logger

class LogModule(Logger):
    def __init__(self, level):
        self.level = level

    @classmethod
    def logger(cls):
        return get_logger(logging.INFO)

    @classmethod
    def log(cls, message, log_type):
        if log_type == "info":
            LogModule.logger().info(message)
        elif log_type == "debug":
            LogModule.logger().debug(message)
        elif log_type == "warning":
            LogModule.logger().warning(message)
        elif log_type == "error":
            LogModule.logger().error(message)