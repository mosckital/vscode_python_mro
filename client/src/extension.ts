import * as path from "path";
import {
    LanguageClient, ServerOptions, TransportKind, LanguageClientOptions
} from 'vscode-languageclient';
import { ExtensionContext, window, commands } from "vscode";

let client : LanguageClient;

export function activate(context: ExtensionContext) {
    // get the absolute path of the compiled server.js
    let serverModule = context.asAbsolutePath(path.join('server', 'out', 'server.js'));
    // the extra options for debug
    // --inspect=6009: runs the server in Node's Inspector mode so VS Code can attach to the server for debugging
    let debugOptions = {
        execArgv: ['--nolazy', '--inspect=6009']
    };
    // all possible server options, currently two: run mode & debug mode
    let serverOptions: ServerOptions = {
        run: {module: serverModule, transport: TransportKind.ipc},
        debug: {
            module: serverModule,
            transport: TransportKind.ipc,
            options: debugOptions
        }
    };
    // the language client options
    let clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'python' }]
    };

    // create the language client
    client = new LanguageClient(
        'pythonMro',
        'Python MRO',
        serverOptions,
        clientOptions
    );

    // define the command handler for the show MRO command
    let showMroCommand = 'pythonMRO.showMRO';
    const showMroHandler = (content: string = 'No MRO List provided!') => {
        // show the MRO list in the right bottom pop-up box
        window.showInformationMessage(content);
    };

    context.subscriptions.push(commands.registerCommand(showMroCommand, showMroHandler));

    // start the client
    // this will also launch the server by launching the complied script
    client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}