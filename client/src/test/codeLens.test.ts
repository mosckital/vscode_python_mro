import * as vscode from 'vscode';
import * as assert from 'assert';
import { activate, addContent, waitFor, EX_STATS_PAIRS } from './helper';

suite('Should show CodeLens', () => {
	EX_STATS_PAIRS.forEach(([exUri, statsObj]) => {
		let finishedCodeLenses = false;
		let finishedNegativeCases = false;

		if (statsObj.code_lenses) {
			test('Check CodeLenses are corrected identified', async () => {
				await testCodeLenses(exUri, statsObj.code_lenses);
				finishedCodeLenses = true;
			});
		}

		if (statsObj.negative_cases) {
			test('Check against the negative cases', async () => {
				await testNegativeCases(exUri, statsObj.negative_cases);
				finishedNegativeCases = true;
			});
		}

		if (statsObj.dummy_content && statsObj.dummy_code_lens) {
			test('Check correctness after adding content', async () => {
				// we should wait until the tests on the original content have finished
				await waitFor(() => (finishedCodeLenses && finishedNegativeCases), 3000);
				let newContent = statsObj.dummy_content.join('\n');
				await addContent(exUri, newContent);
				let updatedLenses = statsObj.code_lenses;
				updatedLenses.push(statsObj.dummy_code_lens);
				await testCodeLenses(exUri, updatedLenses);
			});
		}
	});
});

/**
 * Test if the code lenses can be corrected populated.
 * @param docUri the uri of the target document
 * @param expectedCodeLenses the expected code lenses
 */
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
	assert.strictEqual(actualCodeLenses.length, expectedCodeLenses.length);
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
				assert.strictEqual(lines.length, expected.mro.length);
				assert.deepStrictEqual(lines, expected.mro);
				found = true;
			}
		});
		assert.ok(found);  // a correspondent code lens should exist
	});
};

/**
 * Test that a code lens will not be wrongly populated for a negative case.
 * @param docUri the uri of the target document
 * @param negativeCases the list of negative cases
 */
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