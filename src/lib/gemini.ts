const configuredBackendUrl = import.meta.env.VITE_BACKEND_URL?.trim();
const fallbackBackendUrl = typeof window !== 'undefined' ? window.location.origin : 'http://localhost:3000';

export const BASE_URL = configuredBackendUrl || fallbackBackendUrl;

export async function askAI(endpoint: string, body: Record<string, unknown>) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Backend API request failed: ${response.status} ${response.statusText}: ${errorText}`);
  }

  return response.json();
}
