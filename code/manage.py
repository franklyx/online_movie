#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Created by FrankLyx on 2017/11/28
Desc :
"""
from flask_script import Manager
from app import app

manager = Manager(app)

if __name__ == '__main__':
    manager.run()
