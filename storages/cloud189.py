import re
import time
from dataclasses import dataclass

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA

from models.config import Config
from models.storage import Storage
from utils.base import get_file_ext
from utils.web import WebRequests

PATTERN = r'https*://cloud\.189\.cn/(?:t/|web/share\?code=)([A-Za-z0-9]+)(?:.*?访问码：([A-Za-z0-9]+))?'
COMPILE = re.compile(PATTERN)


class Cloud189Error(Exception):
    """天翼云盘操作基础异常"""
    
    def __init__(self, message: str = "天翼云盘操作错误", code: int = None, details: dict = None):
        """初始化天翼云盘异常
        
        Args:
            message: 错误消息
            code: 错误代码
            details: 额外的错误详情
        """
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)
        
    def __str__(self) -> str:
        """返回易读的错误信息"""
        if self.code:
            return f"{self.__class__.__name__} [错误码: {self.code}]: {self.message}"
        return f"{self.__class__.__name__}: {self.message}"
        
    def add_detail(self, key: str, value: str) -> None:
        """添加错误详情
        
        Args:
            key: 详情键
            value: 详情值
        """
        self.details[key] = value


class ShareLinkError(Cloud189Error):
    """分享链接处理错误"""
    
    def __init__(self, message: str = "分享链接处理错误", code: int = None, details: dict = None, 
                 link: str = None, share_code: str = None):
        """初始化分享链接异常
        
        Args:
            message: 错误消息
            code: 错误代码
            details: 额外的错误详情
            link: 原始分享链接
            share_code: 分享码
        """
        super().__init__(message, code, details)
        if link:
            self.add_detail("link", link)
        if share_code:
            self.add_detail("share_code", share_code)


class StorageError(Cloud189Error):
    """存储空间相关错误"""
    
    def __init__(self, message: str = "存储空间错误", code: int = None, details: dict = None, 
                 account: str = None, needed_space: int = None, available_space: int = None):
        """初始化存储空间异常
        
        Args:
            message: 错误消息
            code: 错误代码
            details: 额外的错误详情
            account: 涉及的账号
            needed_space: 需要的空间大小（字节）
            available_space: 可用空间大小（字节）
        """
        super().__init__(message, code, details)
        if account:
            self.add_detail("account", account)
        if needed_space is not None:
            self.add_detail("needed_space", str(needed_space))
        if available_space is not None:
            self.add_detail("available_space", str(available_space))
            
    def is_space_insufficient(self) -> bool:
        """判断是否为空间不足错误"""
        return "空间不足" in self.message or "insufficient" in self.message.lower()


class FileOperationError(Cloud189Error):
    """文件操作错误"""
    
    def __init__(self, message: str = "文件操作错误", code: int = None, details: dict = None, 
                 operation: str = None, file_id: str = None, file_name: str = None, folder_id: str = None):
        """初始化文件操作异常
        
        Args:
            message: 错误消息
            code: 错误代码
            details: 额外的错误详情
            operation: 操作类型（例如：创建、删除、重命名等）
            file_id: 文件ID
            file_name: 文件名
            folder_id: 文件夹ID
        """
        super().__init__(message, code, details)
        if operation:
            self.add_detail("operation", operation)
        if file_id:
            self.add_detail("file_id", file_id)
        if file_name:
            self.add_detail("file_name", file_name)
        if folder_id:
            self.add_detail("folder_id", folder_id)


@dataclass
class Cloud189File:
    fileId: str
    isFolder: bool
    fileSize: int
    fileName: str

class Cloud189:
    def __init__(self, username, password, logger):
        self.web = WebRequests(logger=logger)
        self.username = username
        self.password = password
        self.api_url = "https://cloud.189.cn/api"
        self.cipher = None
        self.logger = logger

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
        """重命名文件
        
        Args:
            name: 新文件名
            folder_id: 文件夹ID
            file_id: 文件ID，为None时尝试获取文件夹中第一个文件
            
        Returns:
            bool: 重命名是否成功
            
        Raises:
            FileOperationError: 获取文件列表失败或重命名失败
        """
        try:
            # 如果没有指定文件ID，获取文件夹中的第一个文件
            if file_id is None:
                files = self.list_files(folder_id)
                if not files:
                    error_msg = f"获取文件列表失败: 文件夹 {folder_id} 为空或不存在"
                    self.logger.error(error_msg)
                    raise FileOperationError(
                        message=error_msg,
                        operation="rename",
                        folder_id=folder_id
                    )
                    
                file_id = files[0].get("id")
                self.logger.debug(f"使用文件夹 {folder_id} 中的第一个文件: {file_id}")
                
            # 执行重命名操作
            url = f"{self.api_url}/open/file/renameFile.action"
            data = {"fileId": file_id, "destFileName": name}
            
            self.logger.debug(f"重命名文件: {file_id} -> {name}")
            r = self.web.post(url, data=data)
            
            if r.status_code == 200:
                self.logger.info(f"重命名文件成功: {file_id} -> {name}")
                return True
            else:
                error_msg = f"重命名文件失败: HTTP {r.status_code}"
                self.logger.error(error_msg)
                raise FileOperationError(
                    message=error_msg,
                    operation="rename",
                    file_id=file_id,
                    file_name=name,
                    folder_id=folder_id
                )
                
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
                
            error_msg = f"重命名文件时出错: {str(e)}"
            self.logger.error(error_msg)
            raise FileOperationError(
                message=error_msg,
                operation="rename",
                file_id=file_id,
                folder_id=folder_id
            ) from e


