import * as vscode from 'vscode';
import * as assert from 'assert';
import { activate, EX_STATS_PAIRS } from './helper';

suite('Should show Hover', () => {
	EX_STATS_PAIRS.forEach(([exUri, statsObj]) => {
		if (statsObj.code_lenses) {
			test(`Check against all target hovers for ${exUri}`, async () => {
				await activate(exUri);
				await testHovers(exUri, statsObj.code_lenses);
			});
		};
		
		if (statsObj.negative_cases) {
			test(`Check against all negative cases for ${exUri}`, async () => {
				await activate(exUri);
				await testHovers(exUri, statsObj.negative_cases);
			});
		}
	});
});

/**
 * Test if the correctness of the hover feature against a specific document and
 * a list of expected results.
 * The expected results are expressed as code lenses because the hovers use the
 * same information as the code lenses.
 * A code lens with no `mro` field means expecting a negative answer.
 * @param docUri the uri of the target document to test
 * @param expectedCodeLenses the list of expected code lenses (used by hover)
 */
async function testHovers(
	docUri: vscode.Uri,
	expectedCodeLenses: { location: number[], mro?: string[] }[],
) {
	// check over all possible locations (the code lens locations)
	for (const lens of expectedCodeLenses) {
		// fetch the hover results of the target location
		const hoverResults = (await vscode.commands.executeCommand(
			'vscode.executeHoverProvider',
			docUri,
			new vscode.Position(lens.location[0], lens.location[1]),
		)) as vscode.Hover[];
		if (lens.mro) {
			// case of expecting a MRO hover result
			assert.ok(hoverResults.length > 0);
			// check one of the hover results is the MRO hover result
			let foundHover = false;
			hoverResults.forEach(hover => {
				if (hover.contents.length === lens.mro.length) {
					// check if there is element-wise equality
					let match = true;
					hover.contents.map((content, i) => {
						match = match && (
							lens.mro[i] === (
								typeof content === 'string' ? content : content.value
							)
						);
					});
					if (match) { foundHover = true; }
				}
			});
			assert.ok(foundHover);
		} else {
			// case of not expecting a hover result
			assert.strictEqual(hoverResults.length, 0);
		}
	}
}