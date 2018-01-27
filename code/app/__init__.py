#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Created by FrankLyx on 2017/11/28
Desc :
"""
import os
import pymysql
import logging.config
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask.ext.redis import FlaskRedis

# flask config
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'mysql+pymysql://root:admin@10.9.36.126:3306/movie'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config["SECRET_KEY"] = "8cb29f459108417b8513d397b8e0c83a"
app.config["REDIS_URL"] = "redis://10.9.36.126:6379/0"
app.config["UP_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/")
app.config["FC_DIR"] = os.path.join(os.path.abspath(os.path.dirname(__file__)), "static/uploads/users/")
app.debug = True
db = SQLAlchemy(app)
rd = FlaskRedis(app)

# logging
handler = RotatingFileHandler('/home/logs/flask.log', encoding='UTF-8', maxBytes=1024 * 1024, mode="a")
handler.setLevel(logging.DEBUG)
logging_format = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(filename)s - %(funcName)s - %(lineno)s - %(message)s')
handler.setFormatter(logging_format)
app.logger.addHandler(handler)

# blueprint
from app.home import home as home_blueprint
from app.admin import admin as admin_blueprint

app.register_blueprint(home_blueprint)
app.register_blueprint(admin_blueprint, url_prefix="/admin")


@app.errorhandler(404)
def page_not_found(error):
    return render_template("home/404.html"), 404
