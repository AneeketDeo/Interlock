CREATE TABLE Action (
  action_id STRING(128) NOT NULL,
  incident_id STRING(128),
  decision_id STRING(128),
  action_type STRING(MAX),
  target_id STRING(128),
  description STRING(MAX),
  status STRING(MAX),
  proposed_by STRING(MAX),
  proposed_at TIMESTAMP,
  payload STRING(MAX),
) PRIMARY KEY(action_id);

CREATE TABLE Affects (
  incident_id STRING(128) NOT NULL,
  machine_id STRING(128) NOT NULL,
) PRIMARY KEY(incident_id, machine_id);

CREATE TABLE Alarm (
  alarm_id STRING(128) NOT NULL,
  sensor_id STRING(128),
  machine_id STRING(128),
  raised_at TIMESTAMP,
  severity STRING(MAX),
  rule STRING(MAX),
  value FLOAT64,
  threshold FLOAT64,
  acknowledged_by STRING(MAX),
) PRIMARY KEY(alarm_id);

CREATE TABLE Anomaly (
  anomaly_id STRING(128) NOT NULL,
  sensor_id STRING(128),
  machine_id STRING(128),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  windows INT64,
  peak_residual FLOAT64,
  anomaly_type STRING(MAX),
) PRIMARY KEY(anomaly_id);

CREATE TABLE Approval (
  approval_id STRING(128) NOT NULL,
  decision_id STRING(128),
  approver_id STRING(128),
  approved_at TIMESTAMP,
  outcome STRING(MAX),
) PRIMARY KEY(approval_id);

CREATE TABLE ApprovedBy (
  decision_id STRING(128) NOT NULL,
  approval_id STRING(128) NOT NULL,
) PRIMARY KEY(decision_id, approval_id);

CREATE TABLE Area (
  area_id STRING(128) NOT NULL,
  site_id STRING(128),
  name STRING(MAX),
) PRIMARY KEY(area_id);

CREATE TABLE Batch (
  batch_id STRING(128) NOT NULL,
  work_order_id STRING(128),
  product_code STRING(MAX),
  lot_id STRING(128),
  qty INT64,
  status STRING(MAX),
  machine_id STRING(128),
) PRIMARY KEY(batch_id);

CREATE TABLE Bom (
  bom_id STRING(128) NOT NULL,
  product_code STRING(MAX),
  material_id STRING(128),
  kg_per_unit FLOAT64,
) PRIMARY KEY(bom_id);

CREATE TABLE Calibration (
  calibration_id STRING(128) NOT NULL,
  order_id STRING(128),
  machine_id STRING(128),
  started_at TIMESTAMP,
  ended_at TIMESTAMP,
  steps_required INT64,
  steps_completed INT64,
  skipped_step STRING(MAX),
  duration_min INT64,
  handover_id STRING(128),
  recorded_result STRING(MAX),
  verification_signed_off BOOL,
) PRIMARY KEY(calibration_id);

CREATE TABLE Cause (
  cause_id STRING(128) NOT NULL,
  incident_id STRING(128),
  description STRING(MAX),
  category STRING(MAX),
  confidence FLOAT64,
) PRIMARY KEY(cause_id);

CREATE TABLE CauseMapsTo (
  cause_id STRING(128) NOT NULL,
  failure_mode_id STRING(128) NOT NULL,
) PRIMARY KEY(cause_id, failure_mode_id);

CREATE TABLE Component (
  component_id STRING(128) NOT NULL,
  machine_id STRING(128),
  name STRING(MAX),
) PRIMARY KEY(component_id);

CREATE TABLE ControlPlan (
  control_plan_id STRING(128) NOT NULL,
  failure_mode_id STRING(128),
  description STRING(MAX),
) PRIMARY KEY(control_plan_id);

CREATE TABLE ControlledBy (
  failure_mode_id STRING(128) NOT NULL,
  control_plan_id STRING(128) NOT NULL,
) PRIMARY KEY(failure_mode_id, control_plan_id);

CREATE TABLE CorrectedBy (
  incident_id STRING(128) NOT NULL,
  corrective_action_id STRING(128) NOT NULL,
) PRIMARY KEY(incident_id, corrective_action_id);

CREATE TABLE CorrectiveAction (
  corrective_action_id STRING(128) NOT NULL,
  incident_id STRING(128),
  description STRING(MAX),
  status STRING(MAX),
  owner_id STRING(128),
) PRIMARY KEY(corrective_action_id);

