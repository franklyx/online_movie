#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Created by FrankLyx on 2017/11/28
Desc :
"""
import os
from flask_script import Manager
from app import app

manager = Manager(app)

if __name__ == '__main__':
    # 创建日志文件夹
    if not os.path.exists("/home/logs"):
        os.mkdir("/home/logs")
    manager.run()
