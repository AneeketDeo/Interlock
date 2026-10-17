CREATE OR REPLACE PROPERTY GRAPH FactoryGraph
  NODE TABLES (
    Site,
    Area,
    Line,
    Machine,
    Component,
    Sensor,
    Tag,
    ObservationWindow,
    Alarm,
    Anomaly,
    Product,
    RecipeStep,
    WorkOrder,
    Batch,
    Inspection,
    DefectCode,
    Employee,
    Crew,
    Shift,
    Handover,
    TrainingRecord,
    MaintenanceOrder,
    Calibration,
    PmPlan,
    SparePart,
    Supplier,
    Material,
    Bom,
    MaterialLot,
    MillCertificate,
    PurchaseOrder,
    FailureMode,
    ControlPlan,
    Incident,
    Evidence,
    Cause,
    CorrectiveAction,
    Decision,
    Approval,
    Action
  )
  EDGE TABLES (
    Processed
      SOURCE KEY (machine_id) REFERENCES Machine (machine_id)
      DESTINATION KEY (lot_id) REFERENCES MaterialLot (lot_id)
      LABEL PROCESSED,
    SuppliedBy
      SOURCE KEY (lot_id) REFERENCES MaterialLot (lot_id)
      DESTINATION KEY (supplier_id) REFERENCES Supplier (supplier_id)
      LABEL SUPPLIED_BY,
    Supplies
      SOURCE KEY (supplier_id) REFERENCES Supplier (supplier_id)
      DESTINATION KEY (buyer_supplier_id) REFERENCES Supplier (buyer_supplier_id)
      LABEL SUPPLIES,
    MaintenanceOn
      SOURCE KEY (order_id) REFERENCES MaintenanceOrder (order_id)
      DESTINATION KEY (machine_id) REFERENCES Machine (machine_id)
      LABEL MAINTENANCE_ON,
    PerformedBy
      SOURCE KEY (order_id) REFERENCES MaintenanceOrder (order_id)
      DESTINATION KEY (crew_id) REFERENCES Crew (crew_id)
      LABEL PERFORMED_BY,
    MemberOf
      SOURCE KEY (employee_id) REFERENCES Employee (employee_id)
      DESTINATION KEY (crew_id) REFERENCES Crew (crew_id)
      LABEL MEMBER_OF,
    Affects
      SOURCE KEY (incident_id) REFERENCES Incident (incident_id)
      DESTINATION KEY (machine_id) REFERENCES Machine (machine_id)
      LABEL AFFECTS,
    EvidencedBy
      SOURCE KEY (incident_id) REFERENCES Incident (incident_id)
      DESTINATION KEY (evidence_id) REFERENCES Evidence (evidence_id)
      LABEL EVIDENCED_BY,
    HasCause
      SOURCE KEY (incident_id) REFERENCES Incident (incident_id)
      DESTINATION KEY (cause_id) REFERENCES Cause (cause_id)
      LABEL HAS_CAUSE,
    CauseMapsTo
      SOURCE KEY (cause_id) REFERENCES Cause (cause_id)
      DESTINATION KEY (failure_mode_id) REFERENCES FailureMode (failure_mode_id)
      LABEL CAUSE_MAPS_TO,
    CorrectedBy
      SOURCE KEY (incident_id) REFERENCES Incident (incident_id)
      DESTINATION KEY (corrective_action_id) REFERENCES CorrectiveAction (corrective_action_id)
      LABEL CORRECTED_BY,
    HasDecision
      SOURCE KEY (incident_id) REFERENCES Incident (incident_id)
      DESTINATION KEY (decision_id) REFERENCES Decision (decision_id)
      LABEL HAS_DECISION,
    ApprovedBy
      SOURCE KEY (decision_id) REFERENCES Decision (decision_id)
      DESTINATION KEY (approval_id) REFERENCES Approval (approval_id)
      LABEL APPROVED_BY,
    ControlledBy
      SOURCE KEY (failure_mode_id) REFERENCES FailureMode (failure_mode_id)
      DESTINATION KEY (control_plan_id) REFERENCES ControlPlan (control_plan_id)
      LABEL CONTROLLED_BY,
    Area AS SiteHasArea
      KEY (area_id)
      SOURCE KEY (site_id) REFERENCES Site (site_id)
      DESTINATION KEY (area_id) REFERENCES Area (area_id)
      LABEL HAS_AREA NO PROPERTIES,
    Line AS AreaHasLine
      KEY (line_id)
      SOURCE KEY (area_id) REFERENCES Area (area_id)
      DESTINATION KEY (line_id) REFERENCES Line (line_id)
      LABEL HAS_LINE NO PROPERTIES,
    Machine AS LineHasMachine
      KEY (machine_id)
      SOURCE KEY (line_id) REFERENCES Line (line_id)
      DESTINATION KEY (machine_id) REFERENCES Machine (machine_id)
      LABEL HAS_MACHINE NO PROPERTIES,
    Component AS MachineHasComponent
      KEY (component_id)
      SOURCE KEY (machine_id) REFERENCES Machine (machine_id)
      DESTINATION KEY (component_id) REFERENCES Component (component_id)
      LABEL HAS_COMPONENT NO PROPERTIES,
    Sensor AS MachineHasSensor
      KEY (sensor_id)
      SOURCE KEY (machine_id) REFERENCES Machine (machine_id)
      DESTINATION KEY (sensor_id) REFERENCES Sensor (sensor_id)
      LABEL HAS_SENSOR NO PROPERTIES,
    Tag AS SensorHasTag
      KEY (tag_id)
      SOURCE KEY (sensor_id) REFERENCES Sensor (sensor_id)
      DESTINATION KEY (tag_id) REFERENCES Tag (tag_id)
      LABEL HAS_TAG NO PROPERTIES,
    ObservationWindow AS SensorHasObservation
      KEY (obs_id)
      SOURCE KEY (sensor_id) REFERENCES Sensor (sensor_id)
      DESTINATION KEY (obs_id) REFERENCES ObservationWindow (obs_id)
      LABEL HAS_OBSERVATION NO PROPERTIES,
    Alarm AS SensorHasAlarm
      KEY (alarm_id)
      SOURCE KEY (sensor_id) REFERENCES Sensor (sensor_id)
      DESTINATION KEY (alarm_id) REFERENCES Alarm (alarm_id)
      LABEL HAS_ALARM NO PROPERTIES,
    Anomaly AS SensorHasAnomaly
      KEY (anomaly_id)
      SOURCE KEY (sensor_id) REFERENCES Sensor (sensor_id)
      DESTINATION KEY (anomaly_id) REFERENCES Anomaly (anomaly_id)
      LABEL HAS_ANOMALY NO PROPERTIES,
    WorkOrder AS WorkOrderOnMachine
      KEY (work_order_id)
      SOURCE KEY (work_order_id) REFERENCES WorkOrder (work_order_id)
      DESTINATION KEY (machine_id) REFERENCES Machine (machine_id)
      LABEL RAN_ON NO PROPERTIES,
    WorkOrder AS WorkOrderLot
      KEY (work_order_id)
      SOURCE KEY (work_order_id) REFERENCES WorkOrder (work_order_id)
      DESTINATION KEY (lot_id) REFERENCES MaterialLot (lot_id)
      LABEL CONSUMED_LOT NO PROPERTIES,
    WorkOrder AS WorkOrderShift
      KEY (work_order_id)
      SOURCE KEY (work_order_id) REFERENCES WorkOrder (work_order_id)
      DESTINATION KEY (shift_id) REFERENCES Shift (shift_id)
      LABEL IN_SHIFT NO PROPERTIES,
    WorkOrder AS WorkOrderOperator
      KEY (work_order_id)
      SOURCE KEY (work_order_id) REFERENCES WorkOrder (work_order_id)
      DESTINATION KEY (operator_id) REFERENCES Employee (operator_id)
      LABEL OPERATED_BY NO PROPERTIES,
    Batch AS WorkOrderBatch
      KEY (batch_id)
      SOURCE KEY (work_order_id) REFERENCES WorkOrder (work_order_id)
      DESTINATION KEY (batch_id) REFERENCES Batch (batch_id)
      LABEL PRODUCED_BATCH NO PROPERTIES,
    Inspection AS WorkOrderInspection
      KEY (inspection_id)
      SOURCE KEY (work_order_id) REFERENCES WorkOrder (work_order_id)
      DESTINATION KEY (inspection_id) REFERENCES Inspection (inspection_id)
      LABEL HAS_INSPECTION NO PROPERTIES,
    Shift AS ShiftCrew
      KEY (shift_id)
      SOURCE KEY (shift_id) REFERENCES Shift (shift_id)
      DESTINATION KEY (crew_id) REFERENCES Crew (crew_id)
      LABEL SHIFT_CREW NO PROPERTIES,
    Handover AS HandoverToCrew
      KEY (handover_id)
      SOURCE KEY (handover_id) REFERENCES Handover (handover_id)
      DESTINATION KEY (to_crew_id) REFERENCES Crew (to_crew_id)
      LABEL HANDOVER_TO NO PROPERTIES,
    Handover AS HandoverFromCrew
      KEY (handover_id)
      SOURCE KEY (handover_id) REFERENCES Handover (handover_id)
      DESTINATION KEY (from_crew_id) REFERENCES Crew (from_crew_id)
      LABEL HANDOVER_FROM NO PROPERTIES,
    Calibration AS CalibrationOnMachine
      KEY (calibration_id)
      SOURCE KEY (calibration_id) REFERENCES Calibration (calibration_id)
      DESTINATION KEY (machine_id) REFERENCES Machine (machine_id)
      LABEL CALIBRATED NO PROPERTIES,
    Calibration AS CalibrationOrder
      KEY (calibration_id)
      SOURCE KEY (calibration_id) REFERENCES Calibration (calibration_id)
      DESTINATION KEY (order_id) REFERENCES MaintenanceOrder (order_id)
      LABEL CALIBRATION_ORDER NO PROPERTIES,
    Calibration AS CalibrationHandover
      KEY (calibration_id)
      SOURCE KEY (calibration_id) REFERENCES Calibration (calibration_id)
      DESTINATION KEY (handover_id) REFERENCES Handover (handover_id)
      LABEL DURING_HANDOVER NO PROPERTIES,
    MaintenanceOrder AS OrderTechnician
      KEY (order_id)
      SOURCE KEY (order_id) REFERENCES MaintenanceOrder (order_id)
      DESTINATION KEY (technician_id) REFERENCES Employee (technician_id)
      LABEL PERFORMED_BY_TECH NO PROPERTIES,
    TrainingRecord AS EmployeeTraining
      KEY (training_id)
      SOURCE KEY (employee_id) REFERENCES Employee (employee_id)
      DESTINATION KEY (training_id) REFERENCES TrainingRecord (training_id)
      LABEL HAS_TRAINING NO PROPERTIES,
    MillCertificate AS LotCertificate
      KEY (mill_cert_id)
      SOURCE KEY (lot_id) REFERENCES MaterialLot (lot_id)
      DESTINATION KEY (mill_cert_id) REFERENCES MillCertificate (mill_cert_id)
      LABEL HAS_CERT NO PROPERTIES,
    MillCertificate AS CertIssuer
      KEY (mill_cert_id)
      SOURCE KEY (mill_cert_id) REFERENCES MillCertificate (mill_cert_id)
      DESTINATION KEY (issued_by_supplier_id) REFERENCES Supplier (issued_by_supplier_id)
      LABEL ISSUED_BY NO PROPERTIES,
    Action AS IncidentAction
      KEY (action_id)
      SOURCE KEY (incident_id) REFERENCES Incident (incident_id)
      DESTINATION KEY (action_id) REFERENCES Action (action_id)
      LABEL HAS_ACTION NO PROPERTIES
  );
