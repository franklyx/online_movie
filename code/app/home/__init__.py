#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Created by FrankLyx on 2017/11/28
Desc : 注意这里顺序不能调换
"""
from flask import Blueprint

home = Blueprint("home", __name__)

import app.home.views
