from datetime import datetime
from enum import IntEnum, unique

from db import db

DEFAULT_STYLE = '__default__'

@unique
class TCStatus(IntEnum):
    NOTHING = 0
    SENT = 1
    AGREED = 2

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.Text, unique=True, nullable=False)
    tc_status = db.Column(db.Enum(TCStatus), nullable=False)
    pictures = db.relationship('Picture', backref='user', lazy=True)

    @property
    def pending(self):
        return list(filter(lambda p: not p.converted, self.pictures))

    @property
    def finished(self):
        return list(filter(lambda p: p.converted), self.pictures)

    def add_pending(self, p):
        assert not p.converted
        self.pictures.append(p)

    @staticmethod
    def get_or_create_user(phone_number):
        """
        Retrieves the user with the given phone number from the db.
        If none is present, a new user will be created (not yet saved to db).
        """
        user = User.query.filter_by(phone_number=phone_number).first()
        if user is None:
            user = User(phone_number=phone_number, tc_status=TCStatus.NOTHING)
            db.session.add(user)
        return user

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<User %r %r>' % (self.phone_number, self.tc_status)

class Picture(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    source_url = db.Column(db.Text, nullable=False)
    create_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    message_sid = db.Column(db.Text, nullable=False)
    converted_url = db.Column(db.Text)
    converted_time = db.Column(db.DateTime)
    failed = db.Column(db.Boolean)
    style = db.Column(db.Text)

    @property
    def converted(self):
        assert ((not self.converted_url) == (not self.converted_time)) and not (self.converted_url and self.failed)
        return bool(self.converted_url) or self.failed

    def add_converted_info(self, converted_url, converted_time=None, style=None):
        self.converted_url = converted_url
        self.converted_time = converted_time or datetime.now()
        self.style = style or self.style
        self.save()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return '<Picture %r, converted=%r>' % (self.source_url, self.converted_url is not None)

    @staticmethod
    def get_all_pending():
        return Picture.query\
                      .filter_by(converted_url=None)\
                      .filter((Picture.failed != True) | (Picture.failed == None))\
                      .join(Picture.user)\
                      .filter_by(tc_status=TCStatus.AGREED)\
                      .all()
