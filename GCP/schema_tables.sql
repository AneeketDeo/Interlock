CREATE TABLE Site (
  site_id STRING(128) NOT NULL,
  name STRING(MAX),
  city STRING(MAX),
  country STRING(MAX)
) PRIMARY KEY (site_id);

CREATE TABLE Area (
  area_id STRING(128) NOT NULL,
  site_id STRING(128),
  name STRING(MAX)
) PRIMARY KEY (area_id);

CREATE TABLE Line (
  line_id STRING(128) NOT NULL,
  name STRING(MAX),
  area_id STRING(128),
  product_code STRING(MAX)
) PRIMARY KEY (line_id);

CREATE TABLE Machine (
  machine_id STRING(128) NOT NULL,
  line_id STRING(128),
  name STRING(MAX),
  machine_type STRING(MAX),
  install_year INT64
) PRIMARY KEY (machine_id);

CREATE TABLE Component (
  component_id STRING(128) NOT NULL,
  machine_id STRING(128),
  name STRING(MAX)
) PRIMARY KEY (component_id);

CREATE TABLE Sensor (
  sensor_id STRING(128) NOT NULL,
  machine_id STRING(128),
  component_id STRING(128),
  sensor_type STRING(MAX),
  unit STRING(MAX),
  sampling_hz INT64
) PRIMARY KEY (sensor_id);

CREATE TABLE Tag (
  tag_id STRING(128) NOT NULL,
  tag_name STRING(MAX),
  sensor_id STRING(128),
  protocol STRING(MAX),
  node_id STRING(128)
) PRIMARY KEY (tag_id);

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
  is_anomalous BOOL
) PRIMARY KEY (obs_id);

CREATE TABLE Alarm (
  alarm_id STRING(128) NOT NULL,
  sensor_id STRING(128),
  machine_id STRING(128),
  raised_at TIMESTAMP,
  severity STRING(MAX),
  rule STRING(MAX),
  value FLOAT64,
  threshold FLOAT64,
  acknowledged_by STRING(MAX)
) PRIMARY KEY (alarm_id);

CREATE TABLE Anomaly (
  anomaly_id STRING(128) NOT NULL,
  sensor_id STRING(128),
  machine_id STRING(128),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  windows INT64,
  peak_residual FLOAT64,
  anomaly_type STRING(MAX)
) PRIMARY KEY (anomaly_id);

CREATE TABLE Product (
  product_code STRING(128) NOT NULL,
  name STRING(MAX),
  line_id STRING(128)
) PRIMARY KEY (product_code);

CREATE TABLE RecipeStep (
  recipe_step_id STRING(128) NOT NULL,
  line_id STRING(128),
  seq INT64,
  name STRING(MAX),
  temp_setpoint_c FLOAT64
) PRIMARY KEY (recipe_step_id);

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
  status STRING(MAX)
) PRIMARY KEY (work_order_id);

CREATE TABLE Batch (
  batch_id STRING(128) NOT NULL,
  work_order_id STRING(128),
  product_code STRING(MAX),
  lot_id STRING(128),
  qty INT64,
  status STRING(MAX),
  machine_id STRING(128)
) PRIMARY KEY (batch_id);

CREATE TABLE Inspection (
  inspection_id STRING(128) NOT NULL,
  work_order_id STRING(128),
  machine_id STRING(128),
  inspected_units INT64,
  scrap_units INT64,
  rework_units INT64,
  dominant_defect_code STRING(MAX),
  first_pass_yield FLOAT64
) PRIMARY KEY (inspection_id);

CREATE TABLE DefectCode (
  defect_code STRING(128) NOT NULL,
  description STRING(MAX)
) PRIMARY KEY (defect_code);

CREATE TABLE Employee (
  employee_id STRING(128) NOT NULL,
  name STRING(MAX),
  role STRING(MAX),
  crew_id STRING(128)
) PRIMARY KEY (employee_id);

CREATE TABLE Crew (
  crew_id STRING(128) NOT NULL,
  name STRING(MAX)
) PRIMARY KEY (crew_id);

CREATE TABLE Shift (
  shift_id STRING(128) NOT NULL,
  shift_name STRING(MAX),
  start_time TIMESTAMP,
  end_time TIMESTAMP,
  crew_id STRING(128),
  status STRING(MAX)
) PRIMARY KEY (shift_id);

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
  notes STRING(MAX)
) PRIMARY KEY (handover_id);

CREATE TABLE TrainingRecord (
  training_id STRING(128) NOT NULL,
  employee_id STRING(128),
  machine_type STRING(MAX),
  issued TIMESTAMP,
  expires TIMESTAMP,
  status STRING(MAX)
) PRIMARY KEY (training_id);

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
  spare_part_id STRING(128)
) PRIMARY KEY (order_id);

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
  verification_signed_off BOOL
) PRIMARY KEY (calibration_id);

CREATE TABLE PmPlan (
  plan_id STRING(128) NOT NULL,
  name STRING(MAX),
  interval_days INT64
) PRIMARY KEY (plan_id);

CREATE TABLE SparePart (
  spare_part_id STRING(128) NOT NULL,
  name STRING(MAX),
  stock_qty INT64
) PRIMARY KEY (spare_part_id);

CREATE TABLE Supplier (
  supplier_id STRING(128) NOT NULL,
  name STRING(MAX),
  tier INT64,
  iatf_certified BOOL,
  shares_batch_data BOOL
) PRIMARY KEY (supplier_id);

CREATE TABLE Material (
  material_id STRING(128) NOT NULL,
  name STRING(MAX),
  spec_hardness_hrc STRING(MAX),
  spec_carbon_pct STRING(MAX),
  spec_mn_pct STRING(MAX)
) PRIMARY KEY (material_id);

