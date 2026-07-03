import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface SyncToCalendarResponse {
	status: boolean;
	action: 'created' | 'updated';
	event_id: string;
}

export const syncEntryToCalendar = async (
	token: string,
	entryId: string,
	calendarId: string
): Promise<SyncToCalendarResponse> => {
	let error = null;

	const res = await fetch(`${WEBUI_API_BASE_URL}/pm/entries/${entryId}/sync-to-calendar`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ calendar_id: calendarId })
	})
		.then(async (res) => {
			if (!res.ok) throw await res.json();
			return res.json();
		})
		.catch((err) => {
			error = err.detail;
			console.error(err);
			return null;
		});

	if (error) {
		throw error;
	}

	return res;
};
