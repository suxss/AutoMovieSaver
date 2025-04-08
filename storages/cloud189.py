import re
import time
from dataclasses import dataclass

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from models.config import Config
from models.logger import Logger
from models.storage import Storage
from utils.base import get_file_ext
from utils.web import WebRequests

PATTERN = r'https*://cloud\.189\.cn/(?:t/|web/share\?code=)([A-Za-z0-9]+)(?:.*?访问码：([A-Za-z0-9]+))?'
COMPILE = re.compile(PATTERN)

@dataclass
class Cloud189File:
    fileId: str
    isFolder: bool
    fileSize: int
    fileName: str

class Cloud189:
    def __init__(self, username, password, logger: Logger):
        self.web = WebRequests(logger=logger)
        self.username = username
        self.password = password
        self.api_url = "https://cloud.189.cn/api"
        self.cipher = None

    def get_encrypt_config(self):
        url = "https://open.e.189.cn/api/logbox/config/encryptConf.do"
        data = {"appId": "cloud"}
        r = self.web.post(url, data).json()
        return r.get("data")

    def get_app_config(self, refer, params):
        url = "https://open.e.189.cn/api/logbox/oauth2/appConf.do"
        data = {"appKey": "cloud", "version": "2.0"}
        headers = {"lt": params.get("lt"), "reqid": params.get("reqId"), "Referer": refer, "Origin": "https://open.e.189.cn"}
        r = self.web.post(url, data, headers=headers).json()
        return r.get("data")

    def init_rsa(self, pubkey):
        pub = RSA.importKey(f"-----BEGIN PUBLIC KEY-----\n{pubkey}\n-----END PUBLIC KEY-----")
        self.cipher = PKCS1_v1_5.new(pub)

    def encrypt(self, text):
        if self.cipher is None:
            return
        return self.cipher.encrypt(text.encode()).hex()

    def generate_login_data(self):
        refer, params = self.init_login()
        encrypt_config = self.get_encrypt_config()
        app_config = self.get_app_config(refer, params)
        self.init_rsa(encrypt_config["pubKey"])
        pre = encrypt_config["pre"]
        data = {
            "version": "v2.0",
            "apToken": "",
            "appKey": "cloud",
            "accountType": "01",
            "userName": f"{pre}{self.encrypt(self.username)}",
            "epd": f"{pre}{self.encrypt(self.password)}",
            "captchaType": "",
            "validateCode": "",
            "smsValidateCode": "",
            "captchaToken": "",
            "mailSuffix": "",
            "dynamicCheck": False,
            "clientType": 1,
            "cb_SaveName": 0,
            "isOauth2": False,
            "state": "",
            "paramId": app_config["paramId"]
        }
        headers = {"lt": params.get("lt"), "reqid": params.get("reqId"), "Referer": refer, "Origin": "https://open.e.189.cn"}
        return data, headers

    def init_login(self):
        url = f"{self.api_url}/portal/loginUrl.action?redirectURL=https%3A%2F%2Fcloud.189.cn%2Fmain.action"
        r = self.web.get(url)
        return r.url, {item[0]: item[-1] if len(item) > 1 else "" for item in [param.split("=") for param in r.url.split("?")[-1].split("&")]}

    def login(self):
        data, headers = self.generate_login_data()
        url = "https://open.e.189.cn/api/logbox/oauth2/loginSubmit.do"
        r = self.web.post(url, data, headers=headers)
        url = r.json()["toUrl"]
        r = self.web.post(url, headers={"Referer": "https://open.e.189.cn/"})
        return r.status_code == 200

    def get_size_info(self):
        url = f"{self.api_url}/portal/getUserSizeInfo.action"
        r = self.web.get(url)
        if r.status_code == 200:
            return r.json().get("cloudCapacityInfo")
        return None

    def create_folder(self, folder_name: str, root_folder: str):
        url = f"{self.api_url}/open/file/createFolder.action"
        data = {"folderName": folder_name, "parentFolderId": root_folder}
        r = self.web.post(url, data=data)
        if r.status_code == 200:
            return r.json().get("id")
        return None

    def create_root_folder(self, folder_name: str):
        return self.create_folder(folder_name, "-11")

    def get_share_info(self, share_code: str):
        url = f"{self.api_url}/open/share/getShareInfoByCodeV2.action?shareCode={share_code}"
        r = self.web.get(url)
        if r.status_code == 200:
            j = r.json()
            file = Cloud189File(fileId=j.get("fileId"), isFolder=j.get("isFolder"), fileSize=j.get("fileSize"), fileName=j.get("fileName"))
            return file, j.get("accessCode"), j.get("shareId"), j.get("shareMode")
        return None, None, None, None

    def list_share_dir(self, file_id: str, access_code: str, share_id: str, share_mode: int):
        url = f"{self.api_url}/open/share/listShareDir.action?pageNum=1&pageSize=60&fileId={file_id}&shareDirFileId={file_id}&isFolder=true&shareId={share_id}&shareMode={share_mode}&iconOption=5&orderBy=lastOpTime&descending=true&accessCode={access_code}"
        r = self.web.get(url)
        total_files = []
        if r.status_code == 200:
            file_list = r.json().get("fileListAO", {}).get("fileList", [])
            folder_list = r.json().get("fileListAO", {}).get("folderList", [])
            for file_info in file_list:
                file = Cloud189File(fileId=file_info.get("id"), isFolder=False, fileSize=file_info.get("size"), fileName=file_info.get("name"))
                total_files.append(file)
            for folder_info in folder_list:
                total_files.extend([file for file in self.list_share_dir(folder_info.get("id"), access_code, share_id, share_mode)])
            return total_files
        else:
            return []

    def save_share_file(self, file_id: str, share_id: str, name: str, target_folder_id: str):
        url = f"{self.api_url}/open/batch/createBatchTask.action"
        data = {"type": "SHARE_SAVE",
                "taskInfos": str([{"fileId": file_id, "fileName": name, "isFolder": 0}]),
                "targetFolderId": target_folder_id, "shareId": share_id}
        r = self.web.post(url, data=data)
        return r.status_code == 200

    def list_files(self, folder_id):
        url = f"{self.api_url}/open/file/listFiles.action?pageSize=60&pageNum=1&mediaType=0&folderId={folder_id}&iconOption=5&orderBy=lastOpTime&descending=true"
        r = self.web.get(url)
        if r.status_code == 200:
            file_list = r.json().get("fileListAO", {}).get("fileList", [])
            return file_list
        return []

    def rename_file(self, name: str, folder_id: str, file_id: str=None):
        if file_id is None:
            files = self.list_files(folder_id)
            if files:
                file_id = files[0].get("id")
            else:
                raise BaseException("获取文件列表失败")
        url = f"{self.api_url}/open/file/renameFile.action"
        data = {"fileId": file_id, "destFileName": name}
        r = self.web.post(url, data=data)
        return r.status_code == 200


