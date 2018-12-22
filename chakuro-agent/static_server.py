import mimetypes
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler

from logzero import logger as log
from websockets.http import Headers


class HTTPHandler:
    def __init__(self):
        self.directory = '../dist'
        if not mimetypes.inited:
            mimetypes.init()
        self.extensions_map = mimetypes.types_map.copy()
        self.extensions_map.update({'': 'application/octet-stream'})

    def get_file_path(self, path):
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        if os.path.isdir(path):
            path = os.path.join(path, 'index.html')
        if os.path.exists(path):
            return path
        return None

    def process_request(self, path, _):
        if path.startswith('/ws/'):
            return None
        log.info('Serving %s', path)

        file_path = self.get_file_path(path)
        if not file_path:
            log.warning('File not found: %s', path)
            return HTTPStatus.NOT_FOUND, [], b''

        content_type = SimpleHTTPRequestHandler.guess_type(self, file_path)
        with open(file_path, 'rb') as f:
            content = f.read()
        header = Headers({'Content-type': content_type})
        return HTTPStatus.OK, header, content
