#! /usr/bin/env python
# -*- coding: utf-8 -*-
import paramiko
import os, stat, re
import zipfile, argparse, getpass

def is_admin():
    import platform
    if platform.system() == 'Linux':        # Linux
        return os.geteuid() == 0
    elif platform.system() == "Windows":    # Windows
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() == True
        except:
            return False
    elif platform.system() == "Darwin":
        pass
    else:
        return False


class RootfsDownloader:
    '''
    想法: 利用sftp.listdir_attr 递归遍历所有目录并下载文件，
          然后设置文件的stat
    '''
    def __init__(self, username, password, ip, port = 22, errlog = None):
        self.ip = ip
        self.port = port
        self.username = username
        self.password = password
        self.trans = paramiko.Transport((self.ip, self.port))
        try:
            self.trans.connect(username = self.username, password = self.password)
        except:
            exit(-1)
        self.sftp = paramiko.SFTPClient.from_transport(self.trans)
        self.zipfile = None
        self.ssh = None

        if errlog is not None:
            self.errlog = open(errlog, 'w')
        else:
            self.errlog = open('/dev/null', 'w')
    
    def __del__(self):
        try:
            self.trans.close()
            if self.errlog is not None:
                self.errlog.close()
        except:
            exit(-2)

    def SSH(func):
        '''
            获取ssh连接的装饰器
        '''
        def wrapper(self, *args, **kwargs):
            self.ssh = paramiko.SSHClient()
            self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            self.ssh.connect(
                    hostname = self.ip, port = self.port, 
                    username = self.username, password = self.password)
            func(self, *args, **kwargs)
            self.ssh.close()
            self.ssh = None
        return wrapper


    @SSH
    def _is_admin(self):
        stdin, stdout, stderr = self.ssh.exec_command("id | awk '{print $1}'")
        res = stdout.read().decode('utf-8')

        matched = re.match(r'.*id=(\d+)\(.*\).*', res, re.M | re.I)
        if matched:
            return matched.group(1) == '0'
        else:
            print("Error: Execution of command 'id | awk \'{print $1}\'' failed on target machine: ", (self.ip + ":" + str(self.port)))
            print("Return result is: ", res)
            return False

    def _set_perm(self, local_path, fileattr):
        try:
            # set attributes for local file except symlink file
            os.chmod(local_path, fileattr.st_mode)
            os.chown(local_path, fileattr.st_uid, fileattr.st_gid)
            os.utime(local_path, (fileattr.st_atime, fileattr.st_mtime))
        except:
            self.errlog.write("[-] permission setting failed, local path: %s\n" % local_path)
    
    def _zip(self, local_path):
        if self.zipfile is not None:
            self.zipfile.write(local_path)
    
    def _create_link(self, remotepath):
        '''
        函数功能： 根据remotepath创建本地链接
        接受参数:
            remotepath: 远程链接的路径
        返回值:
            无
        '''
        try:
            realpath = self.sftp.readlink(remotepath)
        except PermissionError as e:
            self.errlog.write("[!]" + str(e) +
                  ", you do not have permission to read this link:%s\n" %
                  remotepath)
        except FileNotFoundError as e:
            self.errlog.write("[!]" + str(e) + ", %s\n" % remotepath)
        else:
            try:
                os.symlink(realpath, remotepath)
            except: # continue whether the link exists or not
                pass
            else:
                # Zipfile does not currently support adding link files
                # self.zipfile.write(realpath)
                pass

    def _can_download(self, remotepath, fileattr):
        '''
        函数功能： 判断远程文件是否可下载
        接受参数：
            remotepath: 远程文件
            fileattr: 远程文件的属性
        返回值：
            可下载则True，否则为False
        '''
        if stat.S_ISREG(fileattr.st_mode):  # 普通文件默认可下载，需处理下载异常
            return True
        elif stat.S_ISLNK(fileattr.st_mode):
            self._create_link(remotepath)
            return False
        elif stat.S_ISSOCK(fileattr.st_mode):
            self.errlog.write("[-] socket file: %s\n" % remotepath)
            return False
        elif stat.S_ISCHR(fileattr.st_mode):
            self.errlog.write("[-] character device: %s\n" % remotepath)
            return False
        elif stat.S_ISFIFO(fileattr.st_mode):
            self.errlog.write("[-] pipeline file: %s\n" % remotepath)
            return False
        elif stat.S_ISBLK(fileattr.st_mode):
            self.errlog.write("[-] block file: %s\n" % remotepath)
            return False
        else:
            return False

    def _download_file(self, rpath, lpath, r_fileattr):
        '''
        函数功能： 把rpath指定的远程文件下载到本地lpath指定的存储位置
        接受参数：
            rpath: 要下载的远程根路径，字符串类型
            lpath: 存储位置，字符串类型
            r_fileattr: 远程文件的属性
        返回值：
            无
        '''
        try:
            if r_fileattr.st_size != 0:  # 大小为0的特殊文件情况
                self.sftp.get(rpath, lpath)
            else:
                with open(lpath, 'a'):
                    os.utime(lpath, None)
        except PermissionError as e:
            self.errlog.write("[!]" + str(e) + 
                  ", you do not have permission to download this file:%s\n" %
                  rpath)
        except FileNotFoundError as e:
            self.errlog.write("[?]" + str(e) + ", %s\n" % rpath)
        except OSError as e:
            self.errlog.write("[!]" + str(e) + ", OS error, rpath:%s, lpath:%s\n" 
                    % (rpath, lpath))
        except:
           self.errlog.write("[-] Other error, %s -> %s\n" % (rpath, lpath))
        else:
            # print("download remote file %s to local path %s\n" % (fileattr.filename, lpath))
            pass


    def _download(self, remotepath, localpath, suffix):
        '''
        接受参数：
            remotepath: 要下载的远程根路径，字符串类型，默认为系统根路径
            localpath: 存储位置，字符串类型，默认为脚本执行目录
            suffix: 文件后缀，如果指定，则只下载远程目标后缀匹配的文件
        返回值：
            无

        思路：递归遍历目录，如果当前路径是符号链接，则本地创建链接;
              如果是目录，则本地创建目录，其余则下载。
              对非符号链接文件的访问权限以及时间等属性进行设置，
              当前可设置属性有st_uid, st_gid, st_mode, st_atime, st_mtime
        参考：https://github.com/paramiko/paramiko/blob/master/paramiko/sftp_attr.py
        '''
        try:
            listdir_attr = self.sftp.listdir_attr(remotepath)
        except PermissionError as e:
            self.errlog.write("[!]" + str(e) + 
                  ", you do not have permission to access this directory:" +
                  remotepath + "\n")
        except FileNotFoundError as e: # listdir_attr方法对一些特殊文件会产生FileNotFound异常，在这里处理
            try:
                # special_file
                sf_stat = self.sftp.stat(remotepath)
            except:
                self.errlog.write("[?]" + str(e) + ", " + remotepath + "\n")
            else:
                lpath = os.path.join(localpath, os.path.basename(remotepath))
                if self._can_download(remotepath, sf_stat):
                    self._download_file(remotepath, lpath, sf_stat)
                    self._set_perm(lpath, sf_stat)
        else:
            for fileattr in listdir_attr:
                if suffix is not None and \
                        not stat.S_ISDIR(fileattr.st_mode) and \
                        os.path.splitext(fileattr)[-1][1:] != suffix:
                    continue
                # rpath = remotepath + '\\' + fileattr.filename # Windows
                rpath = os.path.join(remotepath, fileattr.filename) # Linux
                lpath = os.path.join(localpath, fileattr.filename)
                
                if stat.S_ISDIR(fileattr.st_mode):
                    if not os.path.exists(lpath):
                        os.mkdir(lpath)
                    self._download(rpath, lpath, suffix)
                else:
                    if os.path.exists(lpath) or not self._can_download(rpath, fileattr):
                        continue
                    self._download_file(rpath, lpath, fileattr)

                self._set_perm(lpath, fileattr)
                self._zip(lpath)
    

    def download(self, remotepath = "/", localpath = ".", suffix = None, zfile = None):
        # 检测本地root权限
        if not is_admin():
            print("Please run it as sudo or root user!")
            exit()
        
        # 检测远程root权限
        if not self._is_admin():
            print("Waring: The user %s is not the root user of %s, some files will not have permission to download!" % (self.username, self.ip + ':' + str(self.port)))
        
        # 本地指定文件夹不存在则创建
        if not os.path.exists(localpath):
            os.mkdir(localpath)

        print("Start download...")
        if zfile is not None:
            self.zipfile = zipfile.ZipFile(zfile, mode = 'a')

        self._download(remotepath, localpath, suffix)
        
        if zfile is not None:
            self.zipfile.close()
        print("Finish download!")

    @SSH
    def download_disk(self, remotepath, localpath, readsize = 2097152, bs = '2M'):
        command = "dd if=" + remotepath
        command += " bs=" + bs
        stdin, stdout, stderr = self.ssh.exec_command(command)
 	
        with open(localpath, 'wb') as f:
            while True:
            	res = stdout.read(readsize)
            	if res == b'':
            		break
            	f.write(res)
            
        
        
