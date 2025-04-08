from abc import ABC, abstractmethod


class Storage(ABC):
    @abstractmethod
    def save(self, save_path, file_name, origin_file_info): ...

    @abstractmethod
    def rename(self, new_name, path, origin_name): ...

    @abstractmethod
    def create_folder(self, folder_name, parent_folder_path): ...

    @abstractmethod
    def wait_until_save_complete(self, file_name, save_path): ...

    @abstractmethod
    def get_current_account_info(self): ...