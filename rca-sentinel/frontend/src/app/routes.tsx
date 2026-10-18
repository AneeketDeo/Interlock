import { createBrowserRouter, Navigate } from 'react-router-dom';
import { Shell } from './Shell';
import { CommandCenter } from '../features/command-center/CommandCenter';
import { IncidentDashboard } from '../features/incident/IncidentDashboard';
import { ImpactScreen } from '../features/impact/ImpactScreen';
import { ApprovalGate } from '../features/approvals/ApprovalGate';
import { SupplyChainScreen } from '../features/supply-chain/SupplyChainScreen';
import { MaintenanceScreen } from '../features/maintenance/MaintenanceScreen';
import { GraphExplorerScreen } from '../features/graph-explorer/GraphExplorerScreen';
import { ReportScreen } from '../features/report/ReportScreen';
import { DataTrustScreen } from '../features/trust/DataTrustScreen';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <Shell />,
    children: [
      { index: true, element: <CommandCenter /> },
      { path: 'incident', element: <IncidentDashboard /> },
      { path: 'impact', element: <ImpactScreen /> },
      { path: 'approvals', element: <ApprovalGate /> },
      { path: 'supply-chain', element: <SupplyChainScreen /> },
      { path: 'maintenance', element: <MaintenanceScreen /> },
      { path: 'graph', element: <GraphExplorerScreen /> },
      { path: 'report', element: <ReportScreen /> },
      { path: 'trust', element: <DataTrustScreen /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
