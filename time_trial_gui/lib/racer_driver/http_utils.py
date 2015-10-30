from http.server import BaseHTTPRequestHandler
from io import BytesIO


class ParseException(Exception):
    pass


class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()
        self.request_body = self.rfile.read()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message


def parse_request(request_text):
    request = HTTPRequest(request_text)

    if request.error_code:
        raise ParseException(request.error_message)

    # request.headers is still a message object
    # items returns a list of tuples, but we need actual header k,v pairs:
    header_list = [x[0] + ": " + x[1] for x in request.headers.items()]

    return (request.command, request.path, request.request_version,
            request.request_body, header_list)
