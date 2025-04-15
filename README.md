# AutoMovieSaver

## 项目简介

AutoMovieSaver 是一个用于自动化收集最新电影的Python项目。通过解析网上他人分享的关于电影的网盘分享链接，并将其存储到自己的网盘中，用户可以轻松获取并管理最新的电影资源。此项目旨在简化电影资源的收集过程，为用户提供便捷的解决方案。

### 功能特性

- **自动化解析**：自动解析各种格式的网盘分享链接。
- **网盘同步**：将解析到的电影资源链接自动存储到用户的网盘中。
- **自动存储管理**：自动切换到有足够剩余空间的账号。
- **最新资源收集**：扫描并收集最新的电影资源。
- **易于配置**：提供简便的配置文件，用户可以根据自己的需求进行配置。

### 运行方法

1. 在当前路径创建 `data` 文件夹, 在`data`文件夹内创建`config.toml` 文件并按照下面的例子进行配置 :
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
   
2. 运行 Docker 镜像
   ```bash
   docker run -d --restart=unless-stopped -v $(pwd)/data:/app/data --name="auto-movie-saver" easychat/auto-movie-saver:v1.0
   ```
   
### 运行模式
1. 定时运行:
   填写配置文件 `config.toml` 中的 `cron` 配置项, 程序将安装此配置项的时间自动运行.

2. 手动运行:
   将配置文件 `config.toml` 中的 `cron` 配置项设置为空字符串 `''`, 然后将在每次启动容器时自动运行一次.