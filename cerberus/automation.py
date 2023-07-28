import re
from functools import wraps
from loguru import logger
import requests


base_url = "http://icinga.cerberus.local:8080"
login_url = f'{base_url}/icingaweb2/authentication/login'
create_resource_url = f"{base_url}/icingaweb2/config/createresource"
change_configuration_url = f"{base_url}/icingaweb2/config/general"
module_url = f"{base_url}/icingaweb2/config/module"
enable_module_url = f"{base_url}/icingaweb2/config/moduleenable"

def _extract_token(data: str) -> None | str:
    token_pos = data.find('CSRFToken')
    match = re.search(r"value=\"([^\"]+)\"", data[token_pos:])
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


@csrf_token(login_url)
def login(session: requests.Session, username: str, password: str, **kwargs):
    response = session.post(
        kwargs['url'],
        data={
            'username': username,
            'password': password,
            "formUID": "form_login",
            "btn_submit": "Login",
            "CSRFToken": kwargs['token']
        },
        allow_redirects=False
    )
    if response.status_code == 302 and response.headers['Location'] == '/icingaweb2/dashboard':
        logger.success(f"Successful login as {username}")
        return True
    logger.critical("Failed to login")
    return False


@csrf_token(create_resource_url)
def create_ssh_resource(session: requests.Session, name: str, user: str, pkey: str, **kwargs):
    response = session.post(
        kwargs['url'],
        data={
            "type": "ssh",
            "name": name,
            "user": user,
            "private_key": pkey.replace('\n', '\r\n'),
            "CSRFToken": kwargs['token'],
            "formUID": "form_config_resource",
            "btn_submit": "Save Changes"
        },
        allow_redirects=False
    )
    if response.status_code == 302:
        logger.success(f"Successfully created resource {name}")
        return True
    logger.critical(f"Failed to create resource {name}")
    return False


@csrf_token(change_configuration_url)
def set_module_path(session: requests.Session, module_path: str, **kwargs):
    response = session.post(
        kwargs['url'],
        data={
            'global_config_resource': 'icingaweb2',
            'logging_log': 'syslog',
            'logging_level': 'ERROR',
            'logging_application': 'icingaweb2',
            'logging_facility': 'user',
            "global_module_path": module_path,
            "CSRFToken": kwargs['token'],
            "formUID": "form_config_general",
            "btn_submit": "Save Changes"
        }
    )
    if response.text.find("ul class=\"errors\"") == -1 and response.text.find(module_path) != -1:
        logger.success(f"Updated the module path to {module_path}")
        return True
    logger.critical("Failed to update the config")
    return False


@csrf_token(module_url)
def activate_module(session: requests.Session, module_name: str, **kwargs):
    response = session.get(f"{kwargs['url']}?name={module_name}")
    if b'There is no such module installed' in response.content:
        logger.critical(f"Failed to find module {module_name}")
        return False

    session.post(
        enable_module_url,
        data={
            'identifier': module_name,
            "CSRFToken": kwargs['token'],
            "btn_submit": "btn_submit"
        }
    )

    response = session.get(f"{kwargs['url']}?name={module_name}")
    if b'enabled' not in response.content:
        logger.critical(f"Failed to start module {module_name}")
        return False
    logger.success(f"Module {module_name} enabled")
    return True


def access_module(session: requests.Session, module_name: str, **kwargs):
    response = session.get(f"{kwargs['url']}?name={module_name}")
