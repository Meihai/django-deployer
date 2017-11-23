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

# 注意事项

- 本项目使用 python3，并支持 python3 所写的 django 应用，包括其它使用 uwsgi 的 python web 应用
- 服务器中请预先安装好 python3、pip3
- 有些 python 包安装时需要 Linux 上的依赖程序，比如 `uwsgi`，请在部署前预先安装好所需要依赖库

# 已完成功能/待完成功能

- [x] 支持服务器使用用户名密码登录
- [ ] 支持服务器使用密钥文件登录
- [x] 支持上传时忽略某些文件或者文件夹，示例见 [d_ignore](confexample/d_ignore)
- [x] 支持线上应用文件的备份
- [x] 支持 django 的 `collectstatic`
- [x] 支持安装 python 包依赖
- [x] 支持启动或重启应用
- [ ] 支持启动或重启应用后附加的自定义 shell 命令，如重启 celery

# 联系我

有什么 bug 或者需要完善的，可以提 [issue](https://github.com/Uphie/django-deployer/issues)，或者发邮件到我邮箱：uphie7@gmail.com

# 开源协议

MIT