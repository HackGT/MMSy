from datetime import datetime
from enum import IntEnum, unique

import pymongo

DEFAULT_STYLE = 'default'

@unique
class TCStatus(IntEnum):
    NOTHING = 0
    SENT = 1
    AGREED = 2

class User:
    def __init__(self, phone_number, oid=None, tc_status=TCStatus.NOTHING, pictures=[]):
        self.phone_number = phone_number
        self._oid = oid
        self.tc_status = tc_status
        self.pictures = pictures

    @property
    def pending(self):
        return list(filter(lambda p: not p.converted, self.pictures))

    @property
    def finished(self):
        return list(filter(lambda p: p.converted), self.pictures)

    def add_pending(self, p):
        assert not p.converted
        self.pictures.append(p)
        self.save()

    def send_tc(self):
        # TODO send terms and conditions with twilio api
        self.tc_status = TCStatus.SENT
        self.save()

    def save(self):
        """
        Save current user to database
        """
        pass

    @staticmethod
    def get_or_create_user(phone_number):
        """
        Retrieves the user with the given phone number from the db.
        If none is present, a new user will be created (not yet saved to db).
        """
        # TODO do db query
        return User(phone_number)

class Picture:
    def __init__(self, source_url, create_time, message_sid, converted_url=None, converted_time=None, style=DEFAULT_STYLE):
        self.source = source_url
        self.create_time = create_time
        self.message_sid = message_sid
        self.style = style
        assert (converted_url is None) == (converted_time is None)
        self.converted = converted_url
        self.converted_time = converted_time

    def convert(self, converted_url, converted_time=None, style=None):
        self.converted = converted_url
        self.converted_time = converted_time or datetime.now()
        self.style = style or self.style
