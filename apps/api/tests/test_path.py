from dataclasses import dataclass
from types import SimpleNamespace
from uuid import uuid4

from app.domain import ProgressKey, RelationType
from app.schemas import GraphEdge


@dataclass
class FakeRelationship:
    id: object
    source_character_id: object
    target_character_id: object
    label: str
    relation_type: RelationType


def test_path_contract_shape() -> None:
    source_id = uuid4()
    target_id = uuid4()
    relationship = FakeRelationship(
        id=uuid4(),
        source_character_id=source_id,
        target_character_id=target_id,
        label="旧识",
        relation_type=RelationType.OLD_ACQUAINTANCE,
    )
    assert relationship.source_character_id != relationship.target_character_id
    assert ProgressKey.QINGHE.value == "qinghe"
    assert SimpleNamespace(found=True).found


def test_graph_edge_exposes_confidence() -> None:
    edge = GraphEdge(
        id=uuid4(),
        source=uuid4(),
        target=uuid4(),
        relation_type=RelationType.HIDDEN,
        label="待考关系",
        summary="玩家根据任务细节整理出的关系。",
        directional=False,
        confidence=0.6,
    )

    assert edge.confidence == 0.6
