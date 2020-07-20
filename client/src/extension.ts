import * as path from "path";
import * as net from 'net';
import {
    LanguageClient, ServerOptions, TransportKind, LanguageClientOptions
} from 'vscode-languageclient';
import { ExtensionContext, window, commands, workspace, extensions } from "vscode";
import * as cp from "child_process";

let client : LanguageClient;
let mroServerProcess : cp.ChildProcess;

async function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

export function activate(context: ExtensionContext) {
    // get the absolute path of the compiled server.js
    let serverModule = context.asAbsolutePath(path.join('server', 'out', 'server.js'));
    // the extra options for debug
    // --inspect=6009: runs the server in Node's Inspector mode so VS Code can attach to the server for debugging
    let debugOptions = {
        execArgv: ['--nolazy', '--inspect=6009']
    };
    let connectionEstablished = false;
    const serverOptions: ServerOptions = function() {
		return new Promise((resolve, reject) => {
            var socketClient = new net.Socket();
			socketClient.connect(3000, "127.0.0.1", function() {
                connectionEstablished = true;
				resolve({
                    reader: socketClient,
                    writer: socketClient
				});
			});
		});
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

    // let root_folder = workspace.workspaceFolders[0].uri.fsPath + '/../../';
    let extPath = extensions.getExtension('kaiyan.python-mro').extensionPath;
    let mroServerProcess = cp.exec(`cd ${extPath}; pipenv run python -m python_server.server`, (err, stdout, stderr) => {
        if (err) {
            console.error(err);
            return;
        }
        console.log(stdout);
    });

    async function terminateMroServer() {
        // cp.exec('fuser -k 3000/tcp');
        let signal_result = mroServerProcess.kill('SIGINT');
        let killed = mroServerProcess.killed;
        process.exit(0);
    }

    process.on('SIGINT', terminateMroServer);
    process.on('exit', terminateMroServer);

    // delay the start of the client until the MRO server is connected
    (async () => {
        let startWaitTime = Date.now();
        while (!connectionEstablished) {
            await sleep(1000);
            if (Date.now() - startWaitTime > 3000) {
                break;
            }
        }
        client.start();
    })();

    // start the client
    // this will also launch the server by launching the complied script
    // client.start();
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return client.stop();
}