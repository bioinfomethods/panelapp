import zstandard as zstd


class ZstdMiddleware:
    """Compress responses using zstd for clients that support it."""

    # Only compress these content types
    COMPRESSIBLE_TYPES = (
        "text/",
        "application/json",
        "application/javascript",
        "application/xml",
    )

    def __init__(self, get_response):
        self.get_response = get_response
        self.compressor = zstd.ZstdCompressor(level=3)

    def __call__(self, request):
        response = self.get_response(request)

        accept = request.META.get("HTTP_ACCEPT_ENCODING", "")
        if "zstd" not in accept:
            return response

        if response.streaming or response.status_code != 200:
            return response

        content_type = response.get("Content-Type", "")
        if not any(content_type.startswith(ct) for ct in self.COMPRESSIBLE_TYPES):
            return response

        # Skip small responses (not worth compressing)
        if len(response.content) < 200:
            return response

        response.content = self.compressor.compress(response.content)
        response["Content-Encoding"] = "zstd"
        response["Vary"] = "Accept-Encoding"
        if "Content-Length" in response:
            del response["Content-Length"]

        return response
