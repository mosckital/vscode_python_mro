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
 * The enumerations of the possible logging levels.
 */
enum LogLevel {
    DEBUG,
    INFO,
    WARNING,
    ERROR,
}

// the logging level threshold
let loggingLevel = LogLevel.DEBUG;

/**
 * Show the logging information in the provided output channel.
 * @param output the output channel to show
 * @param level the level string of the logging information level
 * @param msg the message to log
 */
function logToOutput(output: OutputChannel, level: LogLevel, msg: string) {
    if (level > loggingLevel) {
        output.appendLine(`[${new Date().toLocaleTimeString()}]-${LogLevel[level]}: ${msg}`);
    }
}

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
    logToOutput(outputChannel, LogLevel.INFO, `Ready to get an available port and to start the MRO server`);
    let connectionPort = 0;
    (async () => {
        connectionPort = await getPort({port: [3000, 3001, 3002]});
        logToOutput(outputChannel, LogLevel.INFO, `Got an available port ${connectionPort}`);
        // console.info(`using port ${connectionPort}`);
        startMroServer(connectionPort);
    })();

    // server options knows how to connect to the MRO server
    logToOutput(outputChannel, LogLevel.INFO, `Ready to define the ServerOptions`);
    const serverOptions: ServerOptions = function() {
		return new Promise((resolve, reject) => {
            let socketClient = new net.Socket();
            logToOutput(outputChannel, LogLevel.INFO, `Ready to connect to the MRO server via socket`);
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
    logToOutput(outputChannel, LogLevel.INFO, `Ready to define the LanguageClientOptions`);
    let clientOptions: LanguageClientOptions = {
        documentSelector: [{ scheme: 'file', language: 'python' }]
    };

    // create the language client
    logToOutput(outputChannel, LogLevel.INFO, `Ready to instantiate a LanguageClient`);
    client = new LanguageClient(
        'pythonMro',
        extTitle,
        serverOptions,
        clientOptions
    );

    // define the command handler for the show MRO command
    logToOutput(outputChannel, LogLevel.INFO, `Ready to register the show MRO command`);
    let showMroCommand = 'pythonMRO.showMRO';
    const showMroHandler = (content: string = 'No MRO List provided!') => {
        // show the MRO list in the right bottom pop-up box
        window.showInformationMessage(content);
    };
    // register command
    context.subscriptions.push(commands.registerCommand(showMroCommand, showMroHandler));
    logToOutput(outputChannel, LogLevel.INFO, `Finished the registration of the show MRO command`);

    // delay the start of the client until the MRO server is connected
    logToOutput(outputChannel, LogLevel.INFO, `Ready to wait for the launch of MRO server and to start the client`);
    (async () => {
        logToOutput(outputChannel, LogLevel.INFO, `Wait for the start of the MRO server`);
        let startWaitTime = Date.now();
        while (!connectionEstablished) {
            await sleep(1000);
            if (Date.now() - startWaitTime > 3000) {
                break;
            }
        }
        logToOutput(outputChannel, LogLevel.INFO, `MRO server is ready`);
        logToOutput(outputChannel, LogLevel.INFO, `Ready to start the client`);
        client.start();
    })();
}

function startMroServer(port: number) {
    logToOutput(outputChannel, LogLevel.INFO, `Ready to start MRO Server`);
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
    logToOutput(outputChannel, LogLevel.INFO, `MRO server process spawned`);
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
    logToOutput(outputChannel, LogLevel.INFO, `MRO server handlers registered`);
}

export function deactivate(): Thenable<void> | undefined {
    logToOutput(outputChannel, LogLevel.INFO, `Ready to deactivate the Python MRO extension`);
    if (!client) {
        return undefined;
    }
    return killMROServerProcess().then((result) => {
        return client.stop();
    });
}

async function killMROServerProcess() {
    logToOutput(outputChannel, LogLevel.INFO, `Ready to kill the MRO server process`);
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
    logToOutput(outputChannel, LogLevel.INFO, `MRO server process is killed`);
    return Promise.resolve(true);
}