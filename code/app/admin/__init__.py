#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Created by FrankLyx on 2017/11/28
Desc :
"""
from flask import Blueprint

admin = Blueprint("admin", __name__)

import app.admin.views
