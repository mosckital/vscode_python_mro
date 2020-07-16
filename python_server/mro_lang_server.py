import logging
import re
from pyls_jsonrpc.dispatchers import MethodDispatcher
from pyls_jsonrpc.endpoint import Endpoint
from pyls_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter


log = logging.getLogger(__name__)


class MROLanguageServer(MethodDispatcher):
	"""Implement a JSON RPC method dispatcher for the language server protocol."""

	MAX_WORKERS = 64

	SYNC_FULL = 1  # TextDocumentSyncKind.Full = 1
	SYNC_INCREMENTAL = 2  # TextDocumentSyncKind.Incremental = 2

	def __init__(self, rx, tx, check_parent_process=False, sync_kind=0):
		self._jsonrpc_stream_reader = JsonRpcStreamReader(rx)
		self._jsonrpc_stream_writer = JsonRpcStreamWriter(tx)
		self._check_parent_process = check_parent_process
		self._endpoint = Endpoint(self, self._jsonrpc_stream_writer.write, max_workers=self.MAX_WORKERS)
		# to store the synced documents
		self._docs = dict()
		self._found_lenses = dict()
		# the synchronisation kind between the language server and client
		self._sync_kind = sync_kind if sync_kind else self.SYNC_INCREMENTAL

	def start(self):
		"""Entry point for the server."""
		# start to listen on the stream input, the consume() will write the
		# result into the stream output via the stream writer
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
		"""Split the lines of the newly opened document and store them."""
		self._docs[textDocument['uri']] = self._split_lines(textDocument['text'])
	
	def m_text_document__did_change(self, textDocument=None, contentChanges=None):
		"""Update the stored document contents according to the sync kind."""
		if not contentChanges:
			return
		if self._sync_kind == self.SYNC_FULL:
			self._docs[textDocument['uri']] = self._split_lines(contentChanges[0]['text'])
		elif self._sync_kind == self.SYNC_INCREMENTAL:
			for change in contentChanges:
				self._incremental_update(textDocument['uri'], change)
	
	def _incremental_update(self, uri, change):
		"""Update a stored document by its incremental change."""
		# fetch the lines of the old content
		lines = self._docs[uri]
		# decompose the incremental change
		start = change['range']['start']
		start_line, start_char = start['line'], start['character']
		end = change['range']['end']
		end_line, end_char = end['line'], end['character']
		update_lines = self._split_lines(change['text'])
		# the lines of the new content is consisted of three parts:
		# 1. from the start of old content to the start position of the change
		# 2. the change
		# 3. from the end of the change to the end of the old content
		new_lines = []
		new_lines.extend(lines[:start_line])
		new_lines.append(lines[start_line][:start_char] + (update_lines[0] if update_lines else ''))
		new_lines.extend(update_lines[1:])
		new_lines[-1] += lines[end_line][end_char:]
		new_lines.extend(lines[end_line + 1:])
		# update in the recording dict
		self._docs[uri] = new_lines
	
	@staticmethod
	def _split_lines(text):
		"""Split a text into lines and fill a new line if the last line is '\\n'."""
		lines = text.splitlines()
		if not text or text[-1] == '\n':
			lines.append('')
		return lines
	
	def update_code_lenses(self, uri):
		"""Update the code lenses in the document of the given uri."""
		lines = self._docs[uri]
		self._found_lenses[uri] = []
		for idx, line in enumerate(lines):
			for match in re.finditer(r'\bclass (\w+)\b', line):
				self._found_lenses[uri].append({
					'range': {
						'start': {
							'line': idx,
							'character': match.start(1),
						},
						'end': {
							'line': idx,
							'character': match.end(1),
						}
					},
					'data': [
						'Target class name',
						'Parent class 1',
						'Parent class 2',
						'...',
						'Object',
					],
				})
	
	@staticmethod
	def is_pos_in_range(pos, ran):
		"""Check if a position is within a range."""
		ran_start = ran['start']
		ran_end = ran['end']
		if pos['line'] < ran_start['line'] or pos['line'] > ran_end['line']:
			return False
		if pos['line'] == ran_start['line'] and pos['character'] < ran_start['character']:
			return False
		if pos['line'] == ran_end['line'] and pos['character'] >= ran_end['character']:
			return False
		return True

	def m_text_document__hover(self, textDocument=None, position=None, **_kwargs):
		"""Calculate and return the hover result."""
		for lens in self._found_lenses[textDocument['uri']]:
			if self.is_pos_in_range(position, lens['range']):
				return {
					'contents': lens['data'],
				}
		return None
	
	def m_text_document__code_lens(self, textDocument=None, **_kwargs):
		"""Calculate and return the code lens list."""
		uri = textDocument['uri']
		self.update_code_lenses(uri)
		return self._found_lenses[uri]
	
	def m_code_lens__resolve(self, **codeLens):
		"""Fill up the details of a code lens."""
		codeLens['command'] = {
			'command': 'pythonMRO.showMRO',
			'title': 'Show MRO list',
			'arguments': [
				'\n'.join(codeLens['data']),
			]
		}
		return codeLens

	def m_shutdown(self):
		log.info('Shutting down the service')
	
	def m_initialized(self):
		log.info('Service initialised')

	def m_exit(self):
		log.info('Exiting...')
