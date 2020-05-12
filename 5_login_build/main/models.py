from main import db
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin


class Player(db.Model, UserMixin):
    user_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    # ゲーム終了時にリセット
    is_alive = db.Column(db.Boolean, default=True)
    role = db.Column(db.Text, default="村人")
    # 毎回リセットするパラメータ
    ## 受動系パラメータ
    votes = db.Column(db.Integer, default=0)
    is_protected = db.Column(db.Boolean, default=False)
    bitten = db.Column(db.Integer, default=0)
    ## 権利系パラメータ
    can_vote = db.Column(db.Boolean, default=True)
    can_bite = db.Column(db.Boolean, default=False)
    can_protect = db.Column(db.Boolean, default=False)
    can_forecast = db.Column(db.Boolean, default=False)
    can_confirm = db.Column(db.Boolean, default=False)
    # 以下ログイン用
    user_password = db.Column(db.Text)
    group_id = db.Column(db.Integer)
    group_password = db.Column(db.Text)
    # グループstatus管理
    is_got_together = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return "<Entry user_id={} name={!r}>".format(self.user_id, self.name)


class Var(db.Model):
    var_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    value = db.Column(db.Integer, default=0)   
    # グループ管理
    group_id = db.Column(db.Integer)


def init():
    db.create_all()
