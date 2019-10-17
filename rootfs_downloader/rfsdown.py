#! /usr/bin/env python
# -*- coding: utf-8 -*-
import paramiko
import os, stat, sys

class RootfsDownloader:
    '''
    想法: 利用sftp.listdir_attr 递归遍历所有目录并下载文件，
          然后设置文件的stat
    '''
    def __init__(self, username, password, ip, port = 22):
        self.ip = ip
        self.port = port
        self.trans = paramiko.Transport((self.ip, self.port))
        self.trans.connect(username = username, password = password)
        self.sftp = paramiko.SFTPClient.from_transport(self.trans)
        print("connection ready ...")
    
    def __del__(self):
        self.trans.close()
        print("connection closed !")
    
    def download(self, remotepath = "/", localpath = "."):
        '''
        接受参数：
            remotepath: 要下载的远程根路径，字符串类型，默认为系统根路径
            localpath: 存储位置，字符串类型，默认为脚本执行目录
        返回值：
            无

        思路：递归遍历目录，如果当前路径是符号链接，则本地创建链接;
              如果是目录，则本地创建目录，其余则下载。
              对非符号链接文件的访问权限以及时间等属性进行设置，
              当前可设置属性有st_uid, st_gid, st_mode, st_atime, st_mtime
        参考：https://github.com/paramiko/paramiko/blob/master/paramiko/sftp_attr.py
        '''
        for fileattr in self.sftp.listdir_attr(remotepath):
            # rpath = remotepath + '\\' + fileattr.filename # Windows
            rpath = remotepath + '/' + fileattr.filename # Linux
            lpath = os.path.join(localpath, fileattr.filename)
            if stat.S_ISLNK(fileattr.st_mode):
                realpath = self.sftp.readlink(rpath)
                try:
                    os.symlink(realpath, lpath)
                except: # continue whether the link exists or not
                    pass
                continue
            elif not stat.S_ISDIR(fileattr.st_mode):
                if os.path.exists(lpath): 
                    continue
                # print download log
                # print("download remote file %s\n--------> local path %s\n" % (fileattr.filename, lpath))
                self.sftp.get(rpath, lpath)
            else:
                if not os.path.exists(lpath):
                    os.mkdir(lpath)
                self.download(rpath, lpath)

            # set attributes for local file except symlink file
            os.chmod(lpath, fileattr.st_mode)
            os.chown(lpath, fileattr.st_uid, fileattr.st_gid)
            os.utime(lpath, (fileattr.st_atime, fileattr.st_mtime))

    
if __name__ == '__main__':
    # target information (Metasploitable)
    ip = "192.168.217.133"
    port = 22
    
    user = "root"
    password = "root"
    
    remote_path = "/"
    local_path = "./msfadmin"
    
    rfs = RootfsDownloader(user, password, ip, port)
    rfs.download(remote_path, local_path)
    print("finish download!")
