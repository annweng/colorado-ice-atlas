import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatNumber(value: number | null | undefined, digits = 1) {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  return value.toLocaleString("en-US", { maximumFractionDigits: digits, minimumFractionDigits: digits });
}

export function acres(km2: number | null | undefined) {
  if (valueMissing(km2)) return "—";
  return `${formatNumber((km2 as number) * 247.105, 1)} acres`;
}

export function metersToFeet(m: number | null | undefined) {
  if (valueMissing(m)) return "—";
  return `${formatNumber((m as number) * 3.28084, 0)} ft`;
}

export function valueMissing(value: unknown): value is null | undefined {
  return value === null || value === undefined || value === "";
}

export function cToF(c: number | null | undefined) {
  if (valueMissing(c)) return "—";
  return `${formatNumber((c as number) * 9 / 5 + 32, 0)}°F`;
}
