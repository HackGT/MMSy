from collections import namedtuple
from datetime import datetime
from queue import Queue
import threading

from flask import Flask, request, g
from twilio.twiml.messaging_response import MessagingResponse

import config
from logger import logger
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.POSTGRES_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

with app.app_context():
    from db import db, migrate
    from model import User, Picture, TCStatus
from message import create_message, TC_MESSAGE
from worker import NUM_WORKERS, worker

queue = Queue()
def enqueue(picture):
    queue.put(picture)

def enqueue_all(pictures):
    for picture in pictures:
        enqueue(picture)

@app.route("/")
def hello():
    return "Hello World!"

@app.route("/incoming", methods=["POST"])
def handle_incoming():
    message_sid = request.form['MessageSid']
    from_number = request.form['From']
    num_media = int(request.form.get('NumMedia', 0))
    message = request.form.get('Body', None)

    user = User.get_or_create_user(from_number)

    def log(message='', event=None, **kwargs):
        extra = {
            'user_id': user.id,
            'tc_status': user.tc_status,
            'message_sid': message_sid
        }
        if event is not None:
            extra[event] = True
        extra.update(kwargs)
        logger.info(message, extra=extra)

    log('Received message', event='received_message')

    if num_media > 0:
        media_files = [
            (request.form.get("MediaUrl{}".format(i), ''),
             request.form.get("MediaContentType{}".format(i), ''))
            for i in range(0, num_media)
        ]
        for media_file in media_files:
            # TODO upload pictures to google cloud storage and delete from twilio servers
            picture = Picture(
                source_url=media_file,
                create_time=datetime.now(),
                message_sid=message_sid
            )
            user.add_pending(picture)

    response = None

    if user.tc_status is TCStatus.NOTHING:
        log('New user, sending terms and conditions', 'send_tc')
        response = TC_MESSAGE
        user.tc_status = TCStatus.SENT

    elif user.tc_status is TCStatus.SENT:
        if message is not None:
            if message.upper() == 'YES':
                log('Agreed to terms and conditions', 'tc_agreed')
                user.tc_status = TCStatus.AGREED
                response = 'Thank you for agreeing to the terms and conditions.'
                if len(user.pending) > 0:
                    response += " Processing your {} picture(s) now".format(len(user.pending))
                    enqueue_all(user.pending)
                else:
                    response += " You can now send me pictures to convert"

        else:
            log('Remind to agree to terms and conditions', 'tc_remind')
            response = 'You must agree to the terms and conditions by responding YES before continuing.'
            if len(user.pending) > 0:
                response += " You have {} pictures pending".format(len(user.pending))
            response = ' '.join(response)

    else:
        assert user.tc_status is TCStatus.AGREED
        if num_media > 0:
            log('Received new pictures', 'more_pictures', num_new_pictures=num_media)
            response = "Got it! Hard at work processing {} picture(s) for you!".format(num_media)
            enqueue_all(user.pending)

    user.save()

    if not response:
        response = "Sorry, I didn't understand that!"
    if isinstance(response, str):
        response = create_message(response)
    return str(response)

def start_workers(num_workers, queue):
    threads = []
    for i in range(num_workers):
        t = threading.Thread(target=worker, args=(queue,))
        t.start()
        threads.append(t)
    return threads

if __name__=='__main__':
    # TODO Fix this!
    start_workers(NUM_WORKERS, queue)
    for picture in Picture.get_all_pending():
        enqueue(picture)
