import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate, addContent } from './helper';

suite('Should show CodeLens', () => {
	const docUri = getDocUri('diamond.py');

	test('Show CodeLenses in diamond.py', async () => {
		await testCodeLens(docUri, 4, [
			['Generic'], ['A'], ['A'], ['B', 'C'],
		]);
	});

	test('Show CodeLenses after adding new class', async () => {
		await addContent(docUri);
		await testCodeLens(docUri, 5, [
			['Generic'], ['A'], ['A'], ['B', 'C'], [''],
		]);
	});
});

async function testCodeLens(
	docUri: vscode.Uri,
	expectedCodeLensNumber: number,
	data: String[][]
) {
	await activate(docUri);
	// check the number of code lenses is correct
	let actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri
	)) as vscode.CodeLens[];
	assert.equal(actualCodeLenses.length, expectedCodeLensNumber);
	// resolve the code lenses and check the contents are correct
	actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri,
		expectedCodeLensNumber
	)) as vscode.CodeLens[];
	// to check if the content values are correct
	// TODO: update the check from only base parents to MRO list once implemented
	for (var i = 0; i < expectedCodeLensNumber; i++) {
		let content = actualCodeLenses[i].command.arguments[0] as string;
		let lines = content.split('\n');
		assert.equal(lines.length, data[i].length);
		for (var j = 0; j < lines.length; j++) {
			assert.equal(lines[j], data[i][j]);
		}
	}
}