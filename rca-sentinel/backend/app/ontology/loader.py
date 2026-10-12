"""Ontology loader: parses OWL/Turtle with rdflib and writes classes,
properties, and axioms to Neo4j via parameterized Cypher.

Replaces n10s (not available on Aura). The .ttl source file is the single
source of truth; this loader translates it into graph structures.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rdflib import OWL, RDF, RDFS, Graph, Namespace, URIRef
from rdflib.namespace import SKOS

from app.core.logging import get_logger
from app.graph.client import Neo4jClient

logger = get_logger(__name__)

RCA = Namespace("http://rca-sentinel.io/ontology#")
ONTOLOGY_PATH = Path(__file__).parent / "manufacturing.ttl"


class OntologyLoader:
    """Loads the RCA-Sentinel ontology from Turtle into Neo4j Aura."""

    def __init__(self, neo4j_client: Neo4jClient) -> None:
        self._neo4j = neo4j_client
        self._graph = Graph()

    def parse(self, path: Path | None = None) -> None:
        """Parse the Turtle ontology file."""
        ontology_path = path or ONTOLOGY_PATH
        self._graph.parse(str(ontology_path), format="turtle")
        logger.info("ontology_parsed", path=str(ontology_path), triples=len(self._graph))

    async def load(self) -> dict[str, int]:
        """Load the ontology into Neo4j. Returns counts of loaded elements."""
        self.parse()
        counts: dict[str, int] = {
            "classes": 0,
            "object_properties": 0,
            "datatype_properties": 0,
        }

        # Load classes
        classes = self._extract_classes()
        if classes:
            await self._load_classes(classes)
            counts["classes"] = len(classes)

        # Load object properties (relationships)
        obj_props = self._extract_object_properties()
        if obj_props:
            await self._load_object_properties(obj_props)
            counts["object_properties"] = len(obj_props)

        # Load datatype properties
        dt_props = self._extract_datatype_properties()
        if dt_props:
            await self._load_datatype_properties(dt_props)
            counts["datatype_properties"] = len(dt_props)

        logger.info("ontology_loaded", **counts)
        return counts

    def _extract_classes(self) -> list[dict[str, Any]]:
        """Extract all OWL classes from the ontology."""
        classes = []
        for s in self._graph.subjects(RDF.type, OWL.Class):
            if not isinstance(s, URIRef):
                continue
            name = self._local_name(s)
            label = self._get_literal(s, RDFS.label, name)
            comment = self._get_literal(s, RDFS.comment, "")
            alt_label = self._get_literal(s, SKOS.altLabel, "")
            parent = None
            for parent_uri in self._graph.objects(s, RDFS.subClassOf):
                if isinstance(parent_uri, URIRef):
                    parent = self._local_name(parent_uri)
            classes.append({
                "uri": str(s),
                "name": name,
                "label": label,
                "comment": comment,
                "alt_label": alt_label,
                "parent_class": parent,
            })
        return classes

    def _extract_object_properties(self) -> list[dict[str, Any]]:
        """Extract all OWL object properties."""
        props = []
        for s in self._graph.subjects(RDF.type, OWL.ObjectProperty):
            if not isinstance(s, URIRef):
                continue
            name = self._local_name(s)
            label = self._get_literal(s, RDFS.label, name)
            comment = self._get_literal(s, RDFS.comment, "")
            domain = None
            range_ = None
            for d in self._graph.objects(s, RDFS.domain):
                if isinstance(d, URIRef):
                    domain = self._local_name(d)
            for r in self._graph.objects(s, RDFS.range):
                if isinstance(r, URIRef):
                    range_ = self._local_name(r)
            props.append({
                "uri": str(s),
                "name": name,
                "label": label,
                "comment": comment,
                "domain": domain,
                "range": range_,
            })
        return props

    def _extract_datatype_properties(self) -> list[dict[str, Any]]:
        """Extract all OWL datatype properties."""
        props = []
        for s in self._graph.subjects(RDF.type, OWL.DatatypeProperty):
            if not isinstance(s, URIRef):
                continue
            name = self._local_name(s)
            domain = None
            range_ = None
            for d in self._graph.objects(s, RDFS.domain):
                if isinstance(d, URIRef):
                    domain = self._local_name(d)
            for r in self._graph.objects(s, RDFS.range):
                if isinstance(r, URIRef):
                    range_ = str(r)
            props.append({
                "uri": str(s),
                "name": name,
                "domain": domain,
                "range": range_,
            })
        return props

    async def _load_classes(self, classes: list[dict[str, Any]]) -> None:
        """Write ontology classes as OntologyClass nodes."""
        query = """
        UNWIND $rows AS row
        MERGE (c:OntologyClass {uri: row.uri})
        SET c.name = row.name,
            c.label = row.label,
            c.comment = row.comment,
            c.alt_label = row.alt_label,
            c.parent_class = row.parent_class,
            c.updated_at = datetime()
        """
        await self._neo4j.execute_write(query, {"rows": classes})
        logger.info("ontology_classes_loaded", count=len(classes))

    async def _load_object_properties(self, props: list[dict[str, Any]]) -> None:
        """Write object properties as OntologyRelationship nodes."""
        query = """
        UNWIND $rows AS row
        MERGE (r:OntologyRelationship {uri: row.uri})
        SET r.name = row.name,
            r.label = row.label,
            r.comment = row.comment,
            r.domain = row.domain,
            r.range = row.range,
            r.updated_at = datetime()
        """
        await self._neo4j.execute_write(query, {"rows": props})
        logger.info("ontology_object_properties_loaded", count=len(props))

    async def _load_datatype_properties(self, props: list[dict[str, Any]]) -> None:
        """Write datatype properties as OntologyProperty nodes."""
        query = """
        UNWIND $rows AS row
        MERGE (p:OntologyProperty {uri: row.uri})
        SET p.name = row.name,
            p.domain = row.domain,
            p.range = row.range,
            p.updated_at = datetime()
        """
        await self._neo4j.execute_write(query, {"rows": props})
        logger.info("ontology_datatype_properties_loaded", count=len(props))

    @staticmethod
    def _local_name(uri: URIRef) -> str:
        """Extract the local name from a URI (after # or last /)."""
        s = str(uri)
        if "#" in s:
            return s.rsplit("#", 1)[1]
        return s.rsplit("/", 1)[-1]

    def _get_literal(self, subject: URIRef, predicate: URIRef, default: str = "") -> str:
        """Get a literal value for a subject-predicate, or default."""
        for obj in self._graph.objects(subject, predicate):
            return str(obj)
        return default
