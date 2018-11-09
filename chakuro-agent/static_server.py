from multiprocessing import Process
from logzero import logger as log


def get_http_server(host, port):
    import http.server
    from functools import partial
    log.info('Starting HTTP server.')
    handler = partial(http.server.SimpleHTTPRequestHandler, directory='../dist')
    return http.server.HTTPServer((host, port), handler)


def serve_http(host, port):
    http_server = get_http_server(host, port)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.shutdown()
        log.info('HTTP server terminated.')


if __name__ == '__main__':
    process = Process(target=serve_http, name='http_process')
    process.start()
    log.info('HTTP server started.')
    try:
        process.join()
    except KeyboardInterrupt:
        pass
