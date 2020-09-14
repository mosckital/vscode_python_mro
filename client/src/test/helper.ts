import * as vscode from 'vscode';
import * as path from 'path';
import * as yaml from 'js-yaml';
import * as glob from 'glob';
import { readFileSync, existsSync } from 'fs';

export let doc: vscode.TextDocument;
export let editor: vscode.TextEditor;
export let documentEol: string;
export let platformEol: string;

// module-level variables
let isMROServerUp : boolean;

//#region extension_utils

/**
 * Activate a document in the editor.
 * This will activate the extension if not activated yet.
 * @param docUri the uri of the document to activate
 */
export async function activate(docUri: vscode.Uri) {
	// The extensionId is `publisher.name` from package.json
	const ext = vscode.extensions.getExtension('kaiyan.python-mro')!;
	await ext.activate();
	try {
		doc = await vscode.workspace.openTextDocument(docUri);
		editor = await vscode.window.showTextDocument(doc);
		// Wait for server start-up, timeout is 10s
		let startCheckTime = Date.now();
		while (!isMROServerUp) {
			isMROServerUp = await checkMROServerUpByDoc(docUri);
			await sleep(500);
			if (Date.now() - startCheckTime > 10 * 1000) {
				break;
			}
		}
	} catch (e) {
		console.error(e);
	}
}

/**
 * Check if the Python MRO server is up by checking code lens reply of the given doc.
 * @param docUri the uri of the document
 */
async function checkMROServerUpByDoc(docUri: vscode.Uri) {
	let actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri
	)) as vscode.CodeLens[];
	return actualCodeLenses.length > 0;
}

/**
 * Open a document in editor and add new content to its end.
 * @param docUri the uri of the document to add content
 * @param content the content to add into the document
 */
export async function addContent(docUri: vscode.Uri, content: string) {
	try {
		// open the doc in editor
		let doc = await vscode.workspace.openTextDocument(docUri);
		let editor = await vscode.window.showTextDocument(doc);
		// add content to the end
		editor.edit(builder => {
			let nLines = doc.lineCount;
			let nCharLastLine = doc.lineAt(nLines - 1).text.length;
			builder.insert(new vscode.Position(nLines, nCharLastLine), content);
		});
	} catch (e) {
		console.error(e);
	}
}

//#endregion extension_utils

//#region sys_utils

/**
 * Sleep for the given time.
 * @param ms millisecond to sleep
 */
export async function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Wait until the condition is satisfied, or passing the given timeout.
 * @param condition the condition function to judge if no longer to wait
 * @param timeout the timeout in ms
 */
export async function waitFor(condition: () => boolean, timeout: number = 5000) {
	let interval = 100;  // the time length of each small wait
	while (!condition() && timeout > 0) {
		await sleep(interval);
		timeout -= interval;
	}
	return condition();
}

/**
 * Get all the pairs of test example files and their correspondent stats files.
 * The test example file will then be represented as a vscode.Uri and the stats
 * file will be loaded into an object for further processing.
 * @param exDir the directory of the example files
 * @param statsDir the directory of the stats files
 */
function getExampleStatsPairs(exDir: string, statsDir: string) {
	// get all the Python files at first
	let candidateFiles = glob.sync(path.join(exDir, '**/[!_]*.py'));
	let cacheFiles = glob.sync(path.join(exDir, '**/__pycache__/*'));
	let exFiles = candidateFiles.filter(
		(candidate) => !cacheFiles.includes(candidate)
	);
	// place holder for the wanted pairs
	type statsObject = {
		code_lenses?: any[],
		negative_cases?: any[],
		dummy_content?: string[],
		dummy_code_lens?: any,
	};
	var pairs : [vscode.Uri, statsObject][] = [];
	exFiles.forEach(exFile => {
		let statsFile = exFile.replace(exDir, statsDir).replace('.py', '.yaml');
		if (existsSync(statsFile)) {
			pairs.push([
				vscode.Uri.file(exFile),
				yaml.safeLoad(readFileSync(statsFile, 'utf8')) as statsObject,
			]);
		}
	});
	return pairs;
}

/**
 * The prepared list of all the pairs of the test example files and their
 * correspondent stats files in the project.
 * The test example files are represented as a vscode.Uri and the stats files
 * are loaded into an object for further processing.
 */
export const EX_STATS_PAIRS = getExampleStatsPairs(
	path.resolve(__dirname, '../../../tests/examples'),
	path.resolve(__dirname, '../../../tests/example_stats'),
);

//#endregion sys_utils