CREATE TABLE Crew (
  crew_id STRING(128) NOT NULL,
  name STRING(MAX),
) PRIMARY KEY(crew_id);

CREATE TABLE Decision (
  decision_id STRING(128) NOT NULL,
  incident_id STRING(128),
  decision_type STRING(MAX),
  proposed_by STRING(MAX),
  summary STRING(MAX),
  status STRING(MAX),
) PRIMARY KEY(decision_id);

CREATE TABLE DefectCode (
  defect_code STRING(128) NOT NULL,
  description STRING(MAX),
) PRIMARY KEY(defect_code);

CREATE TABLE Employee (
  employee_id STRING(128) NOT NULL,
  name STRING(MAX),
  role STRING(MAX),
  crew_id STRING(128),
) PRIMARY KEY(employee_id);

CREATE TABLE Evidence (
  evidence_id STRING(128) NOT NULL,
  incident_id STRING(128),
  evidence_type STRING(MAX),
  ref_id STRING(128),
  summary STRING(MAX),
) PRIMARY KEY(evidence_id);

CREATE TABLE EvidencedBy (
  incident_id STRING(128) NOT NULL,
  evidence_id STRING(128) NOT NULL,
) PRIMARY KEY(incident_id, evidence_id);

CREATE TABLE FailureMode (
  failure_mode_id STRING(128) NOT NULL,
  category STRING(MAX),
  description STRING(MAX),
  fm_severity INT64,
  occurrence INT64,
  detection INT64,
  rpn INT64,
) PRIMARY KEY(failure_mode_id);

CREATE TABLE Handover (
  handover_id STRING(128) NOT NULL,
  from_shift_id STRING(128),
  to_shift_id STRING(128),
  from_crew_id STRING(128),
  to_crew_id STRING(128),
  handover_time TIMESTAMP,
  duration_min INT64,
  checklist_complete BOOL,
  rushed BOOL,
  notes STRING(MAX),
) PRIMARY KEY(handover_id);

CREATE TABLE HasCause (
  incident_id STRING(128) NOT NULL,
  cause_id STRING(128) NOT NULL,
) PRIMARY KEY(incident_id, cause_id);

CREATE TABLE HasDecision (
  incident_id STRING(128) NOT NULL,
  decision_id STRING(128) NOT NULL,
) PRIMARY KEY(incident_id, decision_id);

CREATE TABLE Incident (
  incident_id STRING(128) NOT NULL,
  title STRING(MAX),
  status STRING(MAX),
  severity STRING(MAX),
  detected_at TIMESTAMP,
  detected_by STRING(MAX),
  metric STRING(MAX),
  baseline_value FLOAT64,
  observed_value FLOAT64,
  description STRING(MAX),
  line_ids STRING(MAX),
  closed_at TIMESTAMP,
) PRIMARY KEY(incident_id);

CREATE TABLE Inspection (
  inspection_id STRING(128) NOT NULL,
  work_order_id STRING(128),
  machine_id STRING(128),
  inspected_units INT64,
  scrap_units INT64,
  rework_units INT64,
  dominant_defect_code STRING(MAX),
  first_pass_yield FLOAT64,
) PRIMARY KEY(inspection_id);

CREATE TABLE Line (
  line_id STRING(128) NOT NULL,
  name STRING(MAX),
  area_id STRING(128),
  product_code STRING(MAX),
) PRIMARY KEY(line_id);

CREATE TABLE Machine (
  machine_id STRING(128) NOT NULL,
  line_id STRING(128),
  name STRING(MAX),
  machine_type STRING(MAX),
  install_year INT64,
) PRIMARY KEY(machine_id);

CREATE TABLE MaintenanceOn (
  order_id STRING(128) NOT NULL,
  machine_id STRING(128) NOT NULL,
) PRIMARY KEY(order_id, machine_id);

CREATE TABLE MaintenanceOrder (
  order_id STRING(128) NOT NULL,
  machine_id STRING(128),
  order_type STRING(MAX),
  plan_id STRING(128),
  crew_id STRING(128),
  technician_id STRING(128),
  scheduled_start TIMESTAMP,
  actual_start TIMESTAMP,
  actual_end TIMESTAMP,
  status STRING(MAX),
  spare_part_id STRING(128),
) PRIMARY KEY(order_id);

