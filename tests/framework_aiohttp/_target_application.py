import asyncio
import sys
from aiohttp import web, WSMsgType, ClientSession
from newrelic.api.function_trace import function_trace


@asyncio.coroutine
def index(request):
    yield
    resp = web.Response(text='Hello Aiohttp!')
    resp.set_cookie('OM', 'NOM')
    return resp


@asyncio.coroutine
def hang(request):
    while True:
        yield


@asyncio.coroutine
def error(request):
    raise ValueError("I'm bad at programming...")


@asyncio.coroutine
def non_500_error(request):
    raise web.HTTPGone()


@asyncio.coroutine
def raise_404(request):
    raise web.HTTPNotFound()


@asyncio.coroutine
@function_trace()
def wait():
    yield from asyncio.sleep(0.1)


@asyncio.coroutine
def run_task(loop):
    yield from wait()
    loop.stop()


@asyncio.coroutine
def background(request):
    try:
        loop = request.loop
    except AttributeError:
        loop = request.task._loop

    asyncio.set_event_loop(loop)
    asyncio.tasks.ensure_future(run_task(loop))
    return web.Response(text='Background Task Scheduled')


class HelloWorldView(web.View):

    @asyncio.coroutine
    def _respond(self):
        yield
        resp = web.Response(text='Hello Aiohttp!')
        resp.set_cookie('OM', 'NOM')
        return resp

    get = _respond
    post = _respond
    put = _respond
    patch = _respond
    delete = _respond


class KnownException(Exception):
    pass


class KnownErrorView(web.View):

    @asyncio.coroutine
    def _respond(self):
        try:
            yield
        except KnownException:
            pass
        finally:
            return web.Response(text='Hello Aiohttp!')

    get = _respond
    post = _respond
    put = _respond
    patch = _respond
    delete = _respond


@asyncio.coroutine
def websocket_handler(request):

    ws = web.WebSocketResponse()
    yield from ws.prepare(request)

    # receive messages for all eternity!
    # (or until the client closes the socket)
    while not ws.closed:
        msg = yield from ws.receive()
        if msg.type == WSMsgType.TEXT:
            result = ws.send_str('/' + msg.data)
            if hasattr(result, '__await__'):
                yield from result.__await__()

    return ws


@asyncio.coroutine
def fetch(method, url, loop):
    session = ClientSession(loop=loop)

    if hasattr(session, '__aenter__'):
        yield from session.__aenter__()
    else:
        session.__enter__()

    try:
        _method = getattr(session, method)
        response = yield from asyncio.wait_for(
                _method(url), timeout=None, loop=loop)
        text = yield from response.text()

    finally:
        if hasattr(session, '__aexit__'):
            yield from session.__aexit__(*sys.exc_info())
        else:
            session.__exit__(*sys.exc_info())

    return text


@asyncio.coroutine
def fetch_multiple(method, loop):
    URLS = ['https://example.com', 'https://example.org']
    coros = [fetch(method, url, loop) for url in URLS]
    responses = yield from asyncio.gather(*coros, loop=loop)
    return '\n'.join(responses)


@asyncio.coroutine
def multi_fetch_handler(request):
    try:
        loop = request.loop
    except AttributeError:
        loop = request.task._loop

    responses = yield from fetch_multiple('get', loop)
    return web.Response(text=responses, content_type='text/html')


def make_app(middlewares=None, loop=None):
    app = web.Application(middlewares=middlewares, loop=loop)
    app.router.add_route('*', '/coro', index)
    app.router.add_route('*', '/class', HelloWorldView)
    app.router.add_route('*', '/error', error)
    app.router.add_route('*', '/known_error', KnownErrorView)
    app.router.add_route('*', '/non_500_error', non_500_error)
    app.router.add_route('*', '/raise_404', raise_404)
    app.router.add_route('*', '/hang', hang)
    app.router.add_route('*', '/background', background)
    app.router.add_route('*', '/ws', websocket_handler)
    app.router.add_route('*', '/multi_fetch', multi_fetch_handler)

    return app


if __name__ == '__main__':
    web.run_app(make_app(), host='127.0.0.1')
