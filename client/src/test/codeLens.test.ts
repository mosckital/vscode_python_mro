import * as vscode from 'vscode';
import * as assert from 'assert';
import { getDocUri, activate, addContent, readYamlFile, waitFor, dummyNewCodeLens } from './helper';

suite('Should show CodeLens', () => {
	const docUri = getDocUri('diamond.py');

	const expectedInfo = readYamlFile('diamond_stats.yml') as {
		code_lenses: any[],
		negative_cases: any[],
	};

	let finishedCodeLenses = false;
	let finishedNegativeCases = false;

	test('Check CodeLenses are corrected identified', async () => {
		await testCodeLenses(docUri, expectedInfo.code_lenses);
		finishedCodeLenses = true;
	});

	test('Check against the negative cases', async () => {
		await testNegativeCases(docUri, expectedInfo.negative_cases);
		finishedNegativeCases = true;
	});

	test('Check correctness after adding content', async () => {
		await waitFor(() => (finishedCodeLenses && finishedNegativeCases), 3000);
		await addContent(docUri);
		let updatedLenses = expectedInfo.code_lenses;
		updatedLenses.push(dummyNewCodeLens);
		await testCodeLenses(docUri, updatedLenses);
	});
});

async function testCodeLenses(
	docUri: vscode.Uri,
	expectedCodeLenses: { location: number[], mro: string[] }[],
) {
	// wait the target document open in editor
	await activate(docUri);
	// fetch code lens list from editor
	let actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri
	)) as vscode.CodeLens[];
	// check the number of code lenses is correct
	assert.equal(actualCodeLenses.length, expectedCodeLenses.length);
	// resolve the code lenses and check the contents are correct
	actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri,
		expectedCodeLenses.length
	)) as vscode.CodeLens[];
	// check the content of the resolved code lenses are correct
	actualCodeLenses.forEach(lens => {
		let found = false;
		expectedCodeLenses.forEach(expected => {
			if ((!found) && lens.range.contains(
				new vscode.Position(expected.location[0], expected.location[1])
			)) {
				assert.ok(lens.command);
				let content = lens.command.arguments[0] as string;
				let lines = content.split('\n');
				assert.equal(lines.length, expected.mro.length);
				assert.deepEqual(lines, expected.mro);
				found = true;
			}
		});
		assert.ok(found);
	});
};

async function testNegativeCases(
	docUri: vscode.Uri,
	negativeCases: { location: number[] }[],
) {
	// wait the target document open in editor
	await activate(docUri);
	// fetch code lens list from editor
	let actualCodeLenses = (await vscode.commands.executeCommand(
		'vscode.executeCodeLensProvider',
		docUri
	)) as vscode.CodeLens[];
	// check all negative cases are not in found code lens ranges
	negativeCases.forEach(negativeCase => {
		actualCodeLenses.forEach(lens => {
			assert.ok(!lens.range.contains(
				new vscode.Position(negativeCase.location[0], negativeCase.location[1])
			));
		});
	});
};