/** Vite `BASE_URL` is `/` locally and `/colorado-ice-atlas/` on GitHub Pages. */
export function assetUrl(path: string): string {
  const base = import.meta.env.BASE_URL.endsWith("/")
    ? import.meta.env.BASE_URL
    : `${import.meta.env.BASE_URL}/`;
  return `${base}${path.replace(/^\//, "")}`;
}

export function routerBasename(): string | undefined {
  const trimmed = import.meta.env.BASE_URL.replace(/\/$/, "");
  return trimmed && trimmed !== "/" ? trimmed : undefined;
}
