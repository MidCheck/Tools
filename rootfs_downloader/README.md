# rootfs\_downloader
此程序功能为根文件系统下载，可以完整下载目标系统的文件系统。

## 时间表：
|   时间     |   内容    |
|:----------:|-----------|
| 2019-10-14 | 创建项目, 搭建python开发环境,寻找资料  |


### day1
经过测试使用cat二进制文件重定向到文件内，添加可执行权限依然可以执行该文件，
因此利用SSH执行shell命令进行回传文件。

完成了paramiko库的测试。