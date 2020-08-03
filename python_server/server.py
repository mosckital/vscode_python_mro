import logging
import os
import socketserver
import threading
from functools import partial
from typing import Callable, Optional
from python_server.mro_lang_server import MROLanguageServer


log = logging.getLogger(__name__)


class _StreamHandlerWrapper(socketserver.StreamRequestHandler, object):
    """A wrapper class that is used to construct a custom handler class."""

    delegate = None

    DELEGATE_CLASS : Optional[Callable] = None
    SHUTDOWN_CALL : Optional[Callable] = None

    def setup(self):
        super(_StreamHandlerWrapper, self).setup()
        # the DELEGATE_CLASS should be MROLanguageServer
        # pylint: disable=no-member
        self.delegate = self.DELEGATE_CLASS(self.rfile, self.wfile)

    def handle(self):
        try:
            self.delegate.start()
        except OSError as e:
            if os.name == 'nt':
                # Catch & pass on ConnectionResetError when parent process dies
                # pylint: disable=no-member, undefined-variable
                if isinstance(e, WindowsError) and e.winerror == 10054:
                    pass

        # pylint: disable=no-member
        self.SHUTDOWN_CALL()


def start_tcp_lang_server(bind_addr, port, check_parent_process, handler_class):
    if not issubclass(handler_class, MROLanguageServer):
        raise ValueError(
            'Handler class must be an instance of MROLanguageServer')

    def shutdown_server(check_parent_process, *args):
        # pylint: disable=unused-argument
        if check_parent_process:
            log.debug('Shutting down server')
            # Shutdown call must be done on a thread, to prevent deadlocks
            stop_thread = threading.Thread(target=server.shutdown)
            stop_thread.start()

    # Construct a custom wrapper class around the user's handler_class
    wrapper_class = type(
     handler_class.__name__ + 'Handler',
     (_StreamHandlerWrapper,),
     {'DELEGATE_CLASS': partial(handler_class,
              check_parent_process=check_parent_process),
      'SHUTDOWN_CALL': partial(shutdown_server, check_parent_process)}
    )

    server = socketserver.TCPServer((bind_addr, port),
                                    wrapper_class,
                                    bind_and_activate=False)
    server.allow_reuse_address = True

    try:
        server.server_bind()
        server.server_activate()
        log.info('Serving %s on (%s, %s)', handler_class.__name__, bind_addr,
                 port)
        server.serve_forever()
    finally:
        log.info('Shutting down')
        server.server_close()


if __name__ == "__main__":
    start_tcp_lang_server('127.0.0.1', 3000, False, MROLanguageServer)
