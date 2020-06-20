import { createConnection, ProposedFeatures, TextDocuments, InitializeParams, InitializeResult, TextDocumentSyncKind, CodeLens, CodeLensParams, CompletionItem, CompletionItemKind, TextDocumentPositionParams, HoverParams, Hover } from 'vscode-languageserver';
import { TextDocument } from 'vscode-languageserver-textdocument';

// create a connection for the server
let connection = createConnection(ProposedFeatures.all);

// create a simple text document manager
let documents: TextDocuments<TextDocument> = new TextDocuments(TextDocument);

connection.onInitialize((params: InitializeParams) => {
    // simply return the server capabilities
    console.log('Initialising Python MRO language server.');
    const result: InitializeResult = {
        capabilities: {
            textDocumentSync: TextDocumentSyncKind.Incremental,
            codeLensProvider: {
                resolveProvider: true
            },
            hoverProvider: true
        }
    };
    return result;
});

// function to identify the CodeLenses in a document
function findClassInTextDocument(textDocument: TextDocument): CodeLens[] {
    console.log(`Searching Python classes in ${textDocument.uri}`);
    // initiate search scope and pattern
    let text = textDocument.getText();
    let pattern = /\bclass\b/g;
    let m: RegExpExecArray | null;
    // find classes and create CodeLenses one by one
    let codeLenses: CodeLens[] = [];
    while (m = pattern.exec(text)) {
        let codeLens: CodeLens = {
            range: {
                start: textDocument.positionAt(m.index),
                end: textDocument.positionAt(m.index + m[0].length)
            }
        };
        codeLenses.push(codeLens);
    }
    console.log(`${codeLenses.length} CodeLens have been found in ${textDocument.uri}`);
    return codeLenses;
};

connection.onCodeLens((codeLensParams: CodeLensParams): CodeLens[] => {
    console.log('Inside onCodeLens() for ' + codeLensParams.textDocument.uri);
    let textDocument = documents.get(codeLensParams.textDocument.uri);
    if (textDocument){
        return findClassInTextDocument(textDocument);
    }
    return [];
});

connection.onCodeLensResolve((lens: CodeLens): CodeLens => {
    console.log(`Resolving CodeLens ${lens}`);
    lens.command = {
        command: 'pythonMRO.showMRO',
        title: 'Show MRO list',
        arguments: [
            'Fake MRO List L1\nFake MRO List L2\nFake MRO List L3'
        ]
    };
    return lens;
});

connection.onHover((hoverParams: HoverParams): Hover => {
    console.log(`Providing Hover in ${hoverParams.textDocument.uri} for line ${hoverParams.position.line} char ${hoverParams.position.character}`);
    let hover: Hover = {
        contents: [
            'Target class name',
            'Parent class 1',
            'Parent class 2',
            '...',
            'Object'
        ]
    };
    return hover;
});

console.log('Python MRO language server registered callbacks.');

documents.listen(connection);

connection.listen();