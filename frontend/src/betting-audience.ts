/** Session-scoped, voluntary audience preference.
 * This is NOT identity verification nor proof of regulatory eligibility.
 * No IP, cookies or gambling profile is sent to an external provider.
 */
const KEY = "latente:betting-audience-v1";
export type BettingAudience = { adult: true; country: "AR"; province: "CABA" | "PBA" };

export function readBettingAudience(): BettingAudience | null {
  try {
    const raw = sessionStorage.getItem(KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as Partial<BettingAudience>;
    if (value.adult === true && value.country === "AR" &&
        (value.province === "CABA" || value.province === "PBA"))
      return value as BettingAudience;
  } catch { /* browsing without storage support */ }
  return null;
}
export function saveBettingAudience(value: BettingAudience | null) {
  try {
    if (value) sessionStorage.setItem(KEY, JSON.stringify(value));
    else sessionStorage.removeItem(KEY);
  } catch { /* storage is optional */ }
  window.dispatchEvent(new Event("latente:betting-audience"));
}
