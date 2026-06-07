"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Background,
  Controls,
  MarkerType,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";

import { useProgress } from "@/components/ui/ProgressSelect";
import { fetchGraph, type GraphData, type RelationType } from "@/lib/graph";
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

export function StoryGraph({ focus }: { focus?: string | null }) {
  const progress = useProgress();
  return (
    <GraphForProgress
      key={`${progress}:${focus ?? ""}`}
      progress={progress}
      focus={focus}
    />
  );
}

function GraphForProgress({
  progress,
  focus,
}: {
  progress: string;
  focus?: string | null;
}) {
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [faction, setFaction] = useState("");
  const [relation, setRelation] = useState<RelationType | "">("");
  const [detail, setDetail] = useState<DetailTarget | null>(null);

  useEffect(() => {
    let active = true;
    fetchGraph(progress, focus)
      .then((response) => {
        if (active) setGraph(response.data);
      })
      .catch((reason: unknown) => {
        if (active) {
          setError(reason instanceof Error ? reason.message : "图谱读取失败。");
        }
      });
    return () => {
      active = false;
    };
  }, [focus, progress]);

  const visible = useMemo(() => {
    if (!graph) return null;
    const nodes = faction
      ? graph.nodes.filter((node) => node.faction_name === faction)
      : graph.nodes;
    const nodeIds = new Set(nodes.map((node) => node.id));
    const edges = graph.edges.filter(
      (edge) =>
        nodeIds.has(edge.source) &&
        nodeIds.has(edge.target) &&
        (!relation || edge.relation_type === relation),
    );
    return { nodes, edges };
  }, [faction, graph, relation]);

  if (error) {
    return <GraphStatus role="alert">加载失败：{error}</GraphStatus>;
  }
  if (!graph || !visible) {
    return <GraphStatus>正在加载图谱数据…</GraphStatus>;
  }
  if (visible.nodes.length === 0) {
    return <GraphStatus>当前进度与筛选条件下没有可显示的角色。</GraphStatus>;
  }

  return (
    <>
      <div className="grid min-h-[68vh] place-items-center px-6 text-center text-[var(--fog)] md:hidden">
        移动端可使用人物卷宗与时间线；完整关系画布请在较宽屏幕查看。
      </div>
      <div className="hidden md:block">
        <div className="flex flex-wrap items-center justify-between gap-4 border-b border-[var(--line)] p-4">
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
              if (node) setDetail({ kind: "node", node });
            }}
          />
          <p className="text-[10px] text-[var(--fog)]">
            {visible.nodes.length} 角色 · {visible.edges.length} 关系
          </p>
        </div>
        <GraphCanvas
          key={`${faction}:${relation}`}
          graph={visible}
          focus={focus}
          onDetail={setDetail}
        />
        <DetailPanel detail={detail} onClose={() => setDetail(null)} />
      </div>
    </>
  );
}

function GraphCanvas({
  graph,
  focus,
  onDetail,
}: {
  graph: Pick<GraphData, "nodes" | "edges">;
  focus?: string | null;
  onDetail: (detail: DetailTarget | null) => void;
}) {
  const radius = Math.max(240, graph.nodes.length * 34);
  const initialNodes: CharacterFlowNode[] = graph.nodes.map((node, index) => {
    const angle = (index / graph.nodes.length) * Math.PI * 2 - Math.PI / 2;
    return {
      id: node.id,
      type: "character",
      position: {
        x: Math.cos(angle) * radius + radius,
        y: Math.sin(angle) * radius + radius,
      },
      selected: node.slug === focus,
      data: {
        label: node.label,
        factionName: node.faction_name,
        importance: node.importance,
      },
    };
  });
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
    },
  }));
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="relative h-[68vh]" aria-label="角色关系图谱">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={NODE_TYPES}
        edgeTypes={EDGE_TYPES}
        onNodeClick={(_, selected) => {
          setNodes((items) =>
            items.map((item) => ({ ...item, selected: item.id === selected.id })),
          );
          const node = graph.nodes.find((item) => item.id === selected.id);
          if (node) onDetail({ kind: "node", node });
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
        fitViewOptions={{ padding: 0.18 }}
        minZoom={0.2}
        maxZoom={2.5}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="rgba(232,223,198,0.08)" gap={32} />
        <Controls showInteractive={false} />
        <MiniMap
          nodeColor="#9d2e25"
          maskColor="rgba(19,21,18,0.72)"
          className="!bg-[var(--ink)]"
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
    <div
      role={role}
      className="grid min-h-[68vh] place-items-center p-8 text-center text-[var(--fog)]"
    >
      {children}
    </div>
  );
}