CREATE TABLE Material (
  material_id STRING(128) NOT NULL,
  name STRING(MAX),
  spec_hardness_hrc STRING(MAX),
  spec_carbon_pct STRING(MAX),
  spec_mn_pct STRING(MAX),
) PRIMARY KEY(material_id);

CREATE TABLE MaterialLot (
  lot_id STRING(128) NOT NULL,
  material_id STRING(128),
  qty_kg INT64,
  received_at TIMESTAMP,
  po_id STRING(128),
  mill_cert_id STRING(128),
  status STRING(MAX),
) PRIMARY KEY(lot_id);

CREATE TABLE MemberOf (
  employee_id STRING(128) NOT NULL,
  crew_id STRING(128) NOT NULL,
) PRIMARY KEY(employee_id, crew_id);

CREATE TABLE MillCertificate (
  mill_cert_id STRING(128) NOT NULL,
  lot_id STRING(128),
  heat_number STRING(MAX),
  issued_by_supplier_id STRING(128),
  hardness_hrc FLOAT64,
  carbon_pct FLOAT64,
  manganese_pct FLOAT64,
  within_spec BOOL,
  edge_flag STRING(MAX),
  document_ref STRING(MAX),
) PRIMARY KEY(mill_cert_id);

CREATE TABLE ObservationWindow (
  obs_id STRING(128) NOT NULL,
  sensor_id STRING(128),
  machine_id STRING(128),
  window_start TIMESTAMP,
  window_end TIMESTAMP,
  mean_value FLOAT64,
  min_value FLOAT64,
  max_value FLOAT64,
  std_dev FLOAT64,
  sample_count INT64,
  quality STRING(MAX),
  is_anomalous BOOL,
) PRIMARY KEY(obs_id);

CREATE TABLE PerformedBy (
  order_id STRING(128) NOT NULL,
  crew_id STRING(128) NOT NULL,
) PRIMARY KEY(order_id, crew_id);

CREATE TABLE PmPlan (
  plan_id STRING(128) NOT NULL,
  name STRING(MAX),
  interval_days INT64,
) PRIMARY KEY(plan_id);

CREATE TABLE Processed (
  machine_id STRING(128) NOT NULL,
  lot_id STRING(128) NOT NULL,
  first_used TIMESTAMP,
  last_used TIMESTAMP,
  work_orders INT64,
  units INT64,
) PRIMARY KEY(machine_id, lot_id);

CREATE TABLE Product (
  product_code STRING(128) NOT NULL,
  name STRING(MAX),
  line_id STRING(128),
) PRIMARY KEY(product_code);

CREATE TABLE PurchaseOrder (
  po_id STRING(128) NOT NULL,
  supplier_id STRING(128),
  material_id STRING(128),
  qty_kg INT64,
  ordered_at TIMESTAMP,
  received_at TIMESTAMP,
) PRIMARY KEY(po_id);

CREATE TABLE RecipeStep (
  recipe_step_id STRING(128) NOT NULL,
  line_id STRING(128),
  seq INT64,
  name STRING(MAX),
  temp_setpoint_c FLOAT64,
) PRIMARY KEY(recipe_step_id);

CREATE TABLE Sensor (
  sensor_id STRING(128) NOT NULL,
  machine_id STRING(128),
  component_id STRING(128),
  sensor_type STRING(MAX),
  unit STRING(MAX),
  sampling_hz INT64,
) PRIMARY KEY(sensor_id);

CREATE TABLE Shift (
  shift_id STRING(128) NOT NULL,
  shift_name STRING(MAX),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  crew_id STRING(128),
  status STRING(MAX),
) PRIMARY KEY(shift_id);

CREATE TABLE Site (
  site_id STRING(128) NOT NULL,
  name STRING(MAX),
  city STRING(MAX),
  country STRING(MAX),
) PRIMARY KEY(site_id);

CREATE TABLE SparePart (
  spare_part_id STRING(128) NOT NULL,
  name STRING(MAX),
  stock_qty INT64,
) PRIMARY KEY(spare_part_id);

CREATE TABLE SuppliedBy (
  lot_id STRING(128) NOT NULL,
  supplier_id STRING(128) NOT NULL,
  relation STRING(128) NOT NULL,
) PRIMARY KEY(lot_id, supplier_id, relation);

CREATE TABLE Supplier (
  supplier_id STRING(128) NOT NULL,
  name STRING(MAX),
  tier INT64,
  iatf_certified BOOL,
  shares_batch_data BOOL,
) PRIMARY KEY(supplier_id);

