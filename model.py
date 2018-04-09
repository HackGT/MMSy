from datetime import datetime
from enum import IntEnum, unique

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import Boolean, Column, Integer, DateTime, Enum, Text, ForeignKey

DEFAULT_STYLE = '__default__'

Base = declarative_base()

@unique
class TCStatus(IntEnum):
    NOTHING = 0
    SENT = 1
    AGREED = 2

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    phone_number = Column(Text, unique=True, nullable=False)
    tc_status = Column(Enum(TCStatus), nullable=False)

    pictures = relationship('Picture', backref='user', lazy=True)

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
    def get_or_create_user(session, phone_number):
        """
        Retrieves the user with the given phone number from the
        If none is present, a new user will be created (not yet saved to db).
        """
        user = session.query(User).filter_by(phone_number=phone_number).first()
        if user is None:
            user = User(phone_number=phone_number, tc_status=TCStatus.NOTHING)
            session.add(user)
        return user

    def __repr__(self):
        return '<User %r %r>' % (self.phone_number, self.tc_status)

class Picture(Base):
    __tablename__ = 'picture'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    source_url = Column(Text, nullable=False)
    create_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    message_sid = Column(Text, nullable=False)
    converted_url = Column(Text)
    converted_time = Column(DateTime)
    failed = Column(Boolean)
    style = Column(Text)

    @property
    def converted(self):
        assert ((not self.converted_url) == (not self.converted_time)) and not (self.converted_url and self.failed)
        return bool(self.converted_url) or self.failed

    def add_converted_info(self, converted_url, converted_time=None, style=None):
        self.converted_url = converted_url
        self.converted_time = converted_time or datetime.now()
        self.style = style or self.style

    def __repr__(self):
        return '<Picture %r, converted=%r>' % (self.source_url, self.converted_url is not None)

    @staticmethod
    def get_all_pending(session):
        return session.query(Picture)\
                      .filter_by(converted_url=None)\
                      .filter((Picture.failed != True) | (Picture.failed == None))\
                      .join(Picture.user)\
                      .filter_by(tc_status=TCStatus.AGREED)\
                      .all()
