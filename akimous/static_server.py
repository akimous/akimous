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
            'fonts': 'akimous_ui.fonts',
            'icons': 'akimous_ui.icons',
            'webfonts': 'akimous_ui.webfonts'
        }

    def translate_path(self, path):
        # abandon query parameters
        path = path.split('?', 1)[0]
        path = path.split('#', 1)[0]
        words = tuple(w for w in path.split('/') if w)
        if len(words) > 2:
            return None, None
        if not words:
            return 'akimous_ui', 'index.html'
        if len(words) == 1:
            return 'akimous_ui', words[0]
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
            header = {
                'content-type': guess_type(file),
                'cache-control': 'max-age=31536000'
            }
            try:
                content = resources.read_binary(package, f'{file}.gz')
                header['content-encoding'] = 'gzip'
            except FileNotFoundError:
                content = resources.read_binary(package, file)

            return HTTPStatus.OK, Headers(header), content
        except FileNotFoundError:
            return HTTPStatus.NOT_FOUND, [], b''
