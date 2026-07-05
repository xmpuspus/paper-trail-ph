// Client-side on-demand loaders (no fs — safe to import from client components).
// Large files: the full search index and the full flood-control graph.
import type { GraphData, Entity } from "./types";

export async function fetchEntities(): Promise<Entity[]> {
  const res = await fetch("/data/entities.json");
  if (!res.ok) throw new Error("Could not load the entity index.");
  const data = await res.json();
  return data.entities as Entity[];
}

export async function fetchMainGraph(): Promise<GraphData> {
  const res = await fetch("/data/graph-main.json");
  if (!res.ok) throw new Error("Could not load the full flood-control graph.");
  return (await res.json()) as GraphData;
}