class Cloud189Storage(Storage):
    def __init__(self, config: Config, logger: Logger):
        self.clients = [Cloud189(username=account.username, password=account.password, logger=logger) for account in config.accounts]
        self.root_folders = [account.root_folder for account in config.accounts]
        self.clients[0].login()
        self.accounts_num = len(config.accounts)
        self.current_client_index = 0
        self.logger = logger
        self.config = config

    @property
    def current_client(self):
        return self.clients[self.current_client_index]

    @property
    def current_root_folder_id(self):
        if not self.root_folders[self.current_client_index]:
            self.config.accounts[self.current_client_index].root_folder = self.root_folders[self.current_client_index] = self.current_client.create_root_folder("电影")
        return self.root_folders[self.current_client_index]

    def switch_client(self):
        self.current_client_index += 1
        if self.current_client_index >= self.accounts_num:
            self.current_client_index = 0
        self.current_client.login()

    def save(self, save_path: str, file_name: str, file_info: str):
        """
        转存分享链接
        :param file_name:
        :param save_path: 文件夹id
        :param file_info: 分享链接
        """
        match = COMPILE.search(file_info)
        if match:
            share_code = match.group(1)
            if match.group(2):
                share_code = f"{share_code}（访问码：{match.group(2)}）"
        else:
            raise BaseException("获取分享码失败")
        file, access_code, share_id, share_mode = self.current_client.get_share_info(share_code)
        if file:
            files = self.current_client.list_share_dir(file.fileId, access_code, share_id, share_mode)
            if files:
                max_size_file = max(files, key=lambda f: f.fileSize)
            else:
                max_size_file = file
            file_ext = get_file_ext(max_size_file.fileName)
            try_times = 0
            while True:
                if self.has_sufficient_storage(max_size_file):
                    break
                try_times += 1
                self.switch_client()
                if try_times > self.accounts_num:
                    raise "空间不足"
            if not self.current_client.save_share_file(max_size_file.fileId, share_id, f"{file_name}.{file_ext}", save_path):
                raise BaseException("转存失败")
            else:
                return file_ext, None
        raise BaseException("获取分享信息失败")

    def has_sufficient_storage(self, file: Cloud189File) -> bool:
        storage_info = self.current_client.get_size_info()
        if storage_info is None:
            raise BaseException("获取剩余空间信息失败")
        return storage_info.get("freeSize", 0) > file.fileSize

    def rename(self, new_name: str, path: str, origin_name: str=None):
        """
        重命名
        :param path: 文件夹id
        :param origin_name: 为空时重命名文件夹下第一个文件
        :param new_name: 新名字
        """
        return self.current_client.rename_file(new_name, path, origin_name)

    def create_folder(self, folder_name, parent_folder_path: str=None):
        return self.current_client.create_folder(folder_name, self.current_root_folder_id)

    def wait_until_save_complete(self, file_name, save_path):
        time.sleep(2)
        return

    def get_current_account_info(self):
        return "Cloud189", self.current_client.username