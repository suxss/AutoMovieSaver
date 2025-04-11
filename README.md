# AutoMovieSaver

## 项目简介

AutoMovieSaver 是一个用于自动化收集最新电影的Python项目。通过解析网上他人分享的关于电影的网盘分享链接，并将其存储到自己的网盘中，用户可以轻松获取并管理最新的电影资源。此项目旨在简化电影资源的收集过程，为用户提供便捷的解决方案。

### 功能特性

- **自动化解析**：自动解析各种格式的网盘分享链接。
- **网盘同步**：将解析到的电影资源链接自动存储到用户的网盘中。
- **自动存储管理**：自动切换到有足够剩余空间的账号。
- **最新资源收集**：扫描并收集最新的电影资源。
- **易于配置**：提供简便的配置文件，用户可以根据自己的需求进行配置。

### 使用方法

1. 克隆本项目到本地：
   ```bash
   git clone https://github.com/suxss/AutoMovieSaver.git
   ```
2. 进入项目目录：
   ```bash
   cd AutoMovieSaver
   ```
   
3. 参照以下示例, 编辑 `data` 目录下的 `config.toml` 文件，填写网盘账号信息及其他配置项。
   ```toml
   folder_rename_pattern = "{title} ({year})"  # 文件夹命名模板
   file_rename_pattern = "{title}. {year}"     # 电影文件命名模板
   api_url = "https://api.siliconflow.cn/v1"   # 大模型API接口
   model = "Qwen/Qwen2.5-32B-Instruct"         # 模型
   token = "sk-"                               # API密钥
   cron = "0 6 * * *"                          # cron 表达式, 默认每次运行时转存前10页中的新电影
   
   [[accounts]]
   username = "139****5210"                    # 天翼云盘用户名(手机号)
   password = "123456"                         # 天翼云用户密码
   root_folder = ""                            # 电影存放的文件夹的ID, 为空时将自动在根文件夹创建"电影"文件夹, 并在运行结束后将其id保存至配置文件中以便下一次运行
   
   # 支持多个账号
   #[[accounts]]
   #username = "139****5210"                    # 天翼云盘用户名(手机号)
   #password = "123456"                         # 天翼云用户密码
   #root_folder = "" 
   
   # 默认使用 SQLite, 因此以下参数无需配置
   #[db_info]
   #username = "root"                           # MySQL用户名
   #password = "123456"                         # MySQL密码
   #database = "189_films"                      # MySQL数据库名
   ```
   
4. 构建 docker 镜像：
   ```bash
   docker build -t automoviesaver .
   ```

5. 运行 docker 容器：
   ```bash
    docker run -d \
         --name automoviesaver \
         --restart always \
         automoviesaver
    ```