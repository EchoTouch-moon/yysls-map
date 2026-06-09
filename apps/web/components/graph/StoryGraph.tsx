"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Background,
  BackgroundVariant,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { fetchGraph, type GraphData, type RelationType } from "@/lib/graph";
import { getCenteredGraphPositions } from "@/lib/graph-layout";
import {
  CharacterNode,
  type CharacterFlowNode,
} from "@/components/graph/CharacterNode";
import {
  RelationshipEdge,
  type RelationshipFlowEdge,
} from "@/components/graph/RelationshipEdge";
import { DetailPanel, type DetailTarget } from "@/components/graph/DetailPanel";
import { GraphFilters } from "@/components/graph/GraphFilters";

const NODE_TYPES = { character: CharacterNode };
const EDGE_TYPES = { relationship: RelationshipEdge };
const DEFAULT_FOCUS = "protagonist";

export function StoryGraph({ focus }: { focus?: string | null }) {
  const progress = useProgress();
  const activeFocus = focus || DEFAULT_FOCUS;
  return (
    <GraphForProgress
      key={`${progress}:${activeFocus}`}
      progress={progress}
      focus={activeFocus}
    />
  );
}

function GraphForProgress({
  progress,
  focus,
}: {
  progress: string;
  focus: string;
}) {
  const router = useRouter();
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [faction, setFaction] = useState("");
  const [relation, setRelation] = useState<RelationType | "">("");
  const [detail, setDetail] = useState<DetailTarget | null>(null);
  const [turning, setTurning] = useState(true);

  useEffect(() => {
    let active = true;
    const reducedMotion = typeof window !== "undefined" && window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;

    fetchGraph(progress, focus)
      .then((response) => {
        if (active) {
          setGraph(response.data);
          setError("");
          if (reducedMotion) {
            setTurning(false);
          } else {
            setTimeout(() => {
              if (active) setTurning(false);
            }, 200);
          }
        }
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "图谱读取失败。");
          setTurning(false);
        }
      });
    return () => {
      active = false;
    };
  }, [focus, progress]);

  const visible = useMemo(() => {
    if (!graph) return null;
    const center = graph.nodes.find((node) => node.slug === focus);
    const nodes = faction
      ? graph.nodes.filter(
          (node) => node.id === center?.id || node.faction_name === faction,
        )
      : graph.nodes;
    const nodeIds = new Set(nodes.map((node) => node.id));
    const edges = graph.edges.filter(
      (edge) =>
        nodeIds.has(edge.source) &&
        nodeIds.has(edge.target) &&
        (!relation || edge.relation_type === relation),
    );
    return { nodes, edges };
  }, [faction, focus, graph, relation]);

  function changeFocus(slug: string) {
    if (slug === focus || turning) return;
    setDetail(null);
    setTurning(true);
    const reducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)",
    ).matches;
    window.setTimeout(
      () => router.push(`/graph?focus=${encodeURIComponent(slug)}`, { scroll: false }),
      reducedMotion ? 0 : 260,
    );
  }

  if (error) {
    return <GraphStatus role="alert">加载失败：{error}</GraphStatus>;
  }
  if (!graph || !visible) {
    return <GraphStatus>正在调阅人物关系卷…</GraphStatus>;
  }
  if (visible.nodes.length === 0) {
    return <GraphStatus>当前进度与筛选条件下没有可显示的角色。</GraphStatus>;
  }

  const center = graph.nodes.find((node) => node.slug === focus) ?? graph.nodes[0];

  return (
    <>
      <div className="graph-mobile-notice md:hidden">
        <span className="seal-mark" aria-hidden="true">卷</span>
        <p>移动端请使用人物卷宗与剧情时间线；完整人物关系卷需在较宽画布展开。</p>
      </div>
      <div className="hidden md:block">
        <div className="graph-toolbar">
          <div>
            <p className="archive-kicker">当前人物卷</p>
            <div className="mt-2 flex items-baseline gap-3">
              <h2 className="text-2xl tracking-[0.16em]">{center?.label}</h2>
              <span className="text-xs text-[var(--fog)]">
                {visible.edges.length} 条可见关系
              </span>
            </div>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-3">
            <GraphFilters
              nodes={graph.nodes}
              search={search}
              faction={faction}
              relation={relation}
              onSearch={setSearch}
              onFaction={(value) => {
                setDetail(null);
                setFaction(value);
              }}
              onRelation={(value) => {
                setDetail(null);
                setRelation(value);
              }}
              onSelect={(id) => {
                const node = graph.nodes.find((item) => item.id === id);
                if (node) changeFocus(node.slug);
              }}
            />
            {focus !== DEFAULT_FOCUS && (
              <button
                type="button"
                className="archive-button"
                onClick={() => changeFocus(DEFAULT_FOCUS)}
              >
                回到主角
              </button>
            )}
          </div>
        </div>
        <div className={`book-stage ${turning ? "book-stage-turning" : ""}`}>
          <GraphCanvas
            key={`${focus}:${faction}:${relation}`}
            graph={visible}
            focus={focus}
            onDetail={setDetail}
            onChangeFocus={changeFocus}
          />
        </div>
        <DetailPanel detail={detail} onClose={() => setDetail(null)} />
      </div>
    </>
  );
}

