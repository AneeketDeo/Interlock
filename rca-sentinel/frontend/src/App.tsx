import React from 'react';
import { Activity, ShieldCheck, Cpu, Database } from 'lucide-react';

export default function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 font-sans p-6">
      <header className="border-b border-slate-800 pb-4 mb-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Activity className="h-6 w-6 text-emerald-400" />
            RCA-Sentinel Manufacturing Console
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Agentic Knowledge-Graph-Driven Diagnostic &amp; Remediation Platform
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
            System Online
          </span>
        </div>
      </header>
      <main className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-2">
            <Cpu className="h-5 w-5 text-blue-400" /> Real-time Anomaly Detection
          </h2>
          <p className="text-sm text-slate-400">
            Streaming EWMA/CUSUM analysis active on telemetry streams.
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-2">
            <Database className="h-5 w-5 text-purple-400" /> Knowledge Graph
          </h2>
          <p className="text-sm text-slate-400">
            Neo4j Aura connected with manufacturing ontology and multi-hop lineage.
          </p>
        </div>
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-5">
          <h2 className="text-lg font-semibold text-white flex items-center gap-2 mb-2">
            <ShieldCheck className="h-5 w-5 text-amber-400" /> HITL Safety Engine
          </h2>
          <p className="text-sm text-slate-400">
            DRY_RUN mode active. All actuator interventions gated by engineer approval.
          </p>
        </div>
      </main>
    </div>
  );
}
