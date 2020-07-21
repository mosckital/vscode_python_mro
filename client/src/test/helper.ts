/* --------------------------------------------------------------------------------------------
 * Copyright (c) Microsoft Corporation. All rights reserved.
 * Licensed under the MIT License. See License.txt in the project root for license information.
 * ------------------------------------------------------------------------------------------ */

import * as vscode from 'vscode';
import * as path from 'path';

export let doc: vscode.TextDocument;
export let editor: vscode.TextEditor;
export let documentEol: string;
export let platformEol: string;
let isMROServerUp : boolean;

/**
 * Activates the vscode.lsp-sample extension
 */
export async function activate(docUri: vscode.Uri) {
	// The extensionId is `publisher.name` from package.json
	const ext = vscode.extensions.getExtension('kaiyan.python-mro')!;
	await ext.activate();
	try {
		doc = await vscode.workspace.openTextDocument(docUri);
		editor = await vscode.window.showTextDocument(doc);
		// Wait for server activation
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

async function checkMROServerUpByDoc(docUri: vscode.Uri) {
	let actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri
	)) as vscode.CodeLens[];
	return actualCodeLenses.length > 0;
}

async function sleep(ms: number) {
	return new Promise(resolve => setTimeout(resolve, ms));
}

export const getDocPath = (p: string) => {
	return path.resolve(__dirname, '../../../tests/examples', p);
};
export const getDocUri = (p: string) => {
	return vscode.Uri.file(getDocPath(p));
};

export async function setTestContent(content: string): Promise<boolean> {
	const all = new vscode.Range(
		doc.positionAt(0),
		doc.positionAt(doc.getText().length)
	);
	return editor.edit(eb => eb.replace(all, content));
}

export const checkDummyMROContent = (contents: vscode.MarkedString[]) => {
	let firstLine = contents[0];
	let firstLineContent: string;
	if (typeof firstLine === 'string') {
		firstLineContent = firstLine;
	} else {
		firstLineContent = firstLine.value;
	}
	if (firstLineContent === 'Target class name') {
		return true;
	} else {
		return false;
	}
};

let dummyNewContent = `


class Test:
	pass
`;

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