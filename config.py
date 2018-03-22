import os

class MissingEnvVarError(KeyError):
    pass

def load_config():
    conf = {}
    conf['MONGO_URL'] = os.environ.get('MONGO_URL', 'mongodb://localhost/')
    conf['UNIQUE_APP_ID'] = os.environ.get('UNIQUE_APP_ID', 'MMSy')
    try:
        conf['GCLOUD_API_KEY'] = os.environ['GCLOUD_API_KEY']
        conf['TWILIO_API_KEY'] = os.environ['TWILIO_API_KEY']
        conf['BACKEND_API_URL'] = os.environ['BACKEND_API_URL']
    except KeyError as e:
        raise MissingEnvVarError(e)

    return conf
