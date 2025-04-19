from models.config import Config
from typing import Tuple, Any


class Collector:
    def __init__(self, config: Config, logger, storage, crawler, parser, filter):
        """初始化收集器
        
        Args:
            config: 配置对象
            logger: 日志记录器
            storage: 存储类
            crawler: 爬虫类
            parser: 解析器类
            filter: 过滤器类
        """
        self.config = config
        self.logger = logger
        self.storage = storage(self.config, logger)
        self.crawler = crawler(self.config, parser, logger)
        self.filter = filter(self.config, logger)
        self.filter.init_db()

    def _process_movie(self, movie_info: Any, file_link: str) -> bool:
        """处理单个电影信息
        
        Args:
            movie_info: 电影信息对象
            file_link: 文件链接
            
        Returns:
            bool: 处理是否成功
        """
        try:
            folder_name = self.config.folder_rename_pattern.format(**movie_info.__dict__)
            file_name = self.config.file_rename_pattern.format(**movie_info.__dict__)
            
            # 创建文件夹并保存文件
            folder_id = self.storage.create_folder(folder_name)
            file_ext, file_id = self.storage.save(folder_id, file_name, file_link)
            
            # 等待保存完成并重命名
            self.storage.wait_until_save_complete(file_name, folder_id)
            self.storage.rename(f"{file_name}.{file_ext}", folder_id, file_id)
            
            # 记录已保存的电影
            account_type, account_id = self.storage.get_current_account_info()
            self.filter.record(movie_info, account_type, account_id)
            
            self.logger.info(f"成功保存 {movie_info}")
            return True
        except Exception as e:
            self.logger.error(f"处理电影 {movie_info} 时出错: {e}")
            return False

    def collect(self, num: Tuple[int, int]) -> Config:
        """收集电影信息并保存
        
        Args:
            num: 页码范围元组 (start, end)
            
        Returns:
            Config: 配置对象
        """
        processed_count = 0
        skipped_count = 0
        error_count = 0
        
        try:
            # 从爬虫获取电影信息
            for movie_info, file_link in self.crawler.crawl(num):
                # 检查是否已存在
                if self.filter.filter(movie_info):
                    self.logger.info(f"跳过已存在的电影: {movie_info}")
                    skipped_count += 1
                    continue
                
                # 处理电影
                if self._process_movie(movie_info, file_link):
                    processed_count += 1
                else:
                    error_count += 1
                    
        except KeyboardInterrupt:
            self.logger.info("用户中断")
        except Exception as e:
            self.logger.error(f"收集过程中发生错误: {e}")
        finally:
            # 关闭资源并输出统计信息
            self.filter.close()
            self.logger.info(f"处理完成: 成功 {processed_count}, 跳过 {skipped_count}, 失败 {error_count}")
            return self.config

