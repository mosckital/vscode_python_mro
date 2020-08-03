import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate, checkDummyMROContent } from './helper';

suite('Should show Hover', () => {
	const docUri = getDocUri('diamond.py');

	test('All class names should show hover', async () => {
		// activate the extension and open the document
		await activate(docUri);
		await testHover(docUri, new vscode.Position(8, 6), true);
		await testHover(docUri, new vscode.Position(23, 6), true);
		await testHover(docUri, new vscode.Position(35, 6), true);
		await testHover(docUri, new vscode.Position(47, 6), true);
	});

	test('Keyword class should not show hover', async () => {
		// activate the extension and open the document
		await activate(docUri);
		await testHover(docUri, new vscode.Position(8, 3), false);
		await testHover(docUri, new vscode.Position(23, 0), false);
		await testHover(docUri, new vscode.Position(35, 5), false);
		await testHover(docUri, new vscode.Position(47, 4), false);
	});

	test('Base class list should not show hover', async () => {
		// activate the extension and open the document
		await activate(docUri);
		await testHover(docUri, new vscode.Position(8, 10), false);
		await testHover(docUri, new vscode.Position(23, 8), false);
		await testHover(docUri, new vscode.Position(35, 7), false);
		await testHover(docUri, new vscode.Position(47, 10), false);
	});

	test('Function or other statement should not show hover', async () => {
		// activate the extension and open the document
		await activate(docUri);
		await testHover(docUri, new vscode.Position(2, 6), false);
		await testHover(docUri, new vscode.Position(5, 0), false);
		await testHover(docUri, new vscode.Position(25, 10), false);
		await testHover(docUri, new vscode.Position(53, 18), false);
	});
});

async function testHover(
	docUri: vscode.Uri,
	hoverPosition: vscode.Position,
	should_hover: boolean
) {
	// check if the number of returned hover results is correct
	const actualHoverResults = (await vscode.commands.executeCommand(
		'vscode.executeHoverProvider',
		docUri,
		hoverPosition,
	)) as vscode.Hover[];
	assert.equal(actualHoverResults.length > 0, should_hover);
	// check if the content of the returned hover is correct
	if (!should_hover) {
		return;
	}
	let foundMRO = false;
	actualHoverResults.forEach(hover => {
		if (hover.contents.length > 0) {
			// foundMRO = checkDummyMROContent(hover.contents);
			// TODO: to add the check for real MRO info
			foundMRO = true;
		}
	});
	assert.ok(foundMRO);
	// TODO: to add the check for the contents once the functionality has been
	// fully implemented
}