CREATE TABLE Supplies (
  supplier_id STRING(128) NOT NULL,
  buyer_supplier_id STRING(128) NOT NULL,
  material_id STRING(128),
) PRIMARY KEY(supplier_id, buyer_supplier_id);

CREATE TABLE Tag (
  tag_id STRING(128) NOT NULL,
  tag_name STRING(MAX),
  sensor_id STRING(128),
  protocol STRING(MAX),
  node_id STRING(128),
) PRIMARY KEY(tag_id);

CREATE TABLE TrainingRecord (
  training_id STRING(128) NOT NULL,
  employee_id STRING(128),
  machine_type STRING(MAX),
  issued TIMESTAMP,
  expires TIMESTAMP,
  status STRING(MAX),
) PRIMARY KEY(training_id);

CREATE TABLE WorkOrder (
  work_order_id STRING(128) NOT NULL,
  machine_id STRING(128),
  line_id STRING(128),
  shift_id STRING(128),
  operator_id STRING(128),
  product_code STRING(MAX),
  lot_id STRING(128),
  batch_id STRING(128),
  planned_start TIMESTAMP,
  planned_end TIMESTAMP,
  units_planned INT64,
  units_produced INT64,
  units_good INT64,
  units_scrap INT64,
  units_rework INT64,
  scrap_rate FLOAT64,
  status STRING(MAX),
) PRIMARY KEY(work_order_id);

