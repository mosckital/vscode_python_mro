import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate } from './helper';

suite('Should show Hover', () => {
	const docUri = getDocUri('diamond.py');

	test('All class names should show hover', async () => {
		// activate the extension and open the document
		await activate(docUri);
		await testHover(docUri, new vscode.Position(8, 6), true, ['A', 'Generic', 'object']);
		await testHover(docUri, new vscode.Position(23, 6), true, ['B', 'A', 'Generic', 'object']);
		await testHover(docUri, new vscode.Position(35, 6), true, ['C', 'A', 'Generic', 'object']);
		await testHover(docUri, new vscode.Position(47, 6), true, ['D', 'B', 'C', 'A', 'Generic', 'object']);
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
	should_hover: boolean,
	hover_contents: string[] = undefined,
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
		if (hover.contents.length === hover_contents.length) {
			// to check if the content values are correct
			// TODO: update the check from only base parents to MRO list once implemented
			foundMRO = true;
			for (var i = 0; i < hover_contents.length && foundMRO; i++) {
				var content = hover.contents[i];
				if (typeof content === 'string') {
					content = content;
				} else {
					content = content.value;
				}
				if (content !== hover_contents[i]) {
					foundMRO = false;
				}
			}
		}
	});
	assert.ok(foundMRO);
}