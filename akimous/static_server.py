import mimetypes
from http import HTTPStatus
from importlib import resources

from logzero import logger as log
from websockets.http import Headers

mimetypes.init()


def guess_type(name):
    ext = name[name.rfind('.'):]
    if ext in mimetypes.types_map:
        return mimetypes.types_map[ext]
    ext = ext.lower()
    if ext in mimetypes.types_map:
        return mimetypes.types_map[ext]
    else:
        return 'application/octet-stream'


class HTTPHandler:
    def __init__(self):
        self.resource_mapping = {
            'fonts': 'ui_dist.fonts',
            'icons': 'ui_dist.icons',
            'webfonts': 'ui_dist.webfonts'
        }

    def translate_path(self, path):
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        words = tuple(w for w in path.split('/') if w)
        if len(words) > 2:
            return None, None
        if not words:
            return 'ui_dist', 'index.html'
        if len(words) == 1:
            return 'ui_dist', words[0]
        package, file = words
        package = self.resource_mapping.get(package, None)
        return package, file

    def process_request(self, path, _):
        if path.startswith('/ws/'):
            return None
        log.info('Serving %s', path)

        package, file = self.translate_path(path)
        if not package:
            return HTTPStatus.NOT_FOUND, [], b''
        try:
            content_type = guess_type(file)
            content = resources.read_binary(package, file)
            header = Headers({'Content-type': content_type})
            return HTTPStatus.OK, header, content
        except Exception:
            return HTTPStatus.NOT_FOUND, [], b''
