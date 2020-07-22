import * as net from 'net';
import {
    LanguageClient, ServerOptions, LanguageClientOptions
} from 'vscode-languageclient';
import { ExtensionContext, window, commands, extensions } from "vscode";
import * as cp from "child_process";

// module-level variable place holders
let client : LanguageClient;
let mroServerProcess : cp.ChildProcess;

/**
 * Async sleep.
 * @param ms - milliseconds to sleep
 */
async function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

export function activate(context: ExtensionContext) {
    let connectionEstablished = false;
    // server options knows how to connect to the MRO server
    const serverOptions: ServerOptions = function() {
		return new Promise((resolve, reject) => {
            let socketClient = new net.Socket();
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
    // register command
    context.subscriptions.push(commands.registerCommand(showMroCommand, showMroHandler));

    // get extension root path
    let extPath = extensions.getExtension('kaiyan.python-mro').extensionPath;
    // use spawn to run the long-live MRO server instead of using 
    mroServerProcess = cp.spawn('pipenv', [
        'run', 'python -m python_server.server'
    ], {
        cwd: extPath,
        shell: true,
        detached: true
    });
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
}

export function deactivate(): Thenable<void> | undefined {
    if (!client) {
        return undefined;
    }
    return killMROServerProcess().then((result) => {
        return client.stop();
    });
}

async function killMROServerProcess() {
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
    return Promise.resolve(true);
}