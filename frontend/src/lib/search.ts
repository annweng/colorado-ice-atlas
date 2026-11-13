const STOP = new Set(["lake", "lakes", "reservoir", "pond", "ponds", "the", "of", "near", "county"]);

export function significantTokens(query: string): string[] {
  return query
    .toLowerCase()
    .split(/[^a-z0-9]+/)
    .filter((token) => token.length > 1 && !STOP.has(token));
}

export function haystack(row: {
  name: string;
  official_name: string | null;
  county: string | null;
  alternative_names?: string[] | null;
}): string {
  return [row.name, row.official_name ?? "", row.county ?? "", ...(row.alternative_names ?? [])].join(" ").toLowerCase();
}

export function nameScore(query: string, row: { name: string; official_name: string | null; alternative_names?: string[] | null; area_km2: number }): number {
  const needle = query.trim().toLowerCase();
  const name = (row.official_name || row.name || "").toLowerCase();
  const alts = (row.alternative_names ?? []).map((value) => value.toLowerCase());
  const tokens = new Set(`${name} ${alts.join(" ")}`.replace(/[/-]/g, " ").split(/\s+/));
  const significant = significantTokens(needle);
  let value = 0;
  if (name === needle || alts.includes(needle)) value = 100;
  else if (significant.length && significant.every((token) => name.includes(token) || alts.some((alt) => alt.includes(token)))) value = 92;
  else if (tokens.has(needle)) value = 88;
  else if (name.startsWith(needle) || alts.some((alt) => alt.startsWith(needle))) value = 70;
  else if (name.includes(needle) || alts.some((alt) => alt.includes(needle))) value = 55;
  else value = 0;
  if (!value) return 0;
  return value + Math.min(25, row.area_km2 * 2);
}
