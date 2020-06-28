import asyncio
import websockets
import logging
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


class RequestHandler:

	def __init__(self):
		super().__init__()
		self.lang_server = LanguageServer()
		self.ep = endpoint.Endpoint(
			self.lang_server,
			self.save_result
		)
		self.lang_server = self.ep
		self.result = 'Default'
	
	def save_result(self, msg):
		self.result = json.dumps(msg)
	
	async def handler(self, websocket, path):
		message = await websocket.recv()
		# log.info(f"Received message: {message}")
		print(f"Received message: {message}")
		self.ep.consume(json.loads(message))
		await websocket.send(self.result)
		await websocket.send(self.result)
		print(f"> {self.result}")


if __name__ == "__main__":
	handler = RequestHandler()
	start_server = websockets.serve(handler.handler, "localhost", 3000, ping_interval=None)
	asyncio.get_event_loop().run_until_complete(start_server)
	asyncio.get_event_loop().run_forever()
