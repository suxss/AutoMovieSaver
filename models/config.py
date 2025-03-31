from dataclasses import dataclass
from typing import List


@dataclass
class AccountInfo:
    username: str
    password: str
    root_folder: str

@dataclass
class DBInfo:
    username: str
    password: str
    database: str


@dataclass
class Config:
    accounts: List[AccountInfo]
    folder_rename_pattern: str
    file_rename_pattern: str
    api_url: str
    model: str
    token: str
    db_info: DBInfo