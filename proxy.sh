#########################################################################
# File Name: /home/midcheck/Script/proxy.sh
# Author: MidCHeck
# mail: mc.xin@foxmail.com
# Created Time: 2020年02月23日 星期日 22时39分51秒
#########################################################################
#!/bin/env bash

if [ $1 == "unset" ] 2> /dev/null ; then
	echo "取消代理..."
	unset http_proxy
	unset https_proxy
	unset ftp_proxy
	unset all_proxy
	exit;
elif test -z "$2"; then
	if test -z "$1"; then
		echo "输入ip"
	else
		echo "输入端口"
	fi
	echo "Usage: proxy [unset | ip] [port]"
	exit;
else
	echo "添加代理 http://$1:$2/"
	export http_proxy=http://$1:$2/
	export https_proxy=http://$1:$2/
	export ftp_proxy=http://$1:$2/
	export all_proxy=http://$1:$2/
fi
