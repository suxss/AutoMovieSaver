from models.config import Config


class Collector:
    def __init__(self, config: Config, logger, storage, crawler, parser, filter):
        self.config = config
        self.logger = logger
        self.storage = storage(config, logger)
        self.crawler = crawler(config, parser, logger)
        self.filter = filter(config, logger)

    def collect(self, num):
        for movie_info, file_link in self.crawler.crawl(num):
            if self.filter.filter(movie_info):
                continue
            folder_name = self.config.folder_rename_pattern.format(**movie_info.__dict__)
            file_name = self.config.file_rename_pattern.format(**movie_info.__dict__)
            try:
                folder_id = self.storage.create_folder(folder_name)
                file_ext, file_id = self.storage.save(folder_id, file_name, file_link)
                self.storage.rename(f"{file_name}.{file_ext}", folder_id, file_id)
                self.filter.record(movie_info)
                self.logger.log(f"成功保存 {movie_info}", log_type="info")
            except Exception as e:
                self.logger.log(e, "error")
        self.filter.close()

