from typing import Dict, List, Set


class DAGValidationError(Exception):
    pass


class ConceptDAGValidator:
    """
    Validates that the concept curriculum forms a strict Directed Acyclic Graph (DAG)
    and provides topological traversal capabilities.
    """

    @staticmethod
    def validate_and_sort(concepts: List[str], edges: List[tuple[str, str]]) -> List[str]:
        """
        Validates the graph and returns a topological sort.
        edges: list of (concept_id, prerequisite_id) where prerequisite must precede concept.
        In graph terms: prerequisite -> concept.
        """
        concept_set = set(concepts)
        adj: Dict[str, List[str]] = {c: [] for c in concepts}
        in_degree: Dict[str, int] = {c: 0 for c in concepts}

        for concept_id, prereq_id in edges:
            if concept_id not in concept_set:
                raise DAGValidationError(f"Edge references unknown concept: {concept_id}")
            if prereq_id not in concept_set:
                raise DAGValidationError(f"Edge references unknown prerequisite: {prereq_id}")
            if concept_id == prereq_id:
                raise DAGValidationError(f"Self-referential prerequisite detected on {concept_id}")

            # Prerequisite must be mastered before Concept (prereq -> concept)
            adj[prereq_id].append(concept_id)
            in_degree[concept_id] += 1

        # Kahn's algorithm for topological sorting and cycle detection
        queue = [c for c in concepts if in_degree[c] == 0]
        sorted_order = []

        while queue:
            curr = queue.pop(0)
            sorted_order.append(curr)

            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_order) != len(concepts):
            cycle_nodes = [c for c in concepts if in_degree[c] > 0]
            raise DAGValidationError(f"Cycle detected in curriculum DAG involving: {cycle_nodes}")

        return sorted_order

    @staticmethod
    def get_prerequisites_map(edges: List[tuple[str, str]]) -> Dict[str, Set[str]]:
        """
        Returns a mapping of concept_id -> set of direct prerequisite_ids.
        """
        prereq_map: Dict[str, Set[str]] = {}
        for concept_id, prereq_id in edges:
            prereq_map.setdefault(concept_id, set()).add(prereq_id)
        return prereq_map

