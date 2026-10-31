import pytest
from backend.app.domain.dag import ConceptDAGValidator, DAGValidationError
from backend.app.seed.c_curriculum_data import CONCEPTS, PREREQUISITES


def test_seed_curriculum_is_valid_dag():
    """Curated GATE C programming concepts must form a valid DAG with no cycles."""
    concept_ids = [c["id"] for c in CONCEPTS]
    edges = [(p[0], p[1]) for p in PREREQUISITES]
    
    order = ConceptDAGValidator.validate_and_sort(concept_ids, edges)
    
    assert len(order) == len(concept_ids)
    
    # Prerequisite ordering property: every prerequisite must appear BEFORE its dependent
    index_map = {cid: idx for idx, cid in enumerate(order)}
    for concept_id, prereq_id in edges:
        assert index_map[prereq_id] < index_map[concept_id], (
            f"Prerequisite {prereq_id} should appear before {concept_id}"
        )


def test_dag_cycle_detection():
    """Cycle detection should raise DAGValidationError."""
    concepts = ["A", "B", "C"]
    cyclic_edges = [
        ("B", "A"),  # A -> B
        ("C", "B"),  # B -> C
        ("A", "C"),  # C -> A (CYCLE!)
    ]
    
    with pytest.raises(DAGValidationError, match="Cycle detected"):
        ConceptDAGValidator.validate_and_sort(concepts, cyclic_edges)


def test_dag_self_loop_detection():
    """Self-referential edges should be immediately rejected."""
    concepts = ["A", "B"]
    edges = [("A", "A")]
    with pytest.raises(DAGValidationError, match="Self-referential"):
        ConceptDAGValidator.validate_and_sort(concepts, edges)


def test_dag_unknown_concept_reference():
    """Referencing concepts not in the concept list must raise."""
    concepts = ["A", "B"]
    edges = [("A", "UNKNOWN_NODE")]
    with pytest.raises(DAGValidationError, match="Edge references unknown prerequisite"):
        ConceptDAGValidator.validate_and_sort(concepts, edges)

