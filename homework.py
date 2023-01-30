from http import HTTPStatus
import logging
import os
import sys
import time

import requests
import telegram

from dotenv import load_dotenv

from exceptions import (APIRequestError, BaseAPIError, EmptyResponseError,
                        ImproperlyConfigured, ResponseTypeError)

load_dotenv()

logger = logging.getLogger(f'praktikum_{__name__}_bot')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    '%(asctime)s (%(name)s:%(lineno)d) [%(levelname)s]: %(message)s'
)
handler.setFormatter(formatter)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """
    Checks availability of required tokens.

    :raises ImproperlyConfiguredError: if required tokens are missing.
    """
    if not (PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID):
        raise ImproperlyConfigured('Required tokens are missing in .env file.')


def send_message(bot: telegram.Bot, message: str) -> None:
    """
    Send message to TELEGRAM_CHAT_ID.

    :param Bot bot: The bot instance to send message from
    :param str message: The message to be sent
    """
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logger.debug(f'Message sent: {message}')
    except Exception:
        logger.error('Can not send message')


def get_api_answer(timestamp: int) -> dict:
    """Send request to ENDPOINT.

    :param int timestamp: The timestamp to get homeworks from
    :return: The response
    :raises APIRequestError: if response status_code is not OK
    """
    try:
        payload = {'from_date': timestamp}
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException:
        raise APIRequestError(f'API error. Status code: {response.status_code}')

    if response.status_code != HTTPStatus.OK:
        raise APIRequestError(f'API error. Status code: {response.status_code}')
    return response.json()


def check_response(response: dict) -> None:
    """
    Check that response type corresponds with docs.

    :param dict response: The response from ENDPOINT
    :raises ResponseTypeError: if 'homeworks' or 'current_date' are not present
    in response, or 'lesson_name' or 'status' are not present in homework,
    or status not in HOMEWORK_VERDICTS
    :raises EmptyResponseError: if 'homeworks' list in response is empty
    """
    if 'homeworks' not in response:
        raise ResponseTypeError('API response is of wrong type.')
    if 'current_date' not in response:
        raise ResponseTypeError('API response is of wrong type.')
    if not type(response['homeworks']) is list:
        raise ResponseTypeError('API response is of wrong type.')
    if len(response['homeworks']) == 0:
        raise EmptyResponseError('API response is empty.')
    if 'status' not in response['homeworks'][0]:
        raise ResponseTypeError('API response is of wrong type.')
    if 'homework_name' not in response['homeworks'][0]:
        raise ResponseTypeError('API response is of wrong type.')
    if response['homeworks'][0]['status'] not in HOMEWORK_VERDICTS:
        raise ResponseTypeError('API response is of wrong type.')


def parse_status(homework: dict) -> str:
    """
    Parse homework verdict from homework dict.

    :param dict homework: Dict from ENDPOINT to search status in
    :return: Message string with status
    """
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except KeyError:
        raise ResponseTypeError('API response is of wrong type.')


def main():
    """Основная логика работы бота."""
    try:
        check_tokens()
    except ImproperlyConfigured as error:
        logger.critical(error)
        exit(1)

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    is_api_error = False

    while True:
        try:
            timestamp = int(time.time())
            response = get_api_answer(timestamp)
            check_response(response)
            message = '\n'.join(parse_status(hw)
                                for hw in response['homeworks'])
            is_api_error = False
            send_message(bot, message)

        except BaseAPIError as error:
            logger.error(error)
            if not is_api_error:
                is_api_error = True
                message = f'Сбой в работе программы: {error}'
                send_message(bot, message)

        except EmptyResponseError:
            logger.debug('New statuses are not present')

        except Exception as error:
            logger.error('aboba')
            message = f'Сбой в работе программы: {error}'
            send_message(bot, message)

        finally:
            ten_minutes_in_seconds = 10 * 60
            time.sleep(ten_minutes_in_seconds)


if __name__ == '__main__':
    main()