if __name__ == '__main__':
    # parse arguments
    parser = argparse.ArgumentParser(
            prog = 'python rfsdown.py', 
            description = 'download root file system via ssh.')
    
    parser.add_argument('hostip', help='target system ip')

    parser.add_argument('-p', '--port', 
            type = int,
            default = 22,
            help = 'target system port')

    parser.add_argument('-l', '--login', 
            metavar = 'root',
            default = 'root',
            help = "target system username, default is 'root'")

    parser.add_argument('-P', '--password', 
            help = 'the password specified by the login parameter')
    
    parser.add_argument('-r', '--remote', 
            default = '/',
            help = "remote path, it can be a file or a directory, default is '/'")
    
    parser.add_argument('-d', '--directory',
            default = '.',
            help = "store the location of the downloaded file, default is '.'")
    
    parser.add_argument('-s', '--suffix',
            metavar='png',
            help = 'when specify this parameter, only files with this suffix are downloaded')

    parser.add_argument('-z', '--zipfile',
            help = 'specify this parameter to be added to the specified compressed file when downloading')

    parser.add_argument('-e', '--errlog', help = 'log the error log, if not specified, will redirect to /dev/null')

    parser.add_argument('-D', '--dd', 
            action = 'store_true',
            help = "download remote hard disk via commmand 'dd'")

    parser.add_argument('-b', '--bs',
            default = '2M',
            help = "if -D mode is specified, 'bs' parameter of command 'dd'")

    parser.add_argument('-k', '--keep_size',
            default = 2097152,
            type = int,
            help = "if -D mode is specified, the size of bytes read from the channel every time,\
             should be smaller than the current available memory size,\
             default is 2097152(2M)")

    args = parser.parse_args()
    if args.password is None:
        password = getpass.getpass("password:")
    else:
        password = args.password
    
    rfs = RootfsDownloader(
        args.login, password, 
        args.hostip, args.port, 
        errlog = args.errlog)
    
    if not args.dd:
        rfs.download(args.remote, args.directory, zfile = args.zipfile)
    else:
        if args.remote == '/':
            args.remote = '/dev/sda'

        if args.directory == '.':
            args.directory = os.path.basename(args.remote) + '.img'
           
        rfs.download_disk(args.remote, args.directory, args.keep_size, args.bs)