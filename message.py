from twilio.twiml.messaging_response import MessagingResponse

# TODO consolidate with TwilioClient
def create_message(message):
    resp = MessagingResponse()
    resp.message(message)
    return resp

with open('user-agreement.txt', 'r') as f:
    TC_AGREEMENT_TEXT = f.read()

TC_MESSAGE = create_message(TC_AGREEMENT_TEXT)
