# rootfs\_downloader
此程序功能为根文件系统下载，可以完整下载目标系统的文件系统。

## 使用方法
```
python rfsdown.py  # 需在main里修改目标信息
```

## 下一版本
1. 加入命令行参数
2. 可以筛选特定后缀或特定子节文件
3. 添加多线程下载

## 时间表：
|   时间     |   内容    |
|:----------:|-----------|
| 2019-10-14 | 创建项目, 搭建python开发环境,寻找资料  |
| 2019-10-17 | 完成第一版本，可以初步下载文件系统 |

### day1
经过测试使用cat二进制文件重定向到文件内，添加可执行权限依然可以执行该文件，
因此利用SSH执行shell命令进行回传文件。

完成了paramiko库的测试。

### day2
查找资料，尝试使用SSH执行"ls -l"获取文件权限，对回传结果进行分割，设置本地下载文件的权限。对长目录进行分割，并创建本地目录。

尝试失败，分割结果较为复杂。

### day3
发现paramiko库含有SFTP功能。

### day4
完成第一版本，可以下载整个系统文件。

不足：软链接的处理，只在本地重新创建远程文件类似链接。


## 参考资料
1. [github - paramiko](https://github.com/paramiko/paramiko)
2. [渗透思路-使用python获取特定文件](https://zhuanlan.zhihu.com/p/31943296)
3. [how-to-check-a-remote-path-is-a-file-or-a-directory](https://stackoverflow.com/questions/18205731/how-to-check-a-remote-path-is-a-file-or-a-directory)
