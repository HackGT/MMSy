from twilio.rest import Client as _twilioClient

from config import TWILIO_SERVICE_SID, TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN

class _twilioClientWrapper(_twilioClient):
    def __init__(self, account_sid, auth_token, service_sid):
        super(_twilioClientWrapper, self).__init__(account_sid, auth_token)
        self.service_sid = service_sid

    def send_message(self, phone_number, body=None, media_url=None):
        assert body is not None or media_file is not None
        return self.messages.create(
            phone_number,
            messaging_service_sid=self.service_sid,
            body=body,
            media_url=media_url
        )

TwilioClient = _twilioClientWrapper(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_SERVICE_SID)
