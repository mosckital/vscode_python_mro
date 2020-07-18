import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate, checkDummyMROContent, addContent } from './helper';

suite('Should show CodeLens', () => {
	const docUri = getDocUri('diamond.py');

	test('Show CodeLenses in diamond.py', async () => {
		await testCodeLens(docUri, 4);
	});

	test('Show CodeLenses after adding new class', async () => {
		await addContent(docUri);
		await testCodeLens(docUri, 5);
	});
});

async function testCodeLens(
	docUri: vscode.Uri,
	expectedCodeLensNumber: number
) {
	await activate(docUri);
	// check the number of code lenses is correct
	let actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri
	)) as vscode.CodeLens[];
	assert.ok(actualCodeLenses.length === expectedCodeLensNumber);
	// resolve the code lenses and check the contents are correct
	actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri,
		expectedCodeLensNumber
	)) as vscode.CodeLens[];
	actualCodeLenses.forEach(lens => {
		let content = lens.command.arguments[0] as string;
		let lines = content.split('\n');
		assert.ok(checkDummyMROContent(lines));
	});
	// TODO: to add the check for the contents once the functionality has been
	// fully implemented
}