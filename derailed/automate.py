import random
import re
import string
from functools import wraps
from loguru import logger
import requests


base_url = "http://derailed.htb:3000"
register_url = f"{base_url}/register"
login_url = f"{base_url}/login"
create_note_url = f"{base_url}/create"
report_note_url = f"{base_url}/report"
report_note_details_url = report_note_url + "/{note_id}"


def random_string(length: int = 8, charset: str = string.ascii_letters) -> str:
    return ''.join(random.choices(charset, k=length))


def _extract_token(data: str) -> None | str:
    match = re.search(r"name=\"authenticity_token\".*value=\"([^\"]+)\"", data)
    if not match:
        logger.critical("Failed to find authenticity token")
        return None
    return match[1]


def _get_csrf_token(session: requests.Session, url: str) -> None | str:
    response = session.get(url)
    if not response.ok:
        logger.critical(f"Failed to get the requested page [{url}]")
        return None
    return _extract_token(response.text)


def csrf_token(url):
    def decorator(func):
        @wraps(func)
        def wrapper(session: requests.Session, *args, **kwargs):
            _csrf_token = _get_csrf_token(session, url.format(**kwargs))
            if _csrf_token is not None:
                return func(session, url=url, token=_csrf_token, *args, **kwargs)
            return None
        return wrapper
    return decorator


@csrf_token(register_url)
def register(session: requests.Session, username: str, password: str, **kwargs) -> bool:
    logger.info("Registering new user")
    response = session.post(kwargs['url'], data={
        "authenticity_token": kwargs['token'],
        "user[username]": username,
        "user[password]": password,
        "user[password_confirmation]": password
    })

    if not response.ok:
        logger.critical("Failed to create user")
    else:
        logger.success(f"Created user {username}:{password}")
    return response.ok


@csrf_token(login_url)
def login(session: requests.Session, username: str, password: str, **kwargs) -> bool:
    logger.info(f"Login as {username}")

    response = session.post(kwargs['url'], data={
        "authenticity_token": kwargs['token'],
        "session[username]": username,
        "session[password]": password,
        "button": ""
    }, allow_redirects=False)
    login_success = response.status_code == 302 and response.headers["Location"] != '/login'
    if login_success:
        logger.success(f"Logged in as {username}")
    else:
        logger.error("Failed to login")
    return login_success


# we use token from the main page to create the notes
@csrf_token(base_url)
def create_note(session: requests.Session, note: str, **kwargs) -> str | None:
    logger.info("Creating a new note")
    response = session.post(create_note_url, data={
        "authenticity_token": kwargs['token'],
        "note[content]": note,
        "button": ""
    })
    if not response.ok:
        logger.error("Failed to create a new note")
        return None
    note_id = response.url.rsplit("/", 1)[1]
    logger.success(f"New note created, id = {note_id} ({response.url})")
    return note_id


@csrf_token(report_note_details_url)
def report_note(session: requests.Session, note_id: str, **kwargs) -> bool:
    logger.info("Reporting the note")
    session.headers['Referer'] = kwargs['url']
    response = session.post(report_note_url, data={
        "authenticity_token": kwargs['token'],
        "report[reason]": "",
        "report[note_id]": note_id
    })
    if not response.ok:
        logger.error("Failed to report the note")
    else:
        logger.success("Reported the note")
    return response.ok
