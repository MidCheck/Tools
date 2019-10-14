#! /usr/bin/env python
# -*- coding: utf-8 -*-
import paramiko

# 测试机Metasploitable
ip = "192.168.217.133"
port = 22
user = "msfadmin"
password = "msfadmin"
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# 建立连接
ssh.connect(ip, port, user, password, timeout = 10)

# 输入linux命令
stdin, stdout, stderr = ssh.exec_command("ls -l /")

# 输出命令执行结果
result = stdout.read()
print(result)

# 关闭连接
ssh.close()
