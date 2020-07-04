import logging
from tornado import web, ioloop, websocket
from pyls_jsonrpc import dispatchers, endpoint
try:
	import ujson as json
except Exception:  # pylint: disable=broad-except
	import json


log = logging.getLogger(__name__)


class LanguageServer(dispatchers.MethodDispatcher):
	"""Implement a JSON RPC method dispatcher for the language server protocol."""

	def __init__(self):
		# Endpoint is lazily set after construction
		self.endpoint = None

	def m_initialize(self, rootUri=None, **kwargs):
		log.info("Initialising custom Python MRO language server.")
		return {"capabilities": {
			"textDocumentSync": {
				"openClose": True,
				"change": 2,  # TextDocumentSyncKind.Incremental = 2
			},
			# "codeLensProvider": {
			# 	"resolveProvider": True,
			# },
			"hoverProvider": True,
		}}
	
	def m_hover(self, hoverParams=None, **_kwargs):
		log.info("Providing Hover in {0} for line {1} char {2}".format(
			hoverParams['textDocument']['uri'],
			hoverParams['position']['line'],
			hoverParams['position']['character'],
		))
		self.endpoint.notify('textDocument/hover', {
			'contents': [
				'Target class name',
				'Parent class 1',
				'Parent class 2',
				'...',
				'Object',
			],
		})


class LanguageServerWebSocketHandler(websocket.WebSocketHandler):
	"""Setup tornado websocket handler to host language server."""

	def __init__(self, *args, **kwargs):
		# Create an instance of the language server used to dispatch JSON RPC methods
		langserver = LanguageServer()

		# Setup an endpoint that dispatches to the ls, and writes server->client messages
		# back to the client websocket
		self.endpoint = endpoint.Endpoint(langserver, lambda msg: self.write_message(json.dumps(msg)))

		# Give the language server a handle to the endpoint so it can send JSON RPC
		# notifications and requests.
		langserver.endpoint = self.endpoint

		super(LanguageServerWebSocketHandler, self).__init__(*args, **kwargs)

	def on_message(self, message):
		"""Forward client->server messages to the endpoint."""
		log.info("Received message: {}".format(message))
		print("Received message: {}".format(message))
		# self.endpoint.consume(json.loads(message))
		self.endpoint.consume(self._read_message(message))
	
	def _read_message(self, message):
		lines = message.split('\r\n')
		lines = [l.strip() for l in lines]
		print(lines)
		return json.loads(lines[-1])

	def check_origin(self, origin):
		return True


if __name__ == "__main__":
	app = web.Application([
		(r"/", LanguageServerWebSocketHandler),
	])
	app.listen(3000, address='127.0.0.1')
	ioloop.IOLoop.current().start()