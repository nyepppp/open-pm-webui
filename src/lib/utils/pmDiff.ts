/**
 * PM Diff — text diff algorithm for PM version comparison.
 *
 * Implements the Myers diff algorithm (line-level) with HTML stripping,
 * producing side-by-side diff results suitable for rendering in a
 * comparison UI.
 *
 * References:
 *   Myers, E. "An O(ND) Difference Algorithm and Its Variations", 1986.
 *   https://www.codeproject.com/Articles/42279/Instant-Diff
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface DiffLine {
	type: 'added' | 'removed' | 'unchanged';
	content: string;
	oldLineNo?: number; // line number in old text (undefined for added lines)
	newLineNo?: number; // line number in new text (undefined for removed lines)
}

// ---------------------------------------------------------------------------
// HTML stripping
// ---------------------------------------------------------------------------

/**
 * Strip HTML tags from a string, decoding common HTML entities.
 * Handles nested tags, self-closing tags, comments, and CDATA sections.
 */
export function stripHtmlTags(html: string): string {
	return (
		html
			// Remove CDATA sections
			.replace(/<!\[CDATA\[[\s\S]*?]]>/gi, '')
			// Remove HTML comments
			.replace(/<!--[\s\S]*?-->/g, '')
			// Remove script/style elements and their content
			.replace(/<(script|style)[^>]*>[\s\S]*?<\/\1>/gi, '')
			// Replace <br> and <br/> with newlines
			.replace(/<br\s*\/?>/gi, '\n')
			// Replace block-level closing tags with newlines for readability
			.replace(/<\/(p|div|li|tr|td|th|h[1-6]|blockquote|pre|section|article|header|footer|nav|aside|main|figure|figcaption|details|summary)>/gi, '\n')
			// Remove all remaining HTML tags
			.replace(/<[^>]+>/g, '')
			// Decode common HTML entities
			.replace(/&amp;/g, '&')
			.replace(/&lt;/g, '<')
			.replace(/&gt;/g, '>')
			.replace(/&quot;/g, '"')
			.replace(/&#39;/g, "'")
			.replace(/&nbsp;/g, ' ')
			// Decode numeric entities
			.replace(/&#x([0-9a-fA-F]+);/g, (_, hex) => String.fromCodePoint(parseInt(hex, 16)))
			.replace(/&#(\d+);/g, (_, dec) => String.fromCodePoint(parseInt(dec, 10)))
			// Collapse multiple blank lines into a single blank line
			.replace(/\n{3,}/g, '\n\n')
			// Trim trailing whitespace but preserve leading newlines from <br> tags
			.replace(/^\n+/, (m) => m.slice(0, 1))
			.replace(/\n+$/, '')
	);
}

// ---------------------------------------------------------------------------
// Myers diff algorithm
// ---------------------------------------------------------------------------

/**
 * Internal representation of a step in the shortest edit script.
 * type = -1 means diagonal (no change), 0 means delete, 1 means insert.
 */
type EditStep = { type: -1 | 0 | 1; oldIdx: number; newIdx: number };

/**
 * Run the Myers diff algorithm on two arrays of lines.
 * Returns an array of EditStep objects describing the shortest edit script.
 */
function myersDiff(oldLines: string[], newLines: string[]): EditStep[] {
	const N = oldLines.length;
	const M = newLines.length;

	// Edge cases
	if (N === 0 && M === 0) return [];
	if (N === 0) {
		return newLines.map((_, i) => ({ type: 1 as const, oldIdx: -1, newIdx: i }));
	}
	if (M === 0) {
		return oldLines.map((_, i) => ({ type: 0 as const, oldIdx: i, newIdx: -1 }));
	}

	const MAX = N + M;

	// V[k] stores the furthest-reaching x coordinate on diagonal k.
	// We use a Map so indices can be negative (k ranges from -d to d).
	// Forward pass: finds the shortest edit distance D.
	const trace: Map<number, number>[] = [];
	const vf = new Map<number, number>();
	vf.set(1, 0);

	let reachedEnd = false;
	let d = 0;

	for (; d <= MAX; d++) {
		const vd = new Map<number, number>();
		trace.push(vd);

		for (let k = -d; k <= d; k += 2) {
			let x: number;

			// Decide whether to move down (insert) or right (delete)
			if (k === -d || (k !== d && (vf.get(k - 1) ?? 0) < (vf.get(k + 1) ?? 0))) {
				// Move down: insert from new
				x = vf.get(k + 1) ?? 0;
			} else {
				// Move right: delete from old
				x = (vf.get(k - 1) ?? 0) + 1;
			}

			let y = x - k;

			// Extend along diagonal (matching lines)
			while (x < N && y < M && oldLines[x] === newLines[y]) {
				x++;
				y++;
			}

			vd.set(k, x);

			// Check if we've reached the end
			if (x >= N && y >= M) {
				reachedEnd = true;
				break;
			}
		}

		// Update vf for next iteration
		vf.clear();
		for (const [k, x] of vd) {
			vf.set(k, x);
		}

		if (reachedEnd) break;
	}

	// Backtrack through the trace to find the actual edit path
	return backtrack(trace, d, N, M, oldLines, newLines);
}

/**
 * Backtrack through the forward trace to reconstruct the edit path.
 * Walks from the endpoint back to the start, then reverses.
 */
function backtrack(
	trace: Map<number, number>[],
	editDistance: number,
	N: number,
	M: number,
	oldLines: string[],
	newLines: string[]
): EditStep[] {
	const steps: EditStep[] = [];
	let x = N;
	let y = M;

	for (let d = editDistance; d > 0; d--) {
		const vd = trace[d];
		const vPrev = trace[d - 1];
		const k = x - y;

		let prevK: number;
		if (k === -d || (k !== d && (vPrev.get(k - 1) ?? 0) < (vPrev.get(k + 1) ?? 0))) {
			prevK = k + 1; // came from down (insert)
		} else {
			prevK = k - 1; // came from right (delete)
		}

		const prevX = vPrev.get(prevK) ?? 0;
		const prevY = prevX - prevK;

		// Diagonal steps (matching lines) from (prevX, prevY) to before the edit step
		let diagX = prevX;
		let diagY = prevY;

		// Skip diagonal at current d level (it was already counted in the forward pass)
		// First, walk back the diagonals that were part of this d-level's extension
		while (x > diagX && y > diagY) {
			x--;
			y--;
			steps.push({ type: -1, oldIdx: x, newIdx: y });
		}

		// The edit step itself
		if (prevK < k) {
			// Delete from old (move right)
			x = prevX;
			y = prevY;
			steps.push({ type: 0, oldIdx: x, newIdx: y });
		} else {
			// Insert from new (move down)
			x = prevX;
			y = prevY;
			steps.push({ type: 1, oldIdx: x, newIdx: y });
		}
	}

	// Handle remaining diagonal steps at d = 0
	while (x > 0 && y > 0) {
		x--;
		y--;
		steps.push({ type: -1, oldIdx: x, newIdx: y });
	}

	// Steps were collected in reverse order
	steps.reverse();
	return steps;
}

/**
 * Convert edit steps into DiffLine objects with proper line numbering.
 */
function stepsToDiffLines(steps: EditStep[], oldLines: string[], newLines: string[]): DiffLine[] {
	const result: DiffLine[] = [];
	let oldLineNo = 0;
	let newLineNo = 0;

	// Group consecutive deletes and inserts that share the same position
	// to produce proper side-by-side diff (removed before added)
	const processed = new Array(steps.length).fill(false);

	for (let idx = 0; idx < steps.length; idx++) {
		if (processed[idx]) continue;

		const step = steps[idx];

		if (step.type === -1) {
			// Unchanged line
			result.push({
				type: 'unchanged',
				content: oldLines[step.oldIdx],
				oldLineNo: oldLineNo + 1,
				newLineNo: newLineNo + 1
			});
			oldLineNo++;
			newLineNo++;
		} else if (step.type === 0) {
			// Collect consecutive deletes
			const deletes: EditStep[] = [];
			let j = idx;
			while (j < steps.length && steps[j].type === 0) {
				deletes.push(steps[j]);
				processed[j] = true;
				j++;
			}
			// Collect consecutive inserts that follow
			const inserts: EditStep[] = [];
			while (j < steps.length && steps[j].type === 1) {
				inserts.push(steps[j]);
				processed[j] = true;
				j++;
			}

			// Emit all deletes
			for (const del of deletes) {
				result.push({
					type: 'removed',
					content: oldLines[del.oldIdx],
					oldLineNo: oldLineNo + 1
				});
				oldLineNo++;
			}
			// Emit all inserts
			for (const ins of inserts) {
				result.push({
					type: 'added',
					content: newLines[ins.newIdx],
					newLineNo: newLineNo + 1
				});
				newLineNo++;
			}
		} else if (step.type === 1) {
			// Collect consecutive inserts
			const inserts: EditStep[] = [];
			let j = idx;
			while (j < steps.length && steps[j].type === 1) {
				inserts.push(steps[j]);
				processed[j] = true;
				j++;
			}

			for (const ins of inserts) {
				result.push({
					type: 'added',
					content: newLines[ins.newIdx],
					newLineNo: newLineNo + 1
				});
				newLineNo++;
			}
		}
	}

	return result;
}

/**
 * Compute a line-level diff between two plain-text strings.
 * Does NOT strip HTML — pass plain text or call computeDiff() instead.
 */
export function diffText(oldText: string, newText: string): DiffLine[] {
	const oldLines = oldText === '' ? [] : oldText.split('\n');
	const newLines = newText === '' ? [] : newText.split('\n');
	const steps = myersDiff(oldLines, newLines);
	return stepsToDiffLines(steps, oldLines, newLines);
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Compute a diff between two HTML strings, suitable for the PM version
 * comparison feature.
 *
 * 1. Strips HTML tags from both inputs
 * 2. Splits into lines
 * 3. Runs Myers diff
 * 4. Returns DiffLine[] with proper line numbering
 */
export function computeDiff(oldHtml: string, newHtml: string): DiffLine[] {
	const oldText = stripHtmlTags(oldHtml);
	const newText = stripHtmlTags(newHtml);
	return diffText(oldText, newText);
}

// ---------------------------------------------------------------------------
// Display formatting
// ---------------------------------------------------------------------------

/** Escape a string for safe inclusion inside an HTML text node or attribute. */
function escapeHtml(str: string): string {
	return str
		.replace(/&/g, '&amp;')
		.replace(/</g, '&lt;')
		.replace(/>/g, '&gt;')
		.replace(/"/g, '&quot;')
		.replace(/'/g, '&#39;');
}

/**
 * Format diff results as HTML strings for side-by-side display panels.
 *
 * Returns `{ left: string, right: string }` where:
 * - `left`  shows the old text (removed lines highlighted, added lines as empty gutter rows)
 * - `right` shows the new text (added lines highlighted, removed lines as empty gutter rows)
 *
 * Each line is wrapped in a `<div>` with CSS classes for styling:
 * - `diff-line`           — base class for all lines
 * - `diff-line-unchanged` — unchanged line
 * - `diff-line-removed`   — removed line (red tint)
 * - `diff-line-added`     — added line (green tint)
 * - `diff-line-empty`     — placeholder row for alignment
 * - `diff-gutter`         — line number / marker cell
 * - `diff-content`        — text content cell
 */
export function formatDiffForDisplay(diffLines: DiffLine[]): { left: string; right: string } {
	const leftLines: string[] = [];
	const rightLines: string[] = [];

	for (const line of diffLines) {
		switch (line.type) {
			case 'unchanged':
				leftLines.push(
					`<div class="diff-line diff-line-unchanged">` +
						`<span class="diff-gutter">${line.oldLineNo ?? ''}</span>` +
						`<span class="diff-content">${escapeHtml(line.content)}</span>` +
						`</div>`
				);
				rightLines.push(
					`<div class="diff-line diff-line-unchanged">` +
						`<span class="diff-gutter">${line.newLineNo ?? ''}</span>` +
						`<span class="diff-content">${escapeHtml(line.content)}</span>` +
						`</div>`
				);
				break;

			case 'removed':
				leftLines.push(
					`<div class="diff-line diff-line-removed">` +
						`<span class="diff-gutter">-</span>` +
						`<span class="diff-content">${escapeHtml(line.content)}</span>` +
						`</div>`
				);
				// Empty row on the right to keep alignment
				rightLines.push(
					`<div class="diff-line diff-line-empty">` +
						`<span class="diff-gutter"></span>` +
						`<span class="diff-content"></span>` +
						`</div>`
				);
				break;

			case 'added':
				// Empty row on the left to keep alignment
				leftLines.push(
					`<div class="diff-line diff-line-empty">` +
						`<span class="diff-gutter"></span>` +
						`<span class="diff-content"></span>` +
						`</div>`
				);
				rightLines.push(
					`<div class="diff-line diff-line-added">` +
						`<span class="diff-gutter">+</span>` +
						`<span class="diff-content">${escapeHtml(line.content)}</span>` +
						`</div>`
				);
				break;
		}
	}

	return { left: leftLines.join('\n'), right: rightLines.join('\n') };
}