CREATE OR REPLACE PROPERTY GRAPH FactoryGraph
  NODE TABLES(
    Action
      KEY(action_id)
      LABEL Action PROPERTIES(
        action_id,
        action_type,
        decision_id,
        description,
        incident_id,
        payload,
        proposed_at,
        proposed_by,
        status,
        target_id),

    Alarm
      KEY(alarm_id)
      LABEL Alarm PROPERTIES(
        acknowledged_by,
        alarm_id,
        machine_id,
        raised_at,
        rule,
        sensor_id,
        severity,
        threshold,
        value),

    Anomaly
      KEY(anomaly_id)
      LABEL Anomaly PROPERTIES(
        anomaly_id,
        anomaly_type,
        end_time,
        machine_id,
        peak_residual,
        sensor_id,
        start_time,
        windows),

    Approval
      KEY(approval_id)
      LABEL Approval PROPERTIES(
        approval_id,
        approved_at,
        approver_id,
        decision_id,
        outcome),

    Area
      KEY(area_id)
      LABEL Area PROPERTIES(
        area_id,
        name,
        site_id),

    Batch
      KEY(batch_id)
      LABEL Batch PROPERTIES(
        batch_id,
        lot_id,
        machine_id,
        product_code,
        qty,
        status,
        work_order_id),

    Bom
      KEY(bom_id)
      LABEL Bom PROPERTIES(
        bom_id,
        kg_per_unit,
        material_id,
        product_code),

    Calibration
      KEY(calibration_id)
      LABEL Calibration PROPERTIES(
        calibration_id,
        duration_min,
        ended_at,
        handover_id,
        machine_id,
        order_id,
        recorded_result,
        skipped_step,
        started_at,
        steps_completed,
        steps_required,
        verification_signed_off),

    Cause
      KEY(cause_id)
      LABEL Cause PROPERTIES(
        category,
        cause_id,
        confidence,
        description,
        incident_id),

    Component
      KEY(component_id)
      LABEL Component PROPERTIES(
        component_id,
        machine_id,
        name),

    ControlPlan
      KEY(control_plan_id)
      LABEL ControlPlan PROPERTIES(
        control_plan_id,
        description,
        failure_mode_id),

    CorrectiveAction
      KEY(corrective_action_id)
      LABEL CorrectiveAction PROPERTIES(
        corrective_action_id,
        description,
        incident_id,
        owner_id,
        status),

    Crew
      KEY(crew_id)
      LABEL Crew PROPERTIES(
        crew_id,
        name),

    Decision
      KEY(decision_id)
      LABEL Decision PROPERTIES(
        decision_id,
        decision_type,
        incident_id,
        proposed_by,
        status,
        summary),

    DefectCode
      KEY(defect_code)
      LABEL DefectCode PROPERTIES(
        defect_code,
        description),

    Employee
      KEY(employee_id)
      LABEL Employee PROPERTIES(
        crew_id,
        employee_id,
        name,
        role),

    Evidence
      KEY(evidence_id)
      LABEL Evidence PROPERTIES(
        evidence_id,
        evidence_type,
        incident_id,
        ref_id,
        summary),

    FailureMode
      KEY(failure_mode_id)
      LABEL FailureMode PROPERTIES(
        category,
        description,
        detection,
        failure_mode_id,
        fm_severity,
        occurrence,
        rpn),

    Handover
      KEY(handover_id)
      LABEL Handover PROPERTIES(
        checklist_complete,
        duration_min,
        from_crew_id,
        from_shift_id,
        handover_id,
        handover_time,
        notes,
        rushed,
        to_crew_id,
        to_shift_id),

    Incident
      KEY(incident_id)
      LABEL Incident PROPERTIES(
        baseline_value,
        closed_at,
        description,
        detected_at,
        detected_by,
        incident_id,
        line_ids,
        metric,
        observed_value,
        severity,
        status,
        title),

    Inspection
      KEY(inspection_id)
      LABEL Inspection PROPERTIES(
        dominant_defect_code,
        first_pass_yield,
        inspected_units,
        inspection_id,
        machine_id,
        rework_units,
        scrap_units,
        work_order_id),

    Line
      KEY(line_id)
      LABEL Line PROPERTIES(
        area_id,
        line_id,
        name,
        product_code),

    Machine
      KEY(machine_id)
      LABEL Machine PROPERTIES(
        install_year,
        line_id,
        machine_id,
        machine_type,
        name),

    MaintenanceOrder
      KEY(order_id)
      LABEL MaintenanceOrder PROPERTIES(
        actual_end,
        actual_start,
        crew_id,
        machine_id,
        order_id,
        order_type,
        plan_id,
        scheduled_start,
        spare_part_id,
        status,
        technician_id),

    Material
      KEY(material_id)
      LABEL Material PROPERTIES(
        material_id,
        name,
        spec_carbon_pct,
        spec_hardness_hrc,
        spec_mn_pct),

    MaterialLot
      KEY(lot_id)
      LABEL MaterialLot PROPERTIES(
        lot_id,
        material_id,
        mill_cert_id,
        po_id,
        qty_kg,
        received_at,
        status),

    MillCertificate
      KEY(mill_cert_id)
      LABEL MillCertificate PROPERTIES(
        carbon_pct,
        document_ref,
        edge_flag,
        hardness_hrc,
        heat_number,
        issued_by_supplier_id,
        lot_id,
        manganese_pct,
        mill_cert_id,
        within_spec),

    ObservationWindow
      KEY(obs_id)
      LABEL ObservationWindow PROPERTIES(
        is_anomalous,
        machine_id,
        max_value,
        mean_value,
        min_value,
        obs_id,
        quality,
        sample_count,
        sensor_id,
        std_dev,
        window_end,
        window_start),

    PmPlan
      KEY(plan_id)
      LABEL PmPlan PROPERTIES(
        interval_days,
        name,
        plan_id),

    Product
      KEY(product_code)
      LABEL Product PROPERTIES(
        line_id,
        name,
        product_code),

    PurchaseOrder
      KEY(po_id)
      LABEL PurchaseOrder PROPERTIES(
        material_id,
        ordered_at,
        po_id,
        qty_kg,
        received_at,
        supplier_id),

    RecipeStep
      KEY(recipe_step_id)
      LABEL RecipeStep PROPERTIES(
        line_id,
        name,
        recipe_step_id,
        seq,
        temp_setpoint_c),

    Sensor
      KEY(sensor_id)
      LABEL Sensor PROPERTIES(
        component_id,
        machine_id,
        sampling_hz,
        sensor_id,
        sensor_type,
        unit),

    Shift
      KEY(shift_id)
      LABEL Shift PROPERTIES(
        crew_id,
        end_time,
        shift_id,
        shift_name,
        start_time,
        status),

    Site
      KEY(site_id)
      LABEL Site PROPERTIES(
        city,
        country,
        name,
        site_id),

    SparePart
      KEY(spare_part_id)
      LABEL SparePart PROPERTIES(
        name,
        spare_part_id,
        stock_qty),

    Supplier
      KEY(supplier_id)
      LABEL Supplier PROPERTIES(
        iatf_certified,
        name,
        shares_batch_data,
        supplier_id,
        tier),

    Tag
      KEY(tag_id)
      LABEL Tag PROPERTIES(
        node_id,
        protocol,
        sensor_id,
        tag_id,
        tag_name),

    TrainingRecord
      KEY(training_id)
      LABEL TrainingRecord PROPERTIES(
        employee_id,
        expires,
        issued,
        machine_type,
        status,
        training_id),

    WorkOrder
      KEY(work_order_id)
      LABEL WorkOrder PROPERTIES(
        batch_id,
        line_id,
        lot_id,
        machine_id,
        operator_id,
        planned_end,
        planned_start,
        product_code,
        scrap_rate,
        shift_id,
        status,
        units_good,
        units_planned,
        units_produced,
        units_rework,
        units_scrap,
        work_order_id)
  )
  EDGE TABLES(
    Affects
      KEY(incident_id, machine_id)
      SOURCE KEY(incident_id) REFERENCES Incident(incident_id)
      DESTINATION KEY(machine_id) REFERENCES Machine(machine_id)
      LABEL AFFECTS PROPERTIES(
        incident_id,
        machine_id),

    ApprovedBy
      KEY(decision_id, approval_id)
      SOURCE KEY(decision_id) REFERENCES Decision(decision_id)
      DESTINATION KEY(approval_id) REFERENCES Approval(approval_id)
      LABEL APPROVED_BY PROPERTIES(
        approval_id,
        decision_id),

    Line AS AreaHasLine
      KEY(line_id)
      SOURCE KEY(area_id) REFERENCES Area(area_id)
      DESTINATION KEY(line_id) REFERENCES Line(line_id)
      LABEL HAS_LINE NO PROPERTIES,

    Calibration AS CalibrationHandover
      KEY(calibration_id)
      SOURCE KEY(calibration_id) REFERENCES Calibration(calibration_id)
      DESTINATION KEY(handover_id) REFERENCES Handover(handover_id)
      LABEL DURING_HANDOVER NO PROPERTIES,

    Calibration AS CalibrationOnMachine
      KEY(calibration_id)
      SOURCE KEY(calibration_id) REFERENCES Calibration(calibration_id)
      DESTINATION KEY(machine_id) REFERENCES Machine(machine_id)
      LABEL CALIBRATED NO PROPERTIES,

    Calibration AS CalibrationOrder
      KEY(calibration_id)
      SOURCE KEY(calibration_id) REFERENCES Calibration(calibration_id)
      DESTINATION KEY(order_id) REFERENCES MaintenanceOrder(order_id)
      LABEL CALIBRATION_ORDER NO PROPERTIES,

    CauseMapsTo
      KEY(cause_id, failure_mode_id)
      SOURCE KEY(cause_id) REFERENCES Cause(cause_id)
      DESTINATION KEY(failure_mode_id) REFERENCES FailureMode(failure_mode_id)
      LABEL CAUSE_MAPS_TO PROPERTIES(
        cause_id,
        failure_mode_id),

    MillCertificate AS CertIssuer
      KEY(mill_cert_id)
      SOURCE KEY(mill_cert_id) REFERENCES MillCertificate(mill_cert_id)
      DESTINATION KEY(issued_by_supplier_id) REFERENCES Supplier(supplier_id)
      LABEL ISSUED_BY NO PROPERTIES,

    ControlledBy
      KEY(failure_mode_id, control_plan_id)
      SOURCE KEY(failure_mode_id) REFERENCES FailureMode(failure_mode_id)
      DESTINATION KEY(control_plan_id) REFERENCES ControlPlan(control_plan_id)
      LABEL CONTROLLED_BY PROPERTIES(
        control_plan_id,
        failure_mode_id),

    CorrectedBy
      KEY(incident_id, corrective_action_id)
      SOURCE KEY(incident_id) REFERENCES Incident(incident_id)
      DESTINATION KEY(corrective_action_id) REFERENCES CorrectiveAction(corrective_action_id)
      LABEL CORRECTED_BY PROPERTIES(
        corrective_action_id,
        incident_id),

    TrainingRecord AS EmployeeTraining
      KEY(training_id)
      SOURCE KEY(employee_id) REFERENCES Employee(employee_id)
      DESTINATION KEY(training_id) REFERENCES TrainingRecord(training_id)
      LABEL HAS_TRAINING NO PROPERTIES,

    EvidencedBy
      KEY(incident_id, evidence_id)
      SOURCE KEY(incident_id) REFERENCES Incident(incident_id)
      DESTINATION KEY(evidence_id) REFERENCES Evidence(evidence_id)
      LABEL EVIDENCED_BY PROPERTIES(
        evidence_id,
        incident_id),

    Handover AS HandoverFromCrew
      KEY(handover_id)
      SOURCE KEY(handover_id) REFERENCES Handover(handover_id)
      DESTINATION KEY(from_crew_id) REFERENCES Crew(crew_id)
      LABEL HANDOVER_FROM NO PROPERTIES,

    Handover AS HandoverToCrew
      KEY(handover_id)
      SOURCE KEY(handover_id) REFERENCES Handover(handover_id)
      DESTINATION KEY(to_crew_id) REFERENCES Crew(crew_id)
      LABEL HANDOVER_TO NO PROPERTIES,

    HasCause
      KEY(incident_id, cause_id)
      SOURCE KEY(incident_id) REFERENCES Incident(incident_id)
      DESTINATION KEY(cause_id) REFERENCES Cause(cause_id)
      LABEL HAS_CAUSE PROPERTIES(
        cause_id,
        incident_id),

    HasDecision
      KEY(incident_id, decision_id)
      SOURCE KEY(incident_id) REFERENCES Incident(incident_id)
      DESTINATION KEY(decision_id) REFERENCES Decision(decision_id)
      LABEL HAS_DECISION PROPERTIES(
        decision_id,
        incident_id),

    Action AS IncidentAction
      KEY(action_id)
      SOURCE KEY(incident_id) REFERENCES Incident(incident_id)
      DESTINATION KEY(action_id) REFERENCES Action(action_id)
      LABEL HAS_ACTION NO PROPERTIES,

    Machine AS LineHasMachine
      KEY(machine_id)
      SOURCE KEY(line_id) REFERENCES Line(line_id)
      DESTINATION KEY(machine_id) REFERENCES Machine(machine_id)
      LABEL HAS_MACHINE NO PROPERTIES,

    MillCertificate AS LotCertificate
      KEY(mill_cert_id)
      SOURCE KEY(lot_id) REFERENCES MaterialLot(lot_id)
      DESTINATION KEY(mill_cert_id) REFERENCES MillCertificate(mill_cert_id)
      LABEL HAS_CERT NO PROPERTIES,

    Component AS MachineHasComponent
      KEY(component_id)
      SOURCE KEY(machine_id) REFERENCES Machine(machine_id)
      DESTINATION KEY(component_id) REFERENCES Component(component_id)
      LABEL HAS_COMPONENT NO PROPERTIES,

    Sensor AS MachineHasSensor
      KEY(sensor_id)
      SOURCE KEY(machine_id) REFERENCES Machine(machine_id)
      DESTINATION KEY(sensor_id) REFERENCES Sensor(sensor_id)
      LABEL HAS_SENSOR NO PROPERTIES,

    MaintenanceOn
      KEY(order_id, machine_id)
      SOURCE KEY(order_id) REFERENCES MaintenanceOrder(order_id)
      DESTINATION KEY(machine_id) REFERENCES Machine(machine_id)
      LABEL MAINTENANCE_ON PROPERTIES(
        machine_id,
        order_id),

    MemberOf
      KEY(employee_id, crew_id)
      SOURCE KEY(employee_id) REFERENCES Employee(employee_id)
      DESTINATION KEY(crew_id) REFERENCES Crew(crew_id)
      LABEL MEMBER_OF PROPERTIES(
        crew_id,
        employee_id),

    MaintenanceOrder AS OrderTechnician
      KEY(order_id)
      SOURCE KEY(order_id) REFERENCES MaintenanceOrder(order_id)
      DESTINATION KEY(technician_id) REFERENCES Employee(employee_id)
      LABEL PERFORMED_BY_TECH NO PROPERTIES,

    PerformedBy
      KEY(order_id, crew_id)
      SOURCE KEY(order_id) REFERENCES MaintenanceOrder(order_id)
      DESTINATION KEY(crew_id) REFERENCES Crew(crew_id)
      LABEL PERFORMED_BY PROPERTIES(
        crew_id,
        order_id),

    Processed
      KEY(machine_id, lot_id)
      SOURCE KEY(machine_id) REFERENCES Machine(machine_id)
      DESTINATION KEY(lot_id) REFERENCES MaterialLot(lot_id)
      LABEL PROCESSED PROPERTIES(
        first_used,
        last_used,
        lot_id,
        machine_id,
        units,
        work_orders),

    Alarm AS SensorHasAlarm
      KEY(alarm_id)
      SOURCE KEY(sensor_id) REFERENCES Sensor(sensor_id)
      DESTINATION KEY(alarm_id) REFERENCES Alarm(alarm_id)
      LABEL HAS_ALARM NO PROPERTIES,

    Anomaly AS SensorHasAnomaly
      KEY(anomaly_id)
      SOURCE KEY(sensor_id) REFERENCES Sensor(sensor_id)
      DESTINATION KEY(anomaly_id) REFERENCES Anomaly(anomaly_id)
      LABEL HAS_ANOMALY NO PROPERTIES,

    ObservationWindow AS SensorHasObservation
      KEY(obs_id)
      SOURCE KEY(sensor_id) REFERENCES Sensor(sensor_id)
      DESTINATION KEY(obs_id) REFERENCES ObservationWindow(obs_id)
      LABEL HAS_OBSERVATION NO PROPERTIES,

    Tag AS SensorHasTag
      KEY(tag_id)
      SOURCE KEY(sensor_id) REFERENCES Sensor(sensor_id)
      DESTINATION KEY(tag_id) REFERENCES Tag(tag_id)
      LABEL HAS_TAG NO PROPERTIES,

    Shift AS ShiftCrew
      KEY(shift_id)
      SOURCE KEY(shift_id) REFERENCES Shift(shift_id)
      DESTINATION KEY(crew_id) REFERENCES Crew(crew_id)
      LABEL SHIFT_CREW NO PROPERTIES,

    Area AS SiteHasArea
      KEY(area_id)
      SOURCE KEY(site_id) REFERENCES Site(site_id)
      DESTINATION KEY(area_id) REFERENCES Area(area_id)
      LABEL HAS_AREA NO PROPERTIES,

    SuppliedBy
      KEY(lot_id, supplier_id, relation)
      SOURCE KEY(lot_id) REFERENCES MaterialLot(lot_id)
      DESTINATION KEY(supplier_id) REFERENCES Supplier(supplier_id)
      LABEL SUPPLIED_BY PROPERTIES(
        lot_id,
        relation,
        supplier_id),

    Supplies
      KEY(supplier_id, buyer_supplier_id)
      SOURCE KEY(supplier_id) REFERENCES Supplier(supplier_id)
      DESTINATION KEY(buyer_supplier_id) REFERENCES Supplier(supplier_id)
      LABEL SUPPLIES PROPERTIES(
        buyer_supplier_id,
        material_id,
        supplier_id),

    Batch AS WorkOrderBatch
      KEY(batch_id)
      SOURCE KEY(work_order_id) REFERENCES WorkOrder(work_order_id)
      DESTINATION KEY(batch_id) REFERENCES Batch(batch_id)
      LABEL PRODUCED_BATCH NO PROPERTIES,

    Inspection AS WorkOrderInspection
      KEY(inspection_id)
      SOURCE KEY(work_order_id) REFERENCES WorkOrder(work_order_id)
      DESTINATION KEY(inspection_id) REFERENCES Inspection(inspection_id)
      LABEL HAS_INSPECTION NO PROPERTIES,

    WorkOrder AS WorkOrderLot
      KEY(work_order_id)
      SOURCE KEY(work_order_id) REFERENCES WorkOrder(work_order_id)
      DESTINATION KEY(lot_id) REFERENCES MaterialLot(lot_id)
      LABEL CONSUMED_LOT NO PROPERTIES,

    WorkOrder AS WorkOrderOnMachine
      KEY(work_order_id)
      SOURCE KEY(work_order_id) REFERENCES WorkOrder(work_order_id)
      DESTINATION KEY(machine_id) REFERENCES Machine(machine_id)
      LABEL RAN_ON NO PROPERTIES,

    WorkOrder AS WorkOrderOperator
      KEY(work_order_id)
      SOURCE KEY(work_order_id) REFERENCES WorkOrder(work_order_id)
      DESTINATION KEY(operator_id) REFERENCES Employee(employee_id)
      LABEL OPERATED_BY NO PROPERTIES,

    WorkOrder AS WorkOrderShift
      KEY(work_order_id)
      SOURCE KEY(work_order_id) REFERENCES WorkOrder(work_order_id)
      DESTINATION KEY(shift_id) REFERENCES Shift(shift_id)
      LABEL IN_SHIFT NO PROPERTIES
  );

