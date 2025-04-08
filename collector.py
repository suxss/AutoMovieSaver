from models.config import Config


class Collector:
    def __init__(self, config: Config, logger, storage, crawler, parser, filter):
        self.config = config
        self.logger = logger
        self.storage = storage(self.config, logger)
        self.crawler = crawler(self.config, parser, logger)
        self.filter = filter(self.config, logger)
        self.filter.init_db()

    def collect(self, num):
        try:
            for movie_info, file_link in self.crawler.crawl(num):
                if self.filter.filter(movie_info):
                    continue
                try:
                    folder_name = self.config.folder_rename_pattern.format(**movie_info.__dict__)
                    file_name = self.config.file_rename_pattern.format(**movie_info.__dict__)
                    folder_id = self.storage.create_folder(folder_name)
                    file_ext, file_id = self.storage.save(folder_id, file_name, file_link)
                    self.storage.wait_until_save_complete(file_name, folder_id)
                    self.storage.rename(f"{file_name}.{file_ext}", folder_id, file_id)
                    account_type, account_id = self.storage.get_current_account_info()
                    self.filter.record(movie_info, account_type, account_id)
                    self.logger.log(f"成功保存 {movie_info}", log_type="info")
                except Exception as e:
                    self.logger.log(e, "error")
        except KeyboardInterrupt:
            self.logger.log("用户中断", "error")
        except Exception as e:
            self.logger.log(e, "error")
        finally:
            self.filter.close()
            return self.config

