"""Action proposal MCP tools for containment and remediation."""

from __future__ import annotations

import uuid
from typing import Any

from app.domain.enums import ActionType, ApprovalStatus
from app.graph.repositories.incident import IncidentRepository

_incident_repo = IncidentRepository()


async def propose_equipment_interlock(
    machine_id: str,
    reason: str,
    incident_id: str,
) -> dict[str, Any]:
    """Propose an emergency equipment interlock / soft stop on a machine.

    MANDATORY: Requires human engineer approval before actuator execution.

    Args:
        machine_id: Canonical machine ID to interlock (e.g. 'station-03b').
        reason: Justification for interlock (e.g. thermal runaway & miscalibration).
        incident_id: Active incident ID this action is attached to.

    Returns:
        Created RemediationAction dict with pending_approval status.
    """
    action_id = f"ACT-INT-{uuid.uuid4().hex[:6]}"
    action_payload = {
        "id": action_id,
        "action_type": ActionType.INTERLOCK.value,
        "target_entity": machine_id,
        "target_entity_type": "Machine",
        "description": f"Emergency soft stop / interlock on {machine_id}: {reason}",
        "status": ApprovalStatus.PENDING.value,
        "requires_human_approval": True,
    }
    return await _incident_repo.propose_action(incident_id, action_payload)


async def propose_erp_quarantine(
    lot_id: str,
    reason: str,
    incident_id: str,
) -> dict[str, Any]:
    """Propose an ERP warehouse quarantine for a contaminated material lot.

    MANDATORY: Requires human engineer approval before ERP status update.

    Args:
        lot_id: Canonical lot ID to quarantine (e.g. 'lot-40921').
        reason: Justification for quarantine (e.g. out-of-spec silicon content).
        incident_id: Active incident ID this action is attached to.

    Returns:
        Created RemediationAction dict with pending_approval status.
    """
    action_id = f"ACT-ERP-{uuid.uuid4().hex[:6]}"
    action_payload = {
        "id": action_id,
        "action_type": ActionType.ERP_REROUTE.value,
        "target_entity": lot_id,
        "target_entity_type": "MaterialLot",
        "description": f"Quarantine lot {lot_id} across ERP warehouses and re-route orders: {reason}",
        "status": ApprovalStatus.PENDING.value,
        "requires_human_approval": True,
    }
    return await _incident_repo.propose_action(incident_id, action_payload)


async def propose_cmms_work_order(
    machine_id: str,
    title: str,
    description: str,
    incident_id: str,
    priority: str = "emergency",
) -> dict[str, Any]:
    """Propose an urgent CMMS maintenance inspection and recalibration work order.

    MANDATORY: Requires human engineer approval before dispatching technician.

    Args:
        machine_id: Target machine requiring maintenance (e.g. 'station-03b').
        title: Work order title.
        description: Detailed instructions (e.g. laser runout recalibration).
        incident_id: Active incident ID.
        priority: Work order priority level ('emergency', 'urgent', 'routine').

    Returns:
        Created RemediationAction dict with pending_approval status.
    """
    action_id = f"ACT-CMMS-{uuid.uuid4().hex[:6]}"
    action_payload = {
        "id": action_id,
        "action_type": ActionType.CMMS_WORK_ORDER.value,
        "target_entity": machine_id,
        "target_entity_type": "Machine",
        "description": f"CMMS Work Order [{priority.upper()}]: {title} - {description}",
        "status": ApprovalStatus.PENDING.value,
        "requires_human_approval": True,
    }
    return await _incident_repo.propose_action(incident_id, action_payload)
