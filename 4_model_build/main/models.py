from main import db
from flask_sqlalchemy import SQLAlchemy


class Entry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    text = db.Column(db.Text)

    def __repr__(self):
        return "<Entry id={} title={!r}>".format(self.id, self.title)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text)
    is_alive = db.Column(db.Boolean, default=True)
    role = db.Column(db.Text)
    votes = db.Column(db.Integer, default=0)

    def __repr__(self):
        return "<Entry id={} name={!r}>".format(self.id, self.name)


def init():
    db.create_all()
