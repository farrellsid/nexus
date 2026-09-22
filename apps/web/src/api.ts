import type { components } from "./generated/api";

export type Investigation = components["schemas"]["Investigation"];
export type Claim = components["schemas"]["Claim"];
export type Source = components["schemas"]["Source"];
export type Neighborhood = components["schemas"]["Neighborhood"];
export type ReviewHistory = components["schemas"]["ReviewHistory"];
export type ReviewAvailability = components["schemas"]["ReviewAvailability"];
export type ProposalRequest = components["schemas"]["ProposalRequest"];
export type DecisionRequest = components["schemas"]["DecisionRequest"];

export async function postJson<T>(path: string, body: unknown): Promise<T> {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Nexus-Review": "1" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const problem = await response.json().catch(() => null);
    const detail =
      typeof problem?.detail === "string"
        ? problem.detail
        : "Check the form values and reload history before retrying.";
    throw new Error(`${response.status}: ${detail}`);
  }
  return response.json() as Promise<T>;
}

export async function getJson<T>(
  path: string,
  signal: AbortSignal,
): Promise<T> {
  const response = await fetch(path, { signal });
  if (!response.ok)
    throw new Error(`The evidence service returned ${response.status}.`);
  return response.json() as Promise<T>;
}
