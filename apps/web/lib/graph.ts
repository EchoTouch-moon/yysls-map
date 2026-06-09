import { apiFetch } from "@/lib/http";

export type RelationType =
  | "mentor"
  | "family"
  | "enemy"
  | "ally"
  | "old_acquaintance"
  | "exploitation"
  | "hierarchy"
  | "same_sect"
  | "interest"
  | "hidden";

export type GraphNode = {
  id: string;
  slug: string;
  label: string;
  faction_id: string | null;
  faction_name: string | null;
  importance: number;
  summary: string;
};

export type GraphEdge = {
  id: string;
  source: string;
  target: string;
  relation_type: RelationType;
  label: string;
  summary: string;
  directional: boolean;
  confidence: number;
};

export type GraphData = {
  nodes: GraphNode[];
  edges: GraphEdge[];
  progress: string;
};

export async function fetchGraph(progress: string, focus?: string | null) {
  const params = new URLSearchParams({ progress });
  if (focus) params.set("focus", focus);
  return apiFetch<GraphData>(`/graph?${params}`);
}
