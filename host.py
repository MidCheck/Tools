#! /usr/bin/python3
#
# 获取github上的hosts文件，防止部分域名的DNS污染
#

import requests
url = "https://raw.githubusercontent.com/googlehosts/hosts/master/hosts-files/hosts"
resp = requests.get(url)

outfile = open("hosts", "w")

if(outfile):
    if resp.status_code == 200:
        outfile.write(resp.text)
        print("[+] 获取hosts完毕")
    else:
        print("[-] 获取hosts失败!")
else:
    print("[-] 打开文件失败!")

outfile.close()
