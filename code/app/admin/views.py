#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
Created by FrankLyx on 2017/11/28
Desc :
"""
import os
import uuid
import datetime
from functools import wraps

from . import admin
from app import db, app
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, AuthForm, RoleForm, AdminForm, PwdForm
from app.models import Admin, Adminlog, Tag, Movie, Preview, User, Comment, Moviecol, Oplog, Userlog, Auth, Role
from flask import render_template, flash, redirect, url_for, session, request, abort
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash


#  登陆检测装饰器
def admin_login_req(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


# 权限控制装饰器
def admin_auth(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin = Admin.query.join(
            Role
        ).filter(
            Role.id == Admin.role_id,
            Admin.id == session["admin_id"]
        ).first()
        auths = admin.role.auths
        auths = list(map(lambda v: int(v), auths.split(",")))
        auth_list = Auth.query.all()
        urls = [u.url for u in auth_list if u.id in auths]
        if str(request.url_rule) not in urls:
            abort(404)
        return f(*args, **kwargs)

    return decorated_function


#  修改安全的文件名
# 利用时间加uuid命名文件
def change_filename(filename):
    if filename.find(".") == -1:
        filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + "." + filename
    else:
        fileinfo = os.path.splitext(filename)
        filename = datetime.datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + fileinfo[-1]
    return filename


@admin.route("/")
@admin_login_req
def index():
    return render_template("admin/index.html")


# 管理员登陆
@admin.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data["account"]).first()
        if not admin.check_pwd(data["pwd"]):
            flash("密码错误", "err")
            return redirect(url_for("admin.login"))
        # logging
        app.logger.info(data["account"])
        session["admin"] = data["account"]
        session["admin_id"] = admin.id
        adminlog = Adminlog(
            admin_id=admin.id,
            ip=request.remote_addr
        )
        db.session.add(adminlog)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("admin.index"))
    return render_template("admin/login.html", form=form)


# 管理员退出
@admin.route("/logout")
@admin_login_req
def logout():
    # session就是一个字典
    session.pop("admin", None)
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


# 修改密码
@admin.route("/pwd/", methods=["GET", "POST"])
@admin_login_req
def pwd():
    form = PwdForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session["admin"]).first()
        admin.pwd = generate_password_hash(data["new_pwd"])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功", "ok")
        return redirect(url_for("admin.logout"))
    return render_template("admin/pwd.html", form=form)


#  添加标签
@admin.route("/tag/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag == 1:
            flash("名称已经存在!", "err")
            return redirect(url_for("admin.tag_add"))
        tag = Tag(name=data["name"])
        db.session.add(tag)
        db.session.commit()
        flash("标签添加成功", "ok")
        return redirect(url_for("admin.tag_add"))
    return render_template("admin/tag_add.html", form=form)


# 编辑标签
@admin.route("/tag/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def tag_edit(id=None):
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data["name"]).count()
        if tag.name != data["name"] and tag_count == 1:
            flash("名称已经存在！", "err")
            return redirect(url_for('admin.tag_edit'), id=id)
        tag.name = data["name"]
        db.session.add(tag)
        db.session.commit()
        flash("修改标签成功！", "ok")
        redirect(url_for('admin.tag_edit', id=id))
    return render_template("admin/tag_edit.html", form=form, tag=tag)


# 删除标签
@admin.route("/tag/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def tag_del(id=None):
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功！", "ok")
    return redirect(url_for('admin.tag_list', page=1))


# 标签列表
@admin.route("/tag/list/<int:page>/", methods=["GET"])
@admin_login_req
def tag_list(page=None):
    if page is None:
        page = 1
    page_data = Tag.query.order_by(
        Tag.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/tag_list.html", page_data=page_data)


# 电影添加
@admin.route("/movie/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        # 对title进行验证
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        # 保证标题的唯一性
        if movie_count == 1:
            flash("片名已存在", "err")
            return redirect(url_for("admin.movie_edit", id=id))
        # secure_filename会自动过滤非ASCII字符
        file_url = secure_filename(form.url.data.filename)
        log_url = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
        url = change_filename(file_url)
        logo = change_filename(log_url)
        form.url.data.save(app.config["UP_DIR"] + url)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        movie = Movie(
            title=data["title"],
            url=url,
            info=data["info"],
            logo=logo,
            star=int(data["star"]),
            playnum=0,
            commentnum=0,
            tag_id=int(data["tag_id"]),
            area=data["area"],
            release_time=data["release_time"],
            length=data["length"]
        )
        db.session.add(movie)
        db.session.commit()
        flash("添加电影成功", "ok")
        return redirect(url_for("admin.movie_add"))
    return render_template("admin/movie_add.html", form=form)


# 电影列表
@admin.route("/movie/list/<int:page>/", methods=["GET"])
@admin_login_req
def movie_list(page=None):
    if page is None:
        page = 1
    page_data = Movie.query.order_by(
        Movie.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/movie_list.html", page_data=page_data)


# 编辑电影
@admin.route("/movie/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def movie_edit(id=None):
    form = MovieForm()
    # 在修改中允许不对之前的封面和视频进行修改
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.get_or_404(int(id))
    if request.method == "GET":
        # 设置非input标签的属性值
        form.info.data = movie.info
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        # 保证标题的唯一性
        if movie_count == 1 and movie.title != data['title']:
            flash("片名已存在", "err")
            return redirect(url_for("admin.movie_edit", id=id))
        # 保证url的正确性,保存上传的视频
        if form.url.data.filename != "":
            file_url = secure_filename(form.url.data.filename)
            movie.url = change_filename(file_url)
            form.url.data.save(app.config["UP_DIR"] + movie.url)
        # 保证logo的正确性,保存上传的封面
        if form.logo.data.filename != "":
            file_logo = secure_filename(form.logo.data.filename)
            movie.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + movie.logo)

        movie.star = data["star"]
        movie.tag_id = data["tag_id"]
        movie.info = data["info"]
        movie.title = data["title"]
        movie.area = data["area"]
        movie.length = data["length"]
        movie.release_time = data["release_time"]
        db.session.add(movie)
        db.session.commit()
        flash("修改电影成功", "ok")
        return redirect(url_for("admin.movie_edit", id=id))
    return render_template("admin/movie_edit.html", form=form, movie=movie)


# 删除电影
@admin.route("/movie/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def movie_del(id):
    movie = Movie.query.get_or_404(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash("删除电影成功", "ok")
    return redirect(url_for("admin.movie_list", page=1))


# 添加预告
@admin.route("/preview/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        preview_count = Preview.query.filter_by(title=data["title"]).count()
        if preview_count == 1:
            flash("预告名已存在", "err")
            return redirect(url_for("admin.preview_add"))
        file_logo = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
        logo = change_filename(file_logo)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        preview = Preview(
            title=data["title"],
            logo=logo
        )
        db.session.add(preview)
        db.session.commit()
        flash("预告添加成功")
        return redirect(url_for("admin.preview_add"))
    return render_template("admin/preview_add.html", form=form)


# 获取预告列表
@admin.route("/preview/list/<int:page>/", methods=["GET"])
@admin_login_req
def preview_list(page=None):
    if page == None:
        page = 1
    page_data = Preview.query.order_by(
        Preview.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/preview_list.html", page_data=page_data)


# 删除预告
@admin.route("/preview/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def preview_del(id=None):
    perview = Preview.query.get_or_404(int(id))
    db.session.delete(perview)
    db.session.commit()
    flash("删除预告成功", "ok")
    return redirect(url_for("admin.preview_list", page=1))


# 修改预告
@admin.route("/preview/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def preview_edit(id=None):
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.get_or_404(int(id))
    if request.method == "GET":
        form.title.data = preview.title
    if form.validate_on_submit():
        data = form.data
        if form.logo.data.filename != "":
            file_logo = secure_filename(form.logo.data.filename)
            preview.logo = change_filename(file_logo)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)
        preview.title = data["title"]
        db.session.add(preview)
        db.session.commit()
        flash("修改预告成功", "ok")
        return redirect(url_for("admin.preview_edit", id=id))
    return render_template("admin/preview_edit.html", form=form, preview=preview)


# 会员列表
@admin.route("/user/list/<int:page>/", methods=["GET"])
@admin_login_req
def user_list(page=None):
    if page is None:
        page = 1
    page_data = User.query.order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/user_list.html", page_data=page_data)


# 删除会员
@admin.route("/user/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def user_del(id=None):
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash("删除会员成功！", "ok")
    return redirect(url_for('admin.user_list', page=1))


# 查看会员
@admin.route("/user/view/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def user_view(id=None):
    user = User.query.get_or_404(int(id))
    return render_template("admin/user_view.html", user=user)


# 评论列表
@admin.route("/comment/list/<int:page>/", methods=["GET"])
@admin_login_req
def comment_list(page=None):
    # TODO 当有数据后来讨论filter存在的必要性
    if page is None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id
    ).order_by(
        Comment.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/comment_list.html", page_data=page_data)


# 删除评论
@admin.route("/comment/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def comment_del(id=None):
    comment = Comment.query.get_or_404(int(id))
    db.session.delete(comment)
    db.session.commit()
    flash("删除评论成功！", "ok")
    return redirect(url_for('admin.comment_list', page=1))


# 收藏列表
@admin.route("/moviecol/list/<int:page>/", methods=["GET"])
@admin_login_req
def moviecol_list(page=None):
    if page is None:
        page = 1
    page_data = Moviecol.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Moviecol.movie_id,
        User.id == Moviecol.user_id
    ).order_by(
        Moviecol.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/moviecol_list.html", page_data=page_data)


# 删除收藏
@admin.route("/moviecol/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def moviecol_del(id=None):
    moviecol = Comment.query.get_or_404(int(id))
    db.session.delete(moviecol)
    db.session.commit()
    flash("删除评论成功！", "ok")
    return redirect(url_for('admin.moviecol_del', page=1))


# 操作日志
@admin.route("/oplog/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def oplog_list(page=None):
    if page is None:
        page = 1
    page_data = Oplog.query.join(
        Admin
    ).filter(
        Admin.id == Oplog.admin_id,
    ).order_by(
        Oplog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/oplog_list.html", page_data=page_data)


# 管理员登陆日志
@admin.route("/adminloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def adminloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Adminlog.query.join(
        Admin
    ).filter(
        Admin.id == Adminlog.admin_id
    ).order_by(
        Adminlog.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/adminloginlog_list.html", page_data=page_data)


# 会员登陆日志
@admin.route("/userloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def userloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.join(
        User
    ).filter(
        User.id == Userlog.user_id
    ).order_by(
        User.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/userloginlog_list.html", page_data=page_data)


# 权限添加
@admin.route("/auth/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def auth_add():
    form = AuthForm()
    if form.validate_on_submit():
        data = form.data
        auth = Auth(
            name=data["name"],
            url=data["url"]
        )
        db.session.add(auth)
        db.session.commit()
        flash("添加权限成功", "ok")
        return redirect(url_for("admin.auth_add"))
    return render_template("admin/auth_add.html", form=form)


# 权限列表
@admin.route("/auth/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def auth_list(page=None):
    if page is None:
        page = 1
    page_data = Auth.query.order_by(
        Auth.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/auth_list.html", page_data=page_data)


# 权限删除
@admin.route("/auth/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def auth_del(id=None):
    auth = Auth.query.get_or_404(int(id))
    db.session.delete(auth)
    db.session.commit()
    flash("权限标签删除成功", "ok")
    return redirect(url_for("admin.auth_list", page=1))


# 编辑权限
@admin.route("/auth/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def auth_edit(id=None):
    form = AuthForm()
    auth = Auth.query.get_or_404(int(id))
    if form.validate_on_submit():
        data = form.data
        auth.url = data["url"]
        auth.name = data["name"]
        db.session.add(auth)
        db.session.commit()
        flash("权限添加成功", "ok")
        return redirect(url_for("admin.auth_edit", id=id))
    return render_template("admin/auth_edit.html", form=form, auth=auth)


# 添加角色
@admin.route("/role/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_add():
    form = RoleForm()
    # 解决数据更新后，下拉框不刷新的问题
    form.auths.choices = [(v.id, v.name) for v in Auth.query.all()]
    if form.validate_on_submit():
        data = form.data
        role = Role(
            name=data["name"],
            auths=",".join(map(lambda v: str(v), data["auths"]))
        )
        db.session.add(role)
        db.session.commit()
        flash("添加角色成功！", "ok")
    return render_template("admin/role_add.html", form=form)


# 编辑角色
@admin.route("/role/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def role_edit(id=None):
    form = RoleForm()
    # 解决数据更新后，下拉框不刷新的问题
    form.auths.choices = [(v.id, v.name) for v in Auth.query.all()]
    role = Role.query.get_or_404(int(id))
    if request.method == "GET":
        auths = role.auths
        if auths is "":
            form.auths.data = []
        else:
            form.auths.data = list(map(lambda v: int(v), auths.split(",")))
    if form.validate_on_submit():
        data = form.data
        role.name = data["name"]
        role.auths = ",".join(map(lambda v: str(v), data["auths"]))
        db.session.add(role)
        db.session.commit()
        flash("修改角色成功！", "ok")
    return render_template("admin/role_edit.html", form=form, role=role)


# 角色列表
@admin.route("/role/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def role_list(page=None):
    if page is None:
        page = 1
    page_data = Role.query.order_by(
        Role.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/role_list.html", page_data=page_data)


# 删除角色
@admin.route("/role/del/<int:id>/", methods=["GET"])
@admin_login_req
@admin_auth
def role_del(id=None):
    role = Role.query.filter_by(id=id).first_or_404()
    db.session.delete(role)
    db.session.commit()
    flash("删除角色成功！", "ok")
    return redirect(url_for('admin.role_list', page=1))


# 添加管理员
@admin.route("/admin/add/", methods=["GET", "POST"])
@admin_login_req
@admin_auth
def admin_add():
    form = AdminForm()
    # 解决数据更新后，下拉框不刷新的问题
    form.role_id.choices = [(v.id, v.name) for v in Role.query.all()]
    from werkzeug.security import generate_password_hash
    if form.validate_on_submit():
        data = form.data
        admin = Admin(
            name=data["name"],
            pwd=generate_password_hash(data["pwd"]),
            role_id=data["role_id"],
            is_super=1
        )
        db.session.add(admin)
        db.session.commit()
        flash("添加成功", "ok")
        return redirect(url_for("admin.admin_add"))
    return render_template("admin/admin_add.html", form=form)


# 管理员列表
@admin.route("/admin/list/<int:page>/", methods=["GET"])
@admin_login_req
@admin_auth
def admin_list(page=None):
    if page is None:
        page = 1
    page_data = Admin.query.join(
        Role
    ).filter(
        Admin.role_id == Role.id
    ).order_by(
        Admin.addtime.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/admin_list.html", page_data=page_data)
