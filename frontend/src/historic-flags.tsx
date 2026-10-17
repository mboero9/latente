import { useState } from "preact/hooks";

/**
 * Real flag images rather than OS-dependent emoji glyphs (which can become
 * AR/PT/EG text on some desktop systems). All codes are allowlisted here.
 * England, Scotland, Wales and Northern Ireland have specific flag images.
 */
export const HISTORIC_COUNTRIES: Record<string,string> = {
  "Argentina": "ar", "Uruguay": "uy", "Brasil": "br",
  "Portugal": "pt", "España": "es", "Italia": "it",
  "Egipto": "eg", "Alemania": "de", "Francia": "fr",
  "México": "mx", "Estados Unidos": "us", "Japón": "jp",
  "Camerún": "cm", "Ghana": "gh", "Nigeria": "ng",
  "Arabia Saudita": "sa", "Costa de Marfil": "ci",
  "Paraguay": "py", "Chile": "cl", "Perú": "pe",
  "Países Bajos": "nl", "Inglaterra": "gb-eng",
  "Escocia": "gb-sct", "Gales": "gb-wls",
  "Irlanda del Norte": "gb-nir", "Hungría": "hu",
  "Austria": "at", "Checoslovaquia": "cz",
  "Estados Unidos de América": "us", "Sudáfrica": "za",
};
export function HistoricFlag({ country, compact = false }: {
  country: string; compact?: boolean;
}) {
  const countries = country.split("/").map(x => x.trim());
  return <span class="historic-flags" title={country} aria-label={country}>
    {countries.map((name, i) => <FlagPart key={i} name={name} compact={compact}/>)}
  </span>;
}

function FlagPart({name,compact}: {name:string;compact:boolean}) {
  const [failed, setFailed] = useState(false);
  const code = HISTORIC_COUNTRIES[name];
  if (!code || failed)
    return <span class="historic-flag-fallback" aria-hidden="true">
      {code?.split("-")[0].toUpperCase() || name.slice(0,2).toUpperCase()}
    </span>;
  return <img class={compact?"historic-flag-img compact":"historic-flag-img"}
    loading="lazy" decoding="async" alt="" width={compact?22:28}
    height={compact?17:21}
    src={`https://flagcdn.com/${compact?"32x24":"40x30"}/${code}.png`}
    onError={() => setFailed(true)}/>;
}