class Cloud189Storage(Storage):
    def __init__(self, config: Config, logger):
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
        
        Args:
            save_path: 目标文件夹ID
            file_name: 文件名
            file_info: 分享链接
            
        Returns:
            Tuple: 文件扩展名和文件ID
            
        Raises:
            ShareLinkError: 分享链接无效或处理分享链接时出错
            StorageError: 存储空间不足
            FileOperationError: 文件操作失败
        """
        self.logger.info(f"开始处理分享链接: {file_info}")
        
        # 解析分享链接
        try:
            match = COMPILE.search(file_info)
            if not match:
                self.logger.error(f"无效的分享链接格式: {file_info}")
                raise ShareLinkError(f"获取分享码失败: 链接格式无效 - {file_info}")
                
            share_code = match.group(1)
            if match.group(2):
                share_code = f"{share_code}（访问码：{match.group(2)}）"
                
            self.logger.debug(f"解析得到分享码: {share_code}")
        except Exception as e:
            self.logger.error(f"解析分享链接时出错: {e}")
            raise ShareLinkError(f"解析分享链接时出错: {str(e)}") from e
        
        # 获取分享信息
        try:
            file, access_code, share_id, share_mode = self.current_client.get_share_info(share_code)
            if not file:
                self.logger.error(f"无法获取分享信息: {share_code}")
                raise ShareLinkError(f"获取分享信息失败: {share_code}")
                
            self.logger.debug(f"成功获取分享文件信息: {file.fileName}, 大小: {file.fileSize}")
        except Exception as e:
            self.logger.error(f"获取分享信息失败: {e}")
            raise ShareLinkError(f"获取分享信息失败: {str(e)}") from e
            
        # 获取文件列表
        try:
            files = self.current_client.list_share_dir(file.fileId, access_code, share_id, share_mode)
            if files:
                max_size_file = max(files, key=lambda f: f.fileSize)
                self.logger.debug(f"选择最大文件: {max_size_file.fileName}, 大小: {max_size_file.fileSize}")
            else:
                max_size_file = file
                self.logger.debug(f"使用主文件: {max_size_file.fileName}")
                
            file_ext = get_file_ext(max_size_file.fileName)
        except Exception as e:
            self.logger.error(f"处理分享文件列表时出错: {e}")
            raise FileOperationError(f"处理分享文件时出错: {str(e)}") from e
            
        # 检查存储空间并在多账号间切换
        try_times = 0
        while True:
            try:
                if self.has_sufficient_storage(max_size_file):
                    self.logger.info(f"账号 {self.current_client.username} 空间充足，开始转存")
                    break
                    
                try_times += 1
                self.logger.warning(f"账号 {self.current_client.username} 空间不足，切换到下一个账号")
                self.switch_client()
                
                if try_times > self.accounts_num:
                    self.logger.error("所有账号空间均不足，无法继续转存")
                    raise StorageError(f"所有账号空间均不足，文件大小: {max_size_file.fileSize}")
            except StorageError:
                raise
            except Exception as e:
                self.logger.error(f"检查存储空间时出错: {e}")
                raise StorageError(f"检查存储空间时出错: {str(e)}") from e
            
        # 执行转存操作
        try:
            save_result = self.current_client.save_share_file(
                max_size_file.fileId, 
                share_id, 
                f"{file_name}.{file_ext}", 
                save_path
            )
            
            if not save_result:
                self.logger.error(f"转存失败: {max_size_file.fileName}")
                raise FileOperationError(f"转存文件失败: {max_size_file.fileName}")
                
            self.logger.info(f"成功转存文件: {file_name}.{file_ext}")
            return file_ext, None
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            self.logger.error(f"转存过程中出错: {e}")
            raise FileOperationError(f"转存过程中出错: {str(e)}") from e

    def has_sufficient_storage(self, file: Cloud189File) -> bool:
        """检查当前账号是否有足够空间存储文件
        
        Args:
            file: 要存储的文件对象
            
        Returns:
            bool: 是否有足够空间
            
        Raises:
            StorageError: 获取存储空间信息失败
        """
        try:
            storage_info = self.current_client.get_size_info()
            
            if storage_info is None:
                self.logger.error(f"账号 {self.current_client.username} 无法获取存储空间信息")
                raise StorageError(
                    message="获取剩余空间信息失败",
                    account=self.current_client.username,
                    operation="检查存储空间"
                )
                
            available_space = storage_info.get("freeSize", 0)
            needed_space = file.fileSize
            
            # 添加额外的安全边界，确保有足够空间（额外预留10MB）
            is_sufficient = available_space > needed_space + (10 * 1024 * 1024)
            
            if not is_sufficient:
                self.logger.warning(
                    f"空间不足: 账号 {self.current_client.username} - "
                    f"需要: {needed_space/(1024*1024):.2f}MB, "
                    f"可用: {available_space/(1024*1024):.2f}MB"
                )
                
            return is_sufficient
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
                
            error_msg = f"检查存储空间时出错: {str(e)}"
            self.logger.error(error_msg)
            raise StorageError(
                message=error_msg,
                account=self.current_client.username,
                needed_space=file.fileSize
            ) from e

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