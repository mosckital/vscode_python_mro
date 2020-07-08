import logging
import os
import socketserver
import threading
from functools import partial
from pyls_jsonrpc.dispatchers import MethodDispatcher
from pyls_jsonrpc.endpoint import Endpoint
from pyls_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter


log = logging.getLogger(__name__)


MAX_WORKERS = 64


class _StreamHandlerWrapper(socketserver.StreamRequestHandler, object):
	"""A wrapper class that is used to construct a custom handler class."""

	delegate = None

	def setup(self):
		super(_StreamHandlerWrapper, self).setup()
		# pylint: disable=no-member
		self.delegate = self.DELEGATE_CLASS(self.rfile, self.wfile)

	def handle(self):
		try:
			self.delegate.start()
		except OSError as e:
			if os.name == 'nt':
				# Catch and pass on ConnectionResetError when parent process
				# dies
				# pylint: disable=no-member, undefined-variable
				if isinstance(e, WindowsError) and e.winerror == 10054:
					pass

		# pylint: disable=no-member
		self.SHUTDOWN_CALL()


def start_tcp_lang_server(bind_addr, port, check_parent_process, handler_class):
	if not issubclass(handler_class, PythonLanguageServer):
		raise ValueError('Handler class must be an instance of PythonLanguageServer')

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

	server = socketserver.TCPServer((bind_addr, port), wrapper_class, bind_and_activate=False)
	server.allow_reuse_address = True

	try:
		server.server_bind()
		server.server_activate()
		log.info('Serving %s on (%s, %s)', handler_class.__name__, bind_addr, port)
		server.serve_forever()
	finally:
		log.info('Shutting down')
		server.server_close()


class PythonLanguageServer(MethodDispatcher):
	"""Implement a JSON RPC method dispatcher for the language server protocol."""

	def __init__(self, rx, tx, check_parent_process=False):
		self._jsonrpc_stream_reader = JsonRpcStreamReader(rx)
		self._jsonrpc_stream_writer = JsonRpcStreamWriter(tx)
		self._check_parent_process = check_parent_process
		self._endpoint = Endpoint(self, self._jsonrpc_stream_writer.write, max_workers=MAX_WORKERS)

	def start(self):
		"""Entry point for the server."""
		self._jsonrpc_stream_reader.listen(self._endpoint.consume)

	def m_initialize(self, rootUri=None, **kwargs):
		log.info("Initialising custom Python MRO language server.")
		return {"capabilities": {
			"textDocumentSync": {
				"openClose": True,
				"change": 2,  # TextDocumentSyncKind.Incremental = 2
			},
			"codeLensProvider": {
				"resolveProvider": True,
			},
			"hoverProvider": True,
		}}
	
	def m_text_document__hover(self, textDocument=None, position=None, **_kwargs):
		return {
			'contents': [
				'Target class name',
				'Parent class 1',
				'Parent class 2',
				'...',
				'Object',
			],
		}
	
	def m_text_document__code_lens(self, textDocument=None, **_kwargs):
		return [{
			'range': {
				'start': {
					'line': 1,
					'character': 3,
				},
				'end': {
					'line': 1,
					'character': 6,
				}
			}
		}]
	
	def m_code_lens__resolve(self, **codeLens):
		codeLens['command'] = {
			'command': 'pythonMRO.showMRO',
			'title': 'Show MRO list',
			'arguments': [
				'Fake MRO List L1\nFake MRO List L2\nFake MRO List L3'
			]
		}
		return codeLens


if __name__ == "__main__":
	start_tcp_lang_server('127.0.0.1', 3000, False, PythonLanguageServer)
