from functools import wraps

from django.core.exceptions import PermissionDenied


def require_verified_reviewer(func):
    """
    Decorator to make a view only allow verified reviewers to make requests to it.
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.reviewer.is_verified()):
            raise PermissionDenied
        return func(request, *args, **kwargs)

    return inner


def require_gel_reviewer(func):
    """
    Decorator to make a view only allow GEL reviewers to make requests to it.
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        if not (request.user.is_authenticated and request.user.reviewer.is_GEL()):
            raise PermissionDenied
        return func(request, *args, **kwargs)

    return inner


def require_gel_or_verified_reviewer(func):
    """
    Decorator to make a view only allow GEL or verified reviewers to make requests to it.
    """

    @wraps(func)
    def inner(request, *args, **kwargs):
        if not (
            request.user.is_authenticated
            and (request.user.reviewer.is_GEL() or request.user.reviewer.is_verified())
        ):
            raise PermissionDenied
        return func(request, *args, **kwargs)

    return inner
