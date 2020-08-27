/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */

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

/**
 * Activates the Python MRO extension
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

export async function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

export async function waitFor(condition: () => boolean, timeout: number = 5000) {
	let interval = 100;
	while (!condition() && timeout > 0) {
		await sleep(interval);
		timeout -= interval;
	}
	return condition();
}

export const getDocPath = (p: string) => {
	return path.resolve(__dirname, '../../../tests/examples', p);
};
export const getDocUri = (p: string) => {
	return vscode.Uri.file(getDocPath(p));
};
export const getYamlPath = (p: string) => {
	return path.resolve(__dirname, '../../../tests/example_stats', p);
};

export async function setTestContent(content: string): Promise<boolean> {
	const all = new vscode.Range(
		doc.positionAt(0),
		doc.positionAt(doc.getText().length)
	);
	return editor.edit(eb => eb.replace(all, content));
}

// dummy content to populate into test docs for testing
let dummyNewContent = `


class Test:
	pass
`;

/**
 * Add dummy content to a doc for testing purpose.
 * @param docUri the uri of the doc to add dummy content
 */
export async function addContent(docUri: vscode.Uri) {
	try {
		let doc = await vscode.workspace.openTextDocument(docUri);
		let editor = await vscode.window.showTextDocument(doc);
		editor.edit(builder => {
			let nLines = doc.lineCount;
			let nCharLastLine = doc.lineAt(nLines - 1).text.length;
			builder.insert(new vscode.Position(nLines, nCharLastLine), dummyNewContent);
		});
	} catch (e) {
		console.error(e);
	}
}

export function readYamlFile(yamlFileName: string) {
	return yaml.safeLoad(readFileSync(getYamlPath(yamlFileName), 'utf8'));
}