function GraphCanvas({
  graph,
  focus,
  onDetail,
  onChangeFocus,
}: {
  graph: Pick<GraphData, "nodes" | "edges">;
  focus: string;
  onDetail: (detail: DetailTarget | null) => void;
  onChangeFocus: (slug: string) => void;
}) {
  const positions = getCenteredGraphPositions(graph.nodes, graph.edges, focus);
  const center = graph.nodes.find((node) => node.slug === focus) ?? graph.nodes[0];
  const initialNodes: CharacterFlowNode[] = graph.nodes.map((node) => ({
    id: node.id,
    type: "character",
    position: positions.get(node.id) ?? { x: 0, y: 0 },
    selected: node.id === center?.id,
    data: {
      label: node.label,
      factionName: node.faction_name,
      importance: node.importance,
      isCenter: node.id === center?.id,
    },
  }));
  const initialEdges: RelationshipFlowEdge[] = graph.edges.map((edge) => ({
    id: edge.id,
    source: edge.source,
    target: edge.target,
    type: "relationship",
    markerEnd: edge.directional
      ? { type: MarkerType.ArrowClosed, color: "#a9a68e" }
      : undefined,
    data: {
      label: edge.label,
      relationType: edge.relation_type,
      confidence: edge.confidence,
    },
  }));
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="graph-canvas" aria-label="角色关系图谱">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        onNodeClick={(_, selected) => {
          const node = graph.nodes.find((item) => item.id === selected.id);
          if (!node) return;
          if (node.id === center?.id) {
            setNodes((items) =>
              items.map((item) => ({ ...item, selected: item.id === selected.id })),
            );
            onDetail({ kind: "node", node });
            return;
          }
          onChangeFocus(node.slug);
        }}
        onEdgeClick={(_, selected) => {
          setEdges((items) =>
            items.map((item) => ({ ...item, selected: item.id === selected.id })),
          );
          const edge = graph.edges.find((item) => item.id === selected.id);
          if (edge) onDetail({ kind: "edge", edge });
        }}
        onPaneClick={() => onDetail(null)}
        fitView
        fitViewOptions={{ padding: 0.2, maxZoom: 1.05 }}
        minZoom={0.22}
        maxZoom={2}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          color="rgba(88,72,49,0.3)"
          gap={34}
          size={1}
        />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor={(node) => node.data.isCenter ? "#9d2e25" : "#8d8267"}
          maskColor="rgba(23,20,15,0.76)"
          className="archive-minimap"
        />
      </ReactFlow>
    </div>
  );
}

function GraphStatus({
  children,
  role,
}: {
  children: React.ReactNode;
  role?: "alert";
}) {
  return (
    <div role={role} className="graph-status">
      <span className="seal-mark" aria-hidden="true">阅</span>
      <p>{children}</p>
    </div>
  );
}
