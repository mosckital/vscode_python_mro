import * as vscode from 'vscode';
import * as path from 'path';
import * as yaml from 'js-yaml';
import { readFileSync } from 'fs';

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
 * Get the path of a test document given its name.
 * All test documents are in a same folder.
 * @param p the test document name
 */
export const getDocPath = (p: string) => {
	return path.resolve(__dirname, '../../../tests/examples', p);
};

/**
 * Get the uri of a test document given its name.
 * @param p the test document name
 */
export const getDocUri = (p: string) => {
	return vscode.Uri.file(getDocPath(p));
};

/**
 * Get the path of a test stats YAML document given its name.
 * All test stats documents are in a same folder.
 * @param p the test stats document name
 */
export const getYamlPath = (p: string) => {
	return path.resolve(__dirname, '../../../tests/example_stats', p);
};

/**
 * Read the target YAML file in the YAMl file folder.
 * @param yamlFileName the name of the target yaml file
 */
export function readYamlFile(yamlFileName: string) {
	return yaml.safeLoad(readFileSync(getYamlPath(yamlFileName), 'utf8'));
}

//#endregion sys_utils