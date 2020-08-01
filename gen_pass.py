#! /usr/bin/env python
# -*- coding: utf-8 -*-
from random import choice
import string
import sys

def gen_password(length=8, chars=string.ascii_letters+string.digits):
    return ''.join([choice(chars) for i in range(length)])

if __name__ == '__main__':
    if not len(sys.argv) < 2:
        if isinstance(sys.argv[1], str):
            print(gen_password(int(sys.argv[1])))
            sys.exit()

    print("Usage: python3 gen_pass LEN")
