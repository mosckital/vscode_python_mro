import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate } from './helper';

suite('Should show CodeLens', () => {
	const docUri = getDocUri('diamond.py');

	test('Show CodeLenses in diamond.py', async () => {
		await testCodeLens(docUri, 4);
	});
});

async function testCodeLens(
	docUri: vscode.Uri,
	expectedCodeLensNumber: number
) {
	await activate(docUri);
	const actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri
	)) as vscode.CodeLens[];
	assert.ok(actualCodeLenses.length === expectedCodeLensNumber);
	// TODO: to add the check for the contents once the functionality has been
	// fully implemented
}