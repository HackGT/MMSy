import os

class MissingEnvVarError(KeyError):
    pass

POSTGRES_URL = os.environ.get('POSTGRES_URL', 'postgres://localhost/')
UNIQUE_APP_ID = os.environ.get('UNIQUE_APP_ID', 'MMSy')
try:
    TWILIO_SERVICE_SID = os.environ['TWILIO_SERVICE_SID']
    TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
    TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
    BACKEND_API_URL = os.environ['BACKEND_API_URL']
except KeyError as e:
    raise MissingEnvVarError(e)

with open('user-agreement.txt', 'r') as f:
    TC_AGREEMENT_TEXT = f.read()
