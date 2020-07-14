import logging
import os
import socketserver
import threading
import re
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

	SYNC_FULL = 1  # TextDocumentSyncKind.Full = 1
	SYNC_INCREMENTAL = 2  # TextDocumentSyncKind.Incremental = 2

	def __init__(self, rx, tx, check_parent_process=False):
		self._jsonrpc_stream_reader = JsonRpcStreamReader(rx)
		self._jsonrpc_stream_writer = JsonRpcStreamWriter(tx)
		self._check_parent_process = check_parent_process
		self._endpoint = Endpoint(self, self._jsonrpc_stream_writer.write, max_workers=MAX_WORKERS)
		self._docs = dict()
		self._sync_kind = self.SYNC_INCREMENTAL

	def start(self):
		"""Entry point for the server."""
		self._jsonrpc_stream_reader.listen(self._endpoint.consume)

	def m_initialize(self, rootUri=None, **kwargs):
		log.info("Initialising custom Python MRO language server.")
		return {"capabilities": {
			"textDocumentSync": {
				"openClose": True,
				"change": self._sync_kind,
			},
			"codeLensProvider": {
				"resolveProvider": True,
			},
			"hoverProvider": True,
		}}
	
	def m_text_document__did_open(self, textDocument=None):
		self._docs[textDocument['uri']] = self._split_lines(textDocument['text'])
	
	def m_text_document__did_change(self, textDocument=None, contentChanges=None):
		if not contentChanges:
			return
		if self._sync_kind == self.SYNC_FULL:
			self._docs[textDocument['uri']] = self._split_lines(contentChanges[0]['text'])
		elif self._sync_kind == self.SYNC_INCREMENTAL:
			for change in contentChanges:
				print(f'Change:\n{change}')
				self._incremental_update(textDocument['uri'], change)
	
	def _incremental_update(self, uri, change):
		lines = self._docs[uri]
		print(f'Original lines:\n{lines}')
		start = change['range']['start']
		start_line, start_char = start['line'], start['character']
		end = change['range']['end']
		end_line, end_char = end['line'], end['character']
		update_lines = self._split_lines(change['text'])
		print(f'Updated lines:\n{update_lines}')
		new_lines = []
		new_lines.extend(lines[:start_line])
		new_lines.append(lines[start_line][:start_char] + (update_lines[0] if update_lines else ''))
		new_lines.extend(update_lines[1:])
		new_lines[-1] += lines[end_line][end_char:]
		new_lines.extend(lines[end_line + 1:])
		self._docs[uri] = new_lines
		print(f'New lines:\n{new_lines}')
	
	@staticmethod
	def _split_lines(text):
		lines = text.splitlines()
		if not text or text[-1] == '\n':
			lines.append('')
		return lines
	
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
	
	@staticmethod
	def find_class_in_text_document(lines):
		lenses = []
		for idx, line in enumerate(lines):
			for match in re.finditer(r'\bclass\b', line):
				lenses.append({
					'range': {
						'start': {
							'line': idx,
							'character': match.start(),
						},
						'end': {
							'line': idx,
							'character': match.end(),
						}
					}
				})
		return lenses
	
	def m_text_document__code_lens(self, textDocument=None, **_kwargs):
		uri = textDocument['uri']
		if uri in self._docs:
			# document = self._docs[uri]
			# text = document['text']
			lines = self._docs[uri]
			return self.find_class_in_text_document(lines)
		else:
			return None
	
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
