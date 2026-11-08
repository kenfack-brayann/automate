// Communication avec l'API Flask via Fetch API.
export class ApiError extends Error {}

async function postJson(url, body) {
  let response;
  try {
    response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
  } catch {
    throw new ApiError('Impossible de joindre le serveur. Vérifiez votre connexion.');
  }
  let data = null;
  try { data = await response.json(); } catch { /* réponse non JSON */ }
  if (!response.ok || !data || data.success !== true) {
    throw new ApiError((data && data.error) || 'Une erreur interne est survenue. Veuillez réessayer.');
  }
  return data;
}

export const generateAutomaton = (alphabet, regex) => postJson('/api/automate', { alphabet, regex });
export const checkWord = (automateId, word) => postJson('/api/automate/check', { automate_id: automateId, word });
