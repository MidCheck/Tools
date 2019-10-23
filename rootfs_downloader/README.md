# rootfs\_downloader
此程序功能为根文件系统下载，可以完整下载目标系统的文件系统。

## 使用方法
```
$ python rfsdown.py -h
usage: python rfsdown.py [-h] [-p PORT] [-l root] [-P PASSWORD] [-r REMOTE]
                         [-d DIRECTORY] [-s png] [-z ZIPFILE] [-e ERRLOG]
                         hostip

download root file system via ssh.

positional arguments:
  hostip                target system ip

optional arguments:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  target system port
  -l root, --login root
                        target system username, default is 'root'
  -P PASSWORD, --password PASSWORD
                        the password specified by the login parameter
  -r REMOTE, --remote REMOTE
                        remote path, it can be a file or a directory, default
                        is '/'
  -d DIRECTORY, --directory DIRECTORY
                        store the location of the downloaded file, default is
                        '.'
  -s png, --suffix png  when specify this parameter, only files with this
                        suffix are downloaded
  -z ZIPFILE, --zipfile ZIPFILE
                        specify this parameter to be added to the specified
                        compressed file when downloading
  -e ERRLOG, --errlog ERRLOG
                        log the error log, if not specified, will redirect to
                        /dev/null
```

## 下一版本
1. 添加多线程，改善运行速度

## 时间表：
|   时间     |   内容    |
|:----------:|-----------|
| 2019-10-14 | 创建项目, 搭建python开发环境,寻找资料  |
| 2019-10-17 | 完成第一版本，可以初步下载文件系统 |
| 2019-10-22 | 修复第一版本出现的问题，添加压缩功能 |
| 2019-10-23 | 添加错误日志、命令行参数、后缀名匹配下载功能 |

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

### day5
修复第一版本出现的异常，使用zipfile库添加了下载文件添加到压缩包功能，由于zipfile只支持目录与普通文件压缩，所以目前不支持链接加入压缩包。

### day6
使用argparse库添加命令行支持，getpass库添加密码回显输入，加入错误日志，后缀名匹配下载功能。

bug：在下载/proc目录时，程序虽在运行，但出现“卡住”情况，使用Ctrl^c后，重新运行则可从卡住处继续下载（需遍历远程主机目录并与本地对比，消耗时间可不记），此状况未修复。

## 参考资料
1. [github - paramiko](https://github.com/paramiko/paramiko)
2. [渗透思路-使用python获取特定文件](https://zhuanlan.zhihu.com/p/31943296)
3. [how-to-check-a-remote-path-is-a-file-or-a-directory](https://stackoverflow.com/questions/18205731/how-to-check-a-remote-path-is-a-file-or-a-directory)
4. [zipfile — Work with ZIP archives](https://docs.python.org/3/library/zipfile.html)
5. [argparse — Parser for command-line options, arguments and sub-commands](https://docs.python.org/3/library/argparse.html)