CREATE TABLE Bom (
  bom_id STRING(128) NOT NULL,
  product_code STRING(MAX),
  material_id STRING(128),
  kg_per_unit FLOAT64
) PRIMARY KEY (bom_id);

CREATE TABLE MaterialLot (
  lot_id STRING(128) NOT NULL,
  material_id STRING(128),
  qty_kg INT64,
  received_at TIMESTAMP,
  po_id STRING(128),
  mill_cert_id STRING(128),
  status STRING(MAX)
) PRIMARY KEY (lot_id);

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
  document_ref STRING(MAX)
) PRIMARY KEY (mill_cert_id);

CREATE TABLE PurchaseOrder (
  po_id STRING(128) NOT NULL,
  supplier_id STRING(128),
  material_id STRING(128),
  qty_kg INT64,
  ordered_at TIMESTAMP,
  received_at TIMESTAMP
) PRIMARY KEY (po_id);

CREATE TABLE FailureMode (
  failure_mode_id STRING(128) NOT NULL,
  category STRING(MAX),
  description STRING(MAX),
  severity INT64,
  occurrence INT64,
  detection INT64,
  rpn INT64
) PRIMARY KEY (failure_mode_id);

CREATE TABLE ControlPlan (
  control_plan_id STRING(128) NOT NULL,
  failure_mode_id STRING(128),
  description STRING(MAX)
) PRIMARY KEY (control_plan_id);

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
  closed_at TIMESTAMP
) PRIMARY KEY (incident_id);

CREATE TABLE Evidence (
  evidence_id STRING(128) NOT NULL,
  incident_id STRING(128),
  evidence_type STRING(MAX),
  ref_id STRING(128),
  summary STRING(MAX)
) PRIMARY KEY (evidence_id);

CREATE TABLE Cause (
  cause_id STRING(128) NOT NULL,
  incident_id STRING(128),
  description STRING(MAX),
  category STRING(MAX),
  confidence FLOAT64
) PRIMARY KEY (cause_id);

CREATE TABLE CorrectiveAction (
  corrective_action_id STRING(128) NOT NULL,
  incident_id STRING(128),
  description STRING(MAX),
  status STRING(MAX),
  owner_id STRING(128)
) PRIMARY KEY (corrective_action_id);

CREATE TABLE Decision (
  decision_id STRING(128) NOT NULL,
  incident_id STRING(128),
  decision_type STRING(MAX),
  proposed_by STRING(MAX),
  summary STRING(MAX),
  status STRING(MAX)
) PRIMARY KEY (decision_id);

CREATE TABLE Approval (
  approval_id STRING(128) NOT NULL,
  decision_id STRING(128),
  approver_id STRING(128),
  approved_at TIMESTAMP,
  outcome STRING(MAX)
) PRIMARY KEY (approval_id);

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
  payload STRING(MAX)
) PRIMARY KEY (action_id);

CREATE TABLE Processed (
  machine_id STRING(128) NOT NULL,
  lot_id STRING(128) NOT NULL,
  first_used TIMESTAMP,
  last_used TIMESTAMP,
  work_orders INT64,
  units INT64
) PRIMARY KEY (machine_id, lot_id);

CREATE TABLE SuppliedBy (
  lot_id STRING(128) NOT NULL,
  supplier_id STRING(128) NOT NULL,
  relation STRING(128) NOT NULL
) PRIMARY KEY (lot_id, supplier_id, relation);

CREATE TABLE Supplies (
  supplier_id STRING(128) NOT NULL,
  buyer_supplier_id STRING(128) NOT NULL,
  material_id STRING(128)
) PRIMARY KEY (supplier_id, buyer_supplier_id);

CREATE TABLE MaintenanceOn (
  order_id STRING(128) NOT NULL,
  machine_id STRING(128) NOT NULL
) PRIMARY KEY (order_id, machine_id);

CREATE TABLE PerformedBy (
  order_id STRING(128) NOT NULL,
  crew_id STRING(128) NOT NULL
) PRIMARY KEY (order_id, crew_id);

CREATE TABLE MemberOf (
  employee_id STRING(128) NOT NULL,
  crew_id STRING(128) NOT NULL
) PRIMARY KEY (employee_id, crew_id);

CREATE TABLE Affects (
  incident_id STRING(128) NOT NULL,
  machine_id STRING(128) NOT NULL
) PRIMARY KEY (incident_id, machine_id);

CREATE TABLE EvidencedBy (
  incident_id STRING(128) NOT NULL,
  evidence_id STRING(128) NOT NULL
) PRIMARY KEY (incident_id, evidence_id);

CREATE TABLE HasCause (
  incident_id STRING(128) NOT NULL,
  cause_id STRING(128) NOT NULL
) PRIMARY KEY (incident_id, cause_id);

CREATE TABLE CauseMapsTo (
  cause_id STRING(128) NOT NULL,
  failure_mode_id STRING(128) NOT NULL
) PRIMARY KEY (cause_id, failure_mode_id);

CREATE TABLE CorrectedBy (
  incident_id STRING(128) NOT NULL,
  corrective_action_id STRING(128) NOT NULL
) PRIMARY KEY (incident_id, corrective_action_id);

CREATE TABLE HasDecision (
  incident_id STRING(128) NOT NULL,
  decision_id STRING(128) NOT NULL
) PRIMARY KEY (incident_id, decision_id);

CREATE TABLE ApprovedBy (
  decision_id STRING(128) NOT NULL,
  approval_id STRING(128) NOT NULL
) PRIMARY KEY (decision_id, approval_id);

CREATE TABLE ControlledBy (
  failure_mode_id STRING(128) NOT NULL,
  control_plan_id STRING(128) NOT NULL
) PRIMARY KEY (failure_mode_id, control_plan_id);
