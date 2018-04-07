import asyncio
from concurrent.futures import CancelledError
from datetime import datetime
import functools
from urllib.parse import urljoin
import threading

from aiohttp import ClientSession
from twilio.rest import Client as _twilioClient

from client import TwilioClient
from logger import logger
from config import BACKEND_API_URL
from model import User, DEFAULT_STYLE


# _expo_backoff_retry = Retry(
#     status=6,
#     status_forcelist=Retry.RETRY_AFTER_STATUS_CODES,
#     backoff_factor=0.5, # exponential backoff
#     respect_retry_after_header=True
# )

# async def convert_picture(picture):
#     """
#     Sends a request to the backend to convert an image
#     Returns (converted_image_url, timestamp)
#     Raises HTTPError
#     """

#     params = {
#         'image_url': picture.source
#     }
#     if picture.style is not DEFAULT_STYLE:
#         params['style'] = picture.style

#     async with ClientSession() as session:
#         async with session.get(BACKEND_API_URL, params=params) as resp:
#             jsonResp = await resp.json()

#     # s = requests.Session()
#     # a = requests.adapters.HTTPAdapter(max_retries=_expo_backoff_retry)
#     # s.mount(BACKEND_API_URL, a)

#     # r = requests.get(urljoin(BACKEND_API_URL, 'convert'), params=params)
#     # r.raise_for_status()

#     # jsonResp = r.json()
#     return jsonResp['converted_image_url'], datetime.now()

async def convert_picture(picture):
    print('start convert picture')
    await asyncio.sleep(.5)
    print('finished convert picture')
    return 'https://www.twilio.com/blog/wp-content/uploads/2016/12/21VC0iKKbFDAY_yVLwtESY3v5-C2KbIh8B-B0q7yU2CGeIs-b4LOBeHcJVX9WgPlfS-6POyD8xBGUgKPAQ63G6-UBYp-aUkIR5GilmibgCQ4Qe6kvEpIQsdLHSQGQXvcGDKiq4gF.png', datetime.now()


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
    TwilioClient.send_message(phone, media_url=picture.converted_url)

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
        except requests.HTTPError as e:
            # TODO flag backend status as erroring, notify users that the service is down
            # TODO retry after a specified time?
            logger.warn('Convert request failed', extra=extra('failed_convert'))
            send_error_message(phone)
        except:
            logger.warn('Convert failed, unknown error', extra=extra('failed_convert'))
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
