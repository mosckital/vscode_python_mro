import * as net from 'net';
import {
    LanguageClient, ServerOptions, LanguageClientOptions
} from 'vscode-languageclient';
import { ExtensionContext, window, commands, extensions, CodeAction, OutputChannel } from "vscode";
import * as cp from "child_process";
import * as getPort from "get-port";

// module-level variable place holders
let client : LanguageClient;
let mroServerProcess : cp.ChildProcess;
let outputChannel : OutputChannel;

/**
 * Async sleep.
 * @param ms - milliseconds to sleep
 */
async function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

export function activate(context: ExtensionContext) {
    let connectionEstablished = false;

    let extTitle = 'Python MRO';

    // create an output channel for output debug information
    outputChannel = window.createOutputChannel(extTitle);
    context.subscriptions.push(outputChannel);

    // get an available port and start the MRO server
    outputChannel.appendLine(`Ready to get an available port and to start the MRO server`);
    let connectionPort = 0;
    (async () => {
        connectionPort = await getPort({port: [3000, 3001, 3002]});
        outputChannel.appendLine(`Got an available port ${connectionPort}`);
        // console.info(`using port ${connectionPort}`);
        startMroServer(connectionPort);
    })();

    // server options knows how to connect to the MRO server
    outputChannel.appendLine(`Ready to define the ServerOptions`);
    const serverOptions: ServerOptions = function() {
		return new Promise((resolve, reject) => {
            let socketClient = new net.Socket();
            outputChannel.appendLine(`Ready to connect to the MRO server via socket`);
			socketClient.connect(connectionPort, "127.0.0.1", function() {
                connectionEstablished = true;
				resolve({
                    reader: socketClient,
                    writer: socketClient
				});
            });
		});
    };
    // the language client options
    outputChannel.appendLine(`Ready to define the LanguageClientOptions`);
    let clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'python' }]
    };

    // create the language client
    outputChannel.appendLine(`Ready to instantiate a LanguageClient`);
    client = new LanguageClient(
        'pythonMro',
        extTitle,
        serverOptions,
        clientOptions
    );

    // define the command handler for the show MRO command
    outputChannel.appendLine(`Ready to register the show MRO command`);
    let showMroCommand = 'pythonMRO.showMRO';
    const showMroHandler = (content: string = 'No MRO List provided!') => {
        // show the MRO list in the right bottom pop-up box
        window.showInformationMessage(content);
    };
    // register command
    context.subscriptions.push(commands.registerCommand(showMroCommand, showMroHandler));
    outputChannel.appendLine(`Finished the registration of the show MRO command`);

    // delay the start of the client until the MRO server is connected
    outputChannel.appendLine(`Ready to wait for the launch of MRO server and to start the client`);
    (async () => {
        outputChannel.appendLine(`Wait for the start of the MRO server`);
        let startWaitTime = Date.now();
        while (!connectionEstablished) {
            await sleep(1000);
            if (Date.now() - startWaitTime > 3000) {
                break;
            }
        }
        outputChannel.appendLine(`MRO server is ready`);
        outputChannel.appendLine(`Ready to start the client`);
        client.start();
    })();
}

function startMroServer(port: number) {
    outputChannel.appendLine(`Ready to start MRO Server`);
    // get extension root path
    let extPath = extensions.getExtension('kaiyan.python-mro').extensionPath;
    // use spawn to run the long-live MRO server instead of using 
    mroServerProcess = cp.spawn('python3', [
        // 'run', 'python -m python_server.server'
        '-m mrols.server', `${port}`
    ], {
        cwd: extPath,
        shell: true,
        detached: true
    });
    outputChannel.appendLine(`MRO server process spawned`);
    // unreference the MRO server process
    mroServerProcess.unref();
    // redirect the MRO server process I/O into this main process
    mroServerProcess.stdout.on('data', (data) => {
        console.log(`MRO Server stdout: ${data}`);
    });
    mroServerProcess.stderr.on('data', (data) => {
        console.error(`MRO Server stderr: ${data}`);
    });
    mroServerProcess.on('close', (code) => {
        console.log(`MRO Server process exited with code ${code}`);
    });
    // kill the MRO server process in case of abnormal exit, like in unit test
    process.on('exit', killMROServerProcess);
    outputChannel.appendLine(`MRO server handlers registered`);
}

export function deactivate(): Thenable<void> | undefined {
    outputChannel.appendLine(`Ready to deactivate the Python MRO extension`);
    if (!client) {
        return undefined;
    }
    return killMROServerProcess().then((result) => {
        return client.stop();
    });
}

async function killMROServerProcess() {
    outputChannel.appendLine(`Ready to kill the MRO server process`);
    let startKillTime = Date.now();
    while (!mroServerProcess.killed) {
        console.log(`Stopping the Python MRO language server process of PID ${mroServerProcess.pid}`);
        // use `process.kill(pid)` instead of `mroServerProcess.kill()` as the
        // latter does not work due to unrecognised reason
        // If pid is less than -1, then sig is sent to every process in the
        // process group whose ID is -pid.
        process.kill(-mroServerProcess.pid);
        await sleep(1000);
        if (Date.now() - startKillTime > 10 * 1000) {
            return Promise.resolve(false);
        }
    }
    outputChannel.appendLine(`MRO server process is killed`);
    return Promise.resolve(true);
}