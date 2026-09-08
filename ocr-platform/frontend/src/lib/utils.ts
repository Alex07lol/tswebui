import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatBytes(bytes: number, decimals = 2) {
  if (bytes === 0) return "0 Bytes";
  const k = 1024;
  const dm = decimals < 0 ? 0 : decimals;
  const sizes = ["Bytes", "KB", "MB", "GB"];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + " " + sizes[i];
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return "0%";
  return `${Math.round(value * 100)}%`;
}

export function getConfidenceColor(confidence: number | null | undefined): string {
  if (confidence === null || confidence === undefined) return "text-zinc-400";
  if (confidence >= 0.85) return "text-emerald-400";
  if (confidence >= 0.60) return "text-amber-400";
  return "text-rose-400";
}

export function getConfidenceBadge(confidence: number | null | undefined): string {
  if (confidence === null || confidence === undefined) return "bg-zinc-900 border-zinc-800 text-zinc-400";
  if (confidence >= 0.85) return "bg-emerald-950/40 border-emerald-800 text-emerald-300";
  if (confidence >= 0.60) return "bg-amber-950/40 border-amber-800 text-amber-300";
  return "bg-rose-950/40 border-rose-800 text-rose-300";
}
