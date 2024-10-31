from csp.constants import (
    NONCE,
    SELF,
)


def default() -> dict:
    return {
        "DIRECTIVES": {
            "default-src": [SELF, NONCE],
            "frame-ancestors": [SELF],
            "form-action": [SELF],
        }
    }


def aws(static_url: str, media_url: str) -> dict:
    policy = default()
    policy["DIRECTIVES"]["default-src"].extend([static_url, media_url])
    return policy
