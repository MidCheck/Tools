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
        self.trans.connect(username = self.username, password = self.password)
        self.sftp = paramiko.SFTPClient.from_transport(self.trans)
        self.zipfile = None
        if errlog is not None:
            self.errlog = open(errlog, 'w')
        else:
            self.errlog = open('/dev/null', 'w')
    
    def __del__(self):
        self.trans.close()
        if self.errlog is not None:
            self.errlog.close()

    def _is_admin(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname = self.ip, port = self.port, 
                    username = self.username, password = self.password)
        stdin, stdout, stderr = ssh.exec_command("id | awk '{print $1}'")
        res = stdout.read().decode('utf-8')
        ssh.close()

        matched = re.match(r'.*id=(\d+)\(.*\).*', res, re.M | re.I)
        if matched:
            return matched.group(1) == '0'
        else:
            print("Error: Execution of command 'id | awk \'{print $1}\'' failed on target machine: ", (self.ip + ":" + str(self.port)))
            print("Return result is: ", res)
            return False

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
        except FileNotFoundError as e:
            self.errlog.write("[?]" + str(e) + ", " + remotepath + "\n")
        else:
            for fileattr in listdir_attr:
                if suffix is not None and \
                        not stat.S_ISDIR(fileattr.st_mode) and \
                        os.path.splitext(fileattr)[-1][1:] != suffix:
                    continue
                # rpath = remotepath + '\\' + fileattr.filename # Windows
                rpath = os.path.join(remotepath, fileattr.filename) # Linux
                lpath = os.path.join(localpath, fileattr.filename)
                if stat.S_ISREG(fileattr.st_mode):
                    if os.path.exists(lpath): 
                        continue
                    try:
                        self.sftp.get(rpath, lpath)
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
                elif stat.S_ISLNK(fileattr.st_mode):
                    try:
                        realpath = self.sftp.readlink(rpath)
                    except PermissionError as e:
                        self.errlog.write("[!]" + str(e) +
                              ", you do not have permission to read this link:%s\n" %
                              rpath)
                    except FileNotFoundError as e:
                        self.errlog.write("[!]" + str(e) + ", %s\n" % rpath)
                    else:
                        try:
                            os.symlink(realpath, lpath)
                        except: # continue whether the link exists or not
                            pass
                        else:
                            # Zipfile does not currently support adding link files
                            # self.zipfile.write(realpath)
                            pass
                    continue
                elif stat.S_ISSOCK(fileattr.st_mode):
                    self.errlog.write("[-] socket file: %s\n" % rpath)
                    continue
                elif stat.S_ISCHR(fileattr.st_mode):
                    self.errlog.write("[-] character device: %s\n" % rpath)
                    continue
                elif stat.S_ISFIFO(fileattr.st_mode):
                    self.errlog.write("[-] pipeline file: %s\n" % rpath)
                    continue
                elif stat.S_ISBLK(fileattr.st_mode):
                    self.errlog.write("[-] block file: %s\n" % rpath)
                    continue
                elif stat.S_ISDIR(fileattr.st_mode):
                    if not os.path.exists(lpath):
                        os.mkdir(lpath)
                    self._download(rpath, lpath, suffix)

                try:
                    # set attributes for local file except symlink file
                    os.chmod(lpath, fileattr.st_mode)
                    os.chown(lpath, fileattr.st_uid, fileattr.st_gid)
                    os.utime(lpath, (fileattr.st_atime, fileattr.st_mtime))
                except:
                    self.errlog.write("[-] permission setting failed, local path: %s\n" % lpath)
                if self.zipfile is not None:
                    self.zipfile.write(lpath)
    
    def download(self, remotepath = "/", localpath = ".", suffix = None, zfile = None):
        # 检测本地root权限
        if not is_admin():
            print("Please run it as sudo or root user!")
            exit()
        
        # 检测远程root权限
        if not self._is_admin():
            print("Waring: The user %s is not the root user of %s, some files will not have permission to download!" % (self.username, self.ip + ':' + str(self.port)))
        
        print("Start download...")
        if zfile is not None:
            self.zipfile = zipfile.ZipFile(zfile, mode = 'a')
        
        self._download(remotepath, localpath, suffix)
        
        if zfile is not None:
            self.zipfile.close()
        print("Finish download!")

    def download_disk(self, remotepath = '/dev/sda', localpath = './sda.img', begin = 0, count = 1):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname = self.ip, port = self.port, 
                    username = self.username, password = self.password)
        command = "dd if=" + remotepath
        command += " of=" + localpath
        command += " skip=" + str(begin)
        command += " count=" + str(count)

        stdin, stdout, stderr = ssh.exec_command(command)
        res = stdout.read()
        ssh.close()

        print(res)



        
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

    parser.add_argument('-D', '--dd', help = "download remote hard disk via commmand 'dd'")

    parser.add_argument('-b', '--begin',
            default = 0,
            help = "if -D mode is specified, specify whick block to start downloading from hard disk")

    parser.add_argument('-c', '--count',
            default = 1,
            help = "if -D mode is specified, specify how many bocks should be downloaded")

    args = parser.parse_args()
    if args.password is None:
        password = getpass.getpass("password:")
    else:
        password = args.password
    
    rfs = RootfsDownloader(
            args.login, password, 
            args.hostip, args.port,
            errlog = args.errlog)

    if args.dd is None:
        rfs.download(args.remote, args.directory, zfile = args.zipfile)
    else:
        rfs.download(args.remote, args.directory, args.begin, args.count)
