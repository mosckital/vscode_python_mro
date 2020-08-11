import logging
from os.path import abspath
from urllib.parse import unquote, urlparse
from pyls_jsonrpc.dispatchers import MethodDispatcher
from pyls_jsonrpc.endpoint import Endpoint
from pyls_jsonrpc.streams import JsonRpcStreamReader, JsonRpcStreamWriter
from python_server.analyser import MROAnalyser


log = logging.getLogger(__name__)


class MROLanguageServer(MethodDispatcher):
    """
    Implement a JSON RPC method dispatcher for the language server protocol.
    """

    MAX_WORKERS = 64

    SYNC_FULL = 1  # TextDocumentSyncKind.Full = 1
    SYNC_INCREMENTAL = 2  # TextDocumentSyncKind.Incremental = 2

    def __init__(self, rx, tx, check_parent_process=False, sync_kind=0):
        self._jsonrpc_stream_reader = JsonRpcStreamReader(rx)
        self._jsonrpc_stream_writer = JsonRpcStreamWriter(tx)
        self._check_parent_process = check_parent_process
        self._endpoint = Endpoint(self,
                                  self._jsonrpc_stream_writer.write,
                                  max_workers=self.MAX_WORKERS)
        # the synchronisation kind between the language server and client
        self._sync_kind = sync_kind if sync_kind else self.SYNC_INCREMENTAL
        # the actual MRO analyser
        self._analyser = None

    def start(self):
        """Entry point for the server."""
        # start to listen on the stream input, the consume() will write the
        # result into the stream output via the stream writer
        self._jsonrpc_stream_reader.listen(self._endpoint.consume)

    def m_initialize(self, rootUri=None, rootPath=None, **kwargs):
        """Initialise the language server and reply the capabilities."""
        root_dir = self.uri_to_abs_path(rootUri) if rootUri else rootPath
        self._analyser = MROAnalyser(root_dir=root_dir)
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
        self._analyser.replace_script_content(
            self.uri_to_abs_path(textDocument['uri']),
            textDocument['text']
        )

    def m_text_document__did_change(self,
                                    textDocument=None,
                                    contentChanges=None):
        """Update the stored document contents according to the sync kind."""
        if not contentChanges:
            return
        if self._sync_kind == self.SYNC_FULL:
            self._analyser.replace_script_content(
                self.uri_to_abs_path(textDocument['uri']),
                contentChanges[0]['text']
            )
        elif self._sync_kind == self.SYNC_INCREMENTAL:
            for change in contentChanges:
                self._analyser.update_script_content(
                    self.uri_to_abs_path(textDocument['uri']),
                    (change['range']['start']['line'],
                     change['range']['start']['character']),
                    (change['range']['end']['line'],
                     change['range']['end']['character']), change['text'])

    def m_text_document__hover(self,
                               textDocument=None,
                               position=None,
                               **_kwargs):
        """Calculate and return the hover result."""
        return self._analyser.update_fetch_hover(
            self.uri_to_abs_path(textDocument['uri']),
            (position['line'], position['character'])
        )

    def m_text_document__code_lens(self, textDocument=None, **_kwargs):
        """Calculate and return the code lens list."""
        return self._analyser.update_fetch_code_lens(
            self.uri_to_abs_path(textDocument['uri'])
        )

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

    @staticmethod
    def uri_to_abs_path(uri: str) -> str:
        """
        Convert an URI to a file path.

        Args:
            uri: the URI to convert
        
        Returns:
            The file path of the URI
        """
        return abspath(unquote(urlparse(uri).path))
