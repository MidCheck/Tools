#! /usr/bin/python
'''
 获取github上的hosts文件，防止部分域名的DNS污染
'''
import requests
url = "https://coding.net/u/scaffrey/p/hosts/git/raw/master/hosts-files/hosts"
resp = requests.get(url)

outfile = open("hosts", "w")

if(outfile):
    if resp.status == 200:
        outfile.write(resp.text)
        print("[+] 获取hosts完毕")
    else:
        print("[-] 获取hosts失败!")
else:
    print("[-] 打开文件失败!")

outfile.close()
