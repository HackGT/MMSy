import asyncio
from concurrent.futures import CancelledError
from datetime import datetime
import functools
import threading
from urllib.parse import urljoin, quote

from aiohttp import ClientSession, ClientError
from twilio.rest import Client as _twilioClient

from client import TwilioClient
from logger import logger
from config import BACKEND_API_URL, TWILIO_SERVICE_SID, TWILIO_AUTH_TOKEN, TWILIO_ACCOUNT_SID
from model import User, DEFAULT_STYLE


# _expo_backoff_retry = Retry(
#     status=6,
#     status_forcelist=Retry.RETRY_AFTER_STATUS_CODES,
#     backoff_factor=0.5, # exponential backoff
#     respect_retry_after_header=True
# )

account = os.environ['TWILIO_ACCOUNT']
token = os.environ["TWILIO_TOKEN"]
client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

async def convert_picture(picture):
    """
    Sends a request to the backend to convert an image
    Returns (converted_image_url, timestamp)
    Raises HTTPError
    """

    params = {
        'image_url': quote(picture.source_url),
        'style': 'psych01'
    }

    print(params)
    # TODO pick random style
    # if picture.style is not DEFAULT_STYLE:
    #     params['style'] = picture.style

    async with ClientSession() as session:
        async with session.get(BACKEND_API_URL, params=params) as resp:
            jsonResp = await resp.json()
            return jsonResp['url'], datetime.now()

def send_error_message(phone):
    """
    Notify the user of a service outage
    phone - string of phone number
    """
    TwilioClient.send_message(phone, body="Sorry, unfortunately the service is unavailable at the moment")

def send_converted_image(phone, picture):
    """
    Send MMS message with converted image
    phone - string of phone number
    picture - instance of `model.Picture`
    """
    # TwilioClient.send_message(phone, media_url=picture.converted_url)
    client.messages.create(
        to=phone,
        messaging_service_sid=TWILIO_SERVICE_SID,
        body="",
        media_url=picture.converted_url
    )

async def process_pictures(session, pictures):
    logger.info("Start processing")
    for picture in pictures:
        phone = picture.user.phone_number
        extra = lambda event: {
            'picture_id': picture.id,
            'event': event
        }
        logger.info('Working on picture', extra=extra('start_convert'))
        try:
            converted_url, timestamp = await convert_picture(picture)
        except ClientError as e:
            # TODO flag backend status as erroring, notify users that the service is down
            # TODO retry after a specified time?
            logger.warn('Convert request failed', extra=extra('failed_convert'))
            picture.failed = True
            send_error_message(phone)
        except:
            logger.warn('Convert failed, unknown error', extra=extra('failed_convert'))
            picture.failed = True
            send_error_message(phone)
        else:
            logger.info('Finished converting', extra=extra('finished_convert'))
            picture.add_converted_info(converted_url, converted_time=timestamp)
            send_converted_image(phone, picture)
    session.commit()
    logger.info("Finished processing")

async def test():
    print("test start")
    await asyncio.sleep(2)
    print("test end")

async def worker(app):
    worker_loop = asyncio.new_event_loop()

    def start_worker_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()

    bw_thread = threading.Thread(target=start_worker_loop, args=(worker_loop,))
    bw_thread.start()

    app['worker'] = {
        'thread': bw_thread,
        'loop': worker_loop
    }

    yield

    def stop_worker_loop(loop):
        asyncio.gather(*asyncio.Task.all_tasks()).cancel()
        try:
            loop.stop()
        except:
            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.close()

    worker_loop.call_soon_threadsafe(stop_worker_loop, worker_loop)
