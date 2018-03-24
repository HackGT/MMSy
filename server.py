from collections import namedtuple
from datetime import datetime
from queue import Queue
import threading

from flask import Flask, request

import config
from model import User, Picture, TCStatus
from worker import NUM_WORKERS, worker

app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_object(config.load_config())

ConvertRequest = namedtuple('ConvertRequest', ('phone', 'picture'))
# Queue of ConvertRequest
queue = Queue()

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/incoming", methods=["POST"])
def handle_incoming():
    message_sid = request.form['MessageSid']
    from_number = request.form['From']
    num_media = int(request.POST.get('NumMedia', 0))

    user = User.get_or_create_user(from_number)

    if num_media == 0:
        message = request.form.get('Body', None)
        handle_incoming_sms(user, message_sid, message)
    else:
        media_files = [
            (request.POST.get("MediaUrl{}".format(i), ''),
             request.POST.get("MediaContentType{}".format(i), ''))
            for i in range(0, num_media)
        ]
        handle_incoming_mms(user, message_sid, media_files)

def handle_incoming_sms(user, message_sid, message):
    if user.tc_status is TCStatus.SENT:
        if message is not None and message.upper() is 'YES':
            user.tc_status = TCStatus.AGREED
            user.save()
            for pending in user.pending:
                req = ConvertRequest(user.phone, pending)
                queue.put(req)
    elif user.tc_status is TCStatus.NOTHING:
        user.send_tc()

def handle_incoming_mms(user, message_sid, media_files):
    for media_file in media_files:
        picture = Picture(media_file, datetime.now(), message_sid)
        user.add_pending(picture)
        if user.tc_status is TCStatus.AGREED:
            req = ConvertRequest(from_number, picture)
            queue.put(req)
        # TODO upload pictures to google cloud storage and delete from twilio servers

def start_workers(num_workers, queue):
    threads = []
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(queue,))
        t.start()
        threads.append(t)
    return threads

start_workers(NUM_WORKERS, queue)
