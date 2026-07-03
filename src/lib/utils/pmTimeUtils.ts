/**
 * PM time utilities — shared across all PM route pages.
 * Handles timestamp normalization from various backend formats
 * (seconds, milliseconds, microseconds) and guards against
 * invalid/falsy values that cause "Invalid Date" display.
 */

/**
 * Normalize a timestamp to milliseconds.
 * Returns null for invalid/falsy inputs instead of producing NaN.
 *
 * Backend may return:
 * - seconds (e.g. 1704067200)
 * - milliseconds (e.g. 1704067200000)
 * - microseconds (e.g. 1704067200000000)
 * - 0 / null / undefined / NaN → invalid
 */
export function normalizeTs(ts: unknown): number | null {
	if (ts == null || typeof ts !== 'number' || !isFinite(ts) || ts === 0) {
		return null;
	}
	if (ts > 1e15) return ts / 1e6; // microsecond → ms
	if (ts > 1e12) return ts;        // already ms
	return ts * 1e3;                  // second → ms
}

/**
 * Format a timestamp as a date string (YYYY-MM-DD).
 * Returns empty string for invalid timestamps.
 */
export function formatDate(ts: unknown): string {
	const ms = normalizeTs(ts);
	if (ms == null) return '';
	const d = new Date(ms);
	return d.toISOString().slice(0, 10);
}

/**
 * Format a timestamp as a datetime string (YYYY-MM-DD HH:mm).
 * Returns empty string for invalid timestamps.
 */
export function formatDateTime(ts: unknown): string {
	const ms = normalizeTs(ts);
	if (ms == null) return '';
	const d = new Date(ms);
	const pad = (n: number) => String(n).padStart(2, '0');
	return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
