import os
import logging
from typing import List, Dict, Set
# Note: tree_sitter and tree_sitter_languages must be installed
# mocking imports for now if environment is not set up
try:
    from tree_sitter_languages import get_language, get_parser
    HAS_TREE_SITTER = True
except ImportError:
    HAS_TREE_SITTER = False

logger = logging.getLogger(__name__)

class KnowledgeGraph:
    """
    Builds a dependency graph of the codebase using Tree-Sitter.
    Enables 'Impact Analysis' to see what breaks when a file changes.
    """
    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir
        self.graph: Dict[str, Set[str]] = {} # file -> {imported_by...}
        self.reverse_graph: Dict[str, Set[str]] = {} # file -> {imports...}

    def build_graph(self):
        """Scans the codebase and builds the graph."""
        if not HAS_TREE_SITTER:
            logger.warning("Tree-Sitter not installed. Knowledge Graph disabled.")
            return

        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    self._parse_file(full_path)

    def _parse_file(self, file_path: str):
        # TODO: Implement actual Tree-Sitter parsing logic here
        # For now, we'll use a naive regex fallback if TS fails or for simplicity in this stub
        pass

    def get_impacted_files(self, changed_file: str) -> List[str]:
        """Returns a list of files that depend on the changed file."""
        # Simple BFS
        impacted = set()
        queue = [changed_file]
        
        while queue:
            current = queue.pop(0)
            if current in self.graph:
                for dependent in self.graph[current]:
                    if dependent not in impacted:
                        impacted.add(dependent)
                        queue.append(dependent)
        
        return list(impacted)

knowledge_graph = KnowledgeGraph()
