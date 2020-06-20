import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate } from './helper';

suite('Should show Hover', () => {
	const docUri = getDocUri('diamond.py');

	test('Show Hover in diamond.py', async () => {
		await testHover(docUri, new vscode.Position(9, 3));
	});
});

async function testHover(
	docUri: vscode.Uri,
	hoverPosition: vscode.Position
) {
	await activate(docUri);
	const actualHoverResults = (await vscode.commands.executeCommand(
		'vscode.executeHoverProvider',
		docUri,
		hoverPosition,
	)) as vscode.Hover[];
	assert.ok(actualHoverResults.length > 0);
	let foundMRO = false;
	actualHoverResults.forEach(hover => {
		if (hover.contents.length > 0) {
			let firstLine = hover.contents[0];
			let firstLineContent: string;
			if (typeof firstLine === 'string') {
				firstLineContent = firstLine;
			} else {
				firstLineContent = firstLine.value;
			}
			if (firstLineContent === 'Target class name') {
				foundMRO = true;
			}
		}
	});
	assert.ok(foundMRO);
	// TODO: to add the check for the contents once the functionality has been
	// fully implemented
}