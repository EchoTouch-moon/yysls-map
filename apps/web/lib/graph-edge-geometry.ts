export type EdgeGeometry = {
  path: string;
  labelX: number;
  labelY: number;
  arrowX: number;
  arrowY: number;
  arrowAngle: number;
};

type EdgeGeometryInput = {
  id: string;
  sourceX: number;
  sourceY: number;
  targetX: number;
  targetY: number;
  isCenterEdge: boolean;
};

function pointOnQuadratic(
  start: number,
  control: number,
  end: number,
  t: number,
) {
  const u = 1 - t;
  return u * u * start + 2 * u * t * control + t * t * end;
}

function stableLabelPosition(id: string) {
  let hash = 0;
  for (const character of id) {
    hash = Math.imul(31, hash) + character.charCodeAt(0);
  }
  return 0.35 + (Math.abs(hash) % 31) / 100;
}

export function getRelationshipEdgeGeometry({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  isCenterEdge,
}: EdgeGeometryInput): EdgeGeometry {
  const dx = targetX - sourceX;
  const dy = targetY - sourceY;
  const distance = Math.hypot(dx, dy);
  let controlX = (sourceX + targetX) / 2;
  let controlY = (sourceY + targetY) / 2;

  if (!isCenterEdge && distance > 10) {
    const normalX = -dy / distance;
    const normalY = dx / distance;
    const outwardDirection =
      normalX * controlX + normalY * controlY >= 0 ? 1 : -1;
    const bend = distance * 0.35 * outwardDirection;
    controlX += normalX * bend;
    controlY += normalY * bend;
  }

  const path = isCenterEdge
    ? `M ${sourceX} ${sourceY} L ${targetX} ${targetY}`
    : `M ${sourceX} ${sourceY} Q ${controlX} ${controlY} ${targetX} ${targetY}`;
  const labelT = stableLabelPosition(id);
  const arrowT = 0.75;
  const arrowU = 1 - arrowT;
  const derivativeX =
    2 * arrowU * (controlX - sourceX) +
    2 * arrowT * (targetX - controlX);
  const derivativeY =
    2 * arrowU * (controlY - sourceY) +
    2 * arrowT * (targetY - controlY);

  return {
    path,
    labelX: pointOnQuadratic(sourceX, controlX, targetX, labelT),
    labelY: pointOnQuadratic(sourceY, controlY, targetY, labelT),
    arrowX: pointOnQuadratic(sourceX, controlX, targetX, arrowT),
    arrowY: pointOnQuadratic(sourceY, controlY, targetY, arrowT),
    arrowAngle: Math.atan2(derivativeY, derivativeX) * (180 / Math.PI),
  };
}
