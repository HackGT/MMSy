import asyncio
from datetime import datetime
import functools

from aiohttp.web import RouteTableDef, Response
from twilio.twiml.messaging_response import MessagingResponse

from logger import logger
from model import User, Picture, TCStatus
from worker import process_pictures, test

routes = RouteTableDef()

@routes.get('/')
async def hello(request):
    loop = request.app['worker']['loop']
    # asyncio.run_coroutine_threadsafe(test(), loop)
    await test()
    return Response(text="Hello World!")

@routes.post('/incoming')
async def handle_incoming(request):
    form = await request.post()
    message_sid = form['MessageSid']
    from_number = form['From']
    num_media = int(form.get('NumMedia', 0))
    message = form.get('Body', None)

    session = request.app['session']()
    user = User.get_or_create_user(session, from_number)

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
            (form.get("MediaUrl{}".format(i), ''),
             form.get("MediaContentType{}".format(i), ''))
            for i in range(0, num_media)
        ]
        for media_file in media_files:
            # TODO upload pictures to google cloud storage and delete from twilio servers
            picture = Picture(
                source_url=media_file,
                create_time=datetime.now(),
                message_sid=message_sid
            )
            session.add(picture)
            user.add_pending(picture)

    session.commit()

    worker_loop = request.app['worker']['loop']
    response = None

    if user.tc_status is TCStatus.NOTHING:

        log('New user, sending terms and conditions', 'send_tc')
        response = config.TC_AGREEMENT_TEXT
        user.tc_status = TCStatus.SENT
    elif user.tc_status is TCStatus.SENT:

        if message is not None:
            if message.upper() == 'YES':
                log('Agreed to terms and conditions', 'tc_agreed')
                user.tc_status = TCStatus.AGREED
                response = 'Thank you for agreeing to the terms and conditions.'
                if len(user.pending) > 0:
                    response += " Processing your {} picture(s) now".format(len(user.pending))
                    asyncio.run_coroutine_threadsafe(process_pictures(session, user.pending), worker_loop)
                    # request.app.loop.call_soon(functools.partial(process_pictures, session, user.pending))
                    # await process_pictures(session, user.pending)
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
            response = "Got it! Hard at work processing {} more /picture(s) for you!".format(num_media)
            asyncio.run_coroutine_threadsafe(process_pictures(session, user.pending), worker_loop)
            # request.app.loop.call_soon(functools.partial(process_pictures, session, user.pending))
            # await process_pictures(session, user.pending)

    session.commit()

    if not response:
        response = "Sorry, I didn't understand that!"
    mesg_resp = MessagingResponse()
    mesg_resp.message(response)
    return Response(text=str(mesg_resp), content_type='text/xml')
