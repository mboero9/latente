/** Recognizable website favicons from the operators' published domains.
 * These are website icons, NOT licensed logo artwork or verification of a
 * gambling licence. No outbound operator links are created here.
 */
type Brand = { label: string; domain: string; pattern: RegExp };
const BRANDS: Brand[] = [
  {label:"Betano",domain:"www.betano.bet.ar",pattern:/^betano\b/i},
  {label:"bplay",domain:"caba.bplay.bet.ar",pattern:/^bplay\b/i},
  {label:"bet365",domain:"www.bet365.com",pattern:/^bet\s*365\b/i},
  {label:"Betsson",domain:"www.betsson.com",pattern:/^betsson\b/i},
  {label:"Betfair",domain:"www.betfair.com",pattern:/^betfair\b/i},
  {label:"Codere",domain:"www.codere.es",pattern:/^codere\b/i},
  {label:"Winamax",domain:"www.winamax.fr",pattern:/^winamax\b/i},
  {label:"Betclic",domain:"www.betclic.fr",pattern:/^betclic\b/i},
  {label:"PMU",domain:"www.pmu.fr",pattern:/^pmu\b/i},
  {label:"Sportium",domain:"www.sportium.es",pattern:/^sportium\b/i},
  {label:"Unibet",domain:"www.unibet.fr",pattern:/^unibet\b/i},
  {label:"bwin",domain:"www.bwin.com",pattern:/^bwin\b/i},
  {label:"DraftKings",domain:"www.draftkings.com",pattern:/^draftkings\b/i},
  {label:"FanDuel",domain:"www.fanduel.com",pattern:/^fanduel\b/i},
];

export function bookmakerBrand(name: string) {
  return BRANDS.find(brand => brand.pattern.test(name.trim()));
}

export function BookmakerMark({ name }: { name: string }) {
  const brand = bookmakerBrand(name);
  const fallback = (brand?.label || name).slice(0, 2).toUpperCase();
  return <span class="bookmaker-brand">
    {brand ? <img
      loading="lazy" decoding="async" alt=""
      src={`https://www.google.com/s2/favicons?domain=${encodeURIComponent(brand.domain)}&sz=64`}
      onError={event => { event.currentTarget.hidden = true; }}
    /> : <span class="bookmaker-brand-initials" aria-hidden="true">{fallback}</span>}
    <strong>{brand?.label || name}</strong>
  </span>;
}
