import config

from flask import Flask

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_object(config.load_config())

@app.route("/")
def hello():
    return "Hello World!"
