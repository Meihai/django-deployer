# django-deployer
一条命令部署 django 应用，包括其它使用 uwsgi 的 python web 应用

# 使用方法

使用前请先阅读 confexample 文件夹下的示例配置文件

在命令行工具中执行
```
$ python deployer.py /some_path/d_conf
```
其中 `/some_path/d_conf` 为所要部署 django 应用的部署配置文件，示例部署配置文件为本项目中 `confexample/d_conf`
，如果没有该参数将使用 `confexample/d_conf` 文件。

## 部署配置文件

参数中的本地文件路径可使用 `~` 符号表示登录用户的家目录，如 `~/projects/MyApp`

参数:
- `host` 服务器主机地址，必填
- `port` 服务器 SSH 端口，默认 22
- `pri_key` SSH 私钥文件绝对路径，`pri_key` 和 `password` 至少选择填写一个，优先使用 SSH 私钥文件登录
- `pri_key_password` SSH 私钥文件密码，如果没有的话请注释该行
- `user` 登录用户名，默认 `root`
- `password` 登录密码，`pri_key` 和 `password` 至少选择填写一个，优先使用 SSH 私钥文件登录
- `local_project_dir` 本地项目路径，必填
- `remote_project_dir` 远程项目路径，必填
- `remote_uwsgi_path` 远程 uwsgi 配置文件路径，默认 `remote_project_dir/uwsgi.ini`
- `remote_requirements_path` 远程 requirements.txt 文件路径，默认 `remote_project_dir/requirements.txt`
- `remote_shell_path` 远程 shell 脚本文件路径，用于部署后执行，如不需要的话请注释该行
- `ignore_path` 本地上传忽略文件路径，建议放在 web 应用根目录下，默认 `local_project_dir/d_ignore`
- `collectstatic` 对于 django 应用是否在上传前先收集静态文件，非 django 项目可忽略该参数，默认 False

## 上传忽略文件

这里的路径都是相对于项目的相对路径

支持下面四种形式的写法
- `dir/file` 忽略指定文件
- `*.ext` 忽略所有指定后缀的文件，如忽略 markdown 文件，写作 `*.md`
- `dir1/dir2/` 忽略指定目录
- `*/dir/` 忽略所有包含 `dir` 的目录，如忽略所有的 \_\_pycache__ 文件夹，写作 `*/__pycache__/`

# 注意事项

- 本项目使用 python3，并支持 python3 所写的 django 应用，包括其它使用 uwsgi 的 python web 应用
- 服务器中请预先安装好 python3、pip3
- 有些 python 包安装时需要 Linux 上的依赖程序，比如 `uwsgi`，请在部署前预先安装好所需要依赖库

# 已完成功能/待完成功能

- [x] 支持服务器使用用户名密码登录
- [x] 支持服务器使用密钥文件登录
- [x] 支持上传时忽略某些文件或者文件夹，示例见 [d_ignore](confexample/d_ignore)
- [x] 支持线上应用文件的备份
- [x] 支持自动收集 django 静态文件
- [x] 支持自动安装 python 包依赖
- [x] 支持自动启动或重启应用
- [x] 支持自动启动或重启应用后执行自定义 shell 脚本，如执行重启 celery 命令
- [ ] 支持日志输出到文件

# 联系我

有什么 bug 或者建议，可以提 [issue](https://github.com/Uphie/django-deployer/issues)，或者发邮件到我邮箱：uphie7@gmail.com

# 开源协议

MIT