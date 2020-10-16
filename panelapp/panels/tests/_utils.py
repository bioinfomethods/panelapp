from typing import (
    List,
    Union,
)

from django.contrib.messages import get_messages
from django.contrib.messages.storage.base import Message
from django.core.handlers.wsgi import WSGIRequest


def get_test_request_messages(
    wsgi_request: WSGIRequest, min_level: int = 0, convert_to_str: bool = True
) -> Union[List[str], List[Message]]:
    """Get messages after processing the request

    :param wsgi_request: test client response wsgi_request - `res.wsgi_request`
    :param min_level: message level - success is 25, anything above is error
    :param convert_to_str: whether to return raw message or a string
    :return: either list of messages or list of strings
    """

    messages = [m for m in get_messages(wsgi_request) if m.level > min_level]
    return list(map(str, messages)) if convert_to_str else messages
