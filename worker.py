from datetime import datetime
from urllib.parse import urljoin

from urllib3.util.retry import Retry
import requests

from client import TwilioClient
from logger import logger
from config import BACKEND_API_URL
from model import User, DEFAULT_STYLE

NUM_WORKERS = 1

_expo_backoff_retry = Retry(
    status=6,
    status_forcelist=Retry.RETRY_AFTER_STATUS_CODES,
    backoff_factor=0.5, # exponential backoff
    respect_retry_after_header=True
)

def convert_picture(picture):
    """
    Sends a request to the backend to convert an image
    Returns (converted_image_url, timestamp)
    Raises HTTPError
    """
    params = {
        'image_url': picture.source
    }
    if picture.style is not DEFAULT_STYLE:
        params['style'] = picture.style

    s = requests.Session()
    a = requests.adapters.HTTPAdapter(max_retries=_expo_backoff_retry)
    s.mount(BACKEND_API_URL, a)

    r = requests.get(urljoin(BACKEND_API_URL, 'convert'), params=params)
    r.raise_for_status()

    jsonResp = r.json()
    return jsonResp['converted_image_url'], datetime.now()

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

def worker(q, stop_event, db):
    logger.info("Start worker")
    while stop_event.wait():
        phone, picture = q.get()
        # TODO this is broken
        # db.session.add(picture)
        extra = lambda event: {
            'picture_id': picture.id,
            'event': event
        }
        logger.info('Working on picture', extra=extra('start_convert'))
        try:
            converted_url, timestamp = convert_picture(picture)
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
            send_converted_image(phone, picture)
            # picture.add_converted_info(converted_url, converted_time=timestamp)
    logger.info("End worker")
