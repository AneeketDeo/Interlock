"""SHACL validator using pyshacl.

Validates data graphs against the SHACL shapes BEFORE any graph write.
Rejects are sent to the quarantine table with detailed reasons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pyshacl import validate as shacl_validate
from rdflib import RDF, Graph, Literal, Namespace, URIRef
from rdflib.namespace import XSD

from app.core.logging import get_logger

logger = get_logger(__name__)

RCA = Namespace("http://rca-sentinel.io/ontology#")
SHAPES_PATH = Path(__file__).parent / "shapes.ttl"


@dataclass
class ValidationResult:
    """Result of a SHACL validation run."""

    conforms: bool
    violations: list[dict[str, str]] = field(default_factory=list)
    records_validated: int = 0
    records_passed: int = 0
    records_failed: int = 0


class ShaclValidator:
    """Validates data against SHACL shapes before graph writes."""

    def __init__(self, shapes_path: Path | None = None) -> None:
        self._shapes_graph = Graph()
        self._shapes_graph.parse(str(shapes_path or SHAPES_PATH), format="turtle")
        logger.info("shacl_shapes_loaded", path=str(shapes_path or SHAPES_PATH))

    def validate_records(
        self,
        records: list[dict[str, Any]],
        record_type: str,
    ) -> ValidationResult:
        """Validate a batch of records against SHACL shapes.

        Args:
            records: List of dictionaries with entity data.
            record_type: The ontology class name (e.g., 'MaterialLot', 'Machine').

        Returns:
            ValidationResult with conformance status and violations.
        """
        result = ValidationResult(conforms=True, records_validated=len(records))
        passed = []
        failed = []

        for i, record in enumerate(records):
            data_graph = self._record_to_rdf(record, record_type, i)
            conforms, _, results_text = shacl_validate(
                data_graph,
                shacl_graph=self._shapes_graph,
                inference="none",
                abort_on_first=False,
            )

            if conforms:
                passed.append(record)
            else:
                failed.append(record)
                result.violations.append({
                    "record_index": str(i),
                    "record_id": record.get("id", f"index-{i}"),
                    "record_type": record_type,
                    "reason": results_text[:500] if results_text else "SHACL validation failed",
                })

        result.conforms = len(failed) == 0
        result.records_passed = len(passed)
        result.records_failed = len(failed)

        if failed:
            logger.warning(
                "shacl_validation_failures",
                record_type=record_type,
                passed=len(passed),
                failed=len(failed),
                total=len(records),
            )
        else:
            logger.debug(
                "shacl_validation_passed",
                record_type=record_type,
                count=len(records),
            )

        return result

    def _record_to_rdf(
        self,
        record: dict[str, Any],
        record_type: str,
        index: int,
    ) -> Graph:
        """Convert a record dict to an RDF graph for validation."""
        g = Graph()
        g.bind("rca", RCA)

        record_id = record.get("id", f"record-{index}")
        subject = URIRef(f"http://rca-sentinel.io/data/{record_type}/{record_id}")

        # Set the class type
        class_uri = RCA[record_type]
        g.add((subject, RDF.type, class_uri))

        # Map record fields to RDF properties
        type_map = {
            str: XSD.string,
            int: XSD.integer,
            float: XSD.float,
            bool: XSD.boolean,
        }

        for key, value in record.items():
            if key == "id" or value is None:
                continue

            prop_uri = RCA[key]
            python_type = type(value)

            if python_type in type_map:
                datatype = type_map[python_type]
                g.add((subject, prop_uri, Literal(value, datatype=datatype)))

        return g

    def validate_single(
        self,
        record: dict[str, Any],
        record_type: str,
    ) -> tuple[bool, str]:
        """Validate a single record. Returns (conforms, reason)."""
        result = self.validate_records([record], record_type)
        if result.conforms:
            return True, ""
        reason = result.violations[0]["reason"] if result.violations else "Unknown"
        return False, reason


# Module-level cached validator instance
_validator: ShaclValidator | None = None


def get_shacl_validator() -> ShaclValidator:
    """Get or create the SHACL validator singleton."""
    global _validator
    if _validator is None:
        _validator = ShaclValidator()
    return _validator
