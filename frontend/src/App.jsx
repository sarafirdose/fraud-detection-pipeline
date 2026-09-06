import React, { useState, useEffect, useCallback } from 'react';
import Navbar from './components/Navbar';
import KpiCards from './components/KpiCards';
import SimulatorControl from './components/SimulatorControl';
import LiveTransactionFeed from './components/LiveTransactionFeed';
import AlertPanel from './components/AlertPanel';
import TransactionModal from './components/TransactionModal';
import TelemetryModal from './components/TelemetryModal';
import FraudAnalytics from './components/FraudAnalytics';
import ModelDiagnostics from './components/ModelDiagnostics';
import ModelComparisonView from './components/ModelComparisonView';
import {
  fetchHealth,
  fetchStats,
  fetchRecentTransactions,
  fetchRecentAlerts,
  fetchTimeseriesAnalytics,
  fetchDistributions,
  fetchModelInfo,
  fetchModelMode,
  fetchSimulatorStatus,
  LiveStreamWebSocket
} from './services/api';
import { Activity, BarChart3, BrainCircuit, Cpu } from 'lucide-react';

export default function App() {
  // State
  const [activeTab, setActiveTab] = useState('live'); // 'live' | 'analytics' | 'model' | 'comparison'
  const [wsStatus, setWsStatus] = useState('connecting');
  const [health, setHealth] = useState(null);
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [timeseries, setTimeseries] = useState([]);
  const [distributions, setDistributions] = useState(null);
  const [modelInfo, setModelInfo] = useState(null);
  const [activeMode, setActiveMode] = useState('SUPERVISED_XGBOOST');
  const [simStatus, setSimStatus] = useState(null);
  const [selectedTx, setSelectedTx] = useState(null);
  const [telemetryState, setTelemetryState] = useState({ isOpen: false, tab: 'prometheus' });

  // Fetch initial REST data
  const loadInitialData = useCallback(async () => {
    try {
      const [h, st, txs, alts, ts, dist, mod, modeRes, sim] = await Promise.all([
        fetchHealth().catch(() => null),
        fetchStats().catch(() => null),
        fetchRecentTransactions(40).catch(() => []),
        fetchRecentAlerts(20).catch(() => []),
        fetchTimeseriesAnalytics().catch(() => []),
        fetchDistributions().catch(() => null),
        fetchModelInfo().catch(() => null),
        fetchModelMode().catch(() => null),
        fetchSimulatorStatus().catch(() => null)
      ]);

      if (h) setHealth(h);
      if (st) setStats(st);
      if (txs) setTransactions(txs);
      if (alts) setAlerts(alts);
      if (ts) setTimeseries(ts);
      if (dist) setDistributions(dist);
      if (mod) setModelInfo(mod);
      if (modeRes?.active_mode) setActiveMode(modeRes.active_mode);
      if (sim) setSimStatus(sim);
    } catch (err) {
      console.error('Error during initial fetch', err);
    }
  }, []);

  // Periodic slow poll for analytics & health sync
  useEffect(() => {
    loadInitialData();
    const interval = setInterval(async () => {
      try {
        const [h, st, ts, dist, sim] = await Promise.all([
          fetchHealth().catch(() => null),
          fetchStats().catch(() => null),
          fetchTimeseriesAnalytics().catch(() => []),
          fetchDistributions().catch(() => null),
          fetchSimulatorStatus().catch(() => null)
        ]);
        if (h) setHealth(h);
        if (st) setStats(st);
        if (ts) setTimeseries(ts);
        if (dist) setDistributions(dist);
        if (sim) setSimStatus(sim);
      } catch (e) {
        // ignore
      }
    }, 4000);

    return () => clearInterval(interval);
  }, [loadInitialData]);

  // WebSocket Live Push Subscription
  useEffect(() => {
    const ws = new LiveStreamWebSocket(
      (event) => {
        if (event.type === 'transaction') {
          const newTx = event.data;
          setTransactions((prev) => {
            if (prev.some((t) => t.transaction_id === newTx.transaction_id)) return prev;
            return [newTx, ...prev].slice(0, 100);
          });
        } else if (event.type === 'alert') {
          const newAlert = event.data;
          setAlerts((prev) => {
            if (prev.some((a) => a.alert_id === newAlert.alert_id)) return prev;
            return [newAlert, ...prev].slice(0, 50);
          });
        } else if (event.type === 'kpi_update') {
          setStats((prev) => ({ ...prev, ...event.data }));
        }
      },
      (status) => setWsStatus(status)
    );

    ws.connect();
    return () => ws.disconnect();
  }, []);

  return (
    <div className="min-h-screen bg-[#F8FAFC] text-slate-900 flex flex-col font-sans">
      
      {/* Top Navbar with System Health & Monitoring Links */}
      <Navbar
        wsStatus={wsStatus}
        health={health}
        activeMode={activeMode}
        onOpenTelemetry={(tab) => setTelemetryState({ isOpen: true, tab })}
      />

      {/* Main Container */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        
        {/* Top KPI Metric Cards */}
        <KpiCards stats={stats} />

        {/* Real-time Simulator Controls, Speed Slider & Model Mode Dropdown */}
        <SimulatorControl
          simStatus={simStatus}
          onStatusRefresh={loadInitialData}
          onModelModeChange={(m) => setActiveMode(m)}
        />

        {/* Tab Navigation */}
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-200 pb-2">
          <button
            type="button"
            onClick={() => setActiveTab('live')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === 'live'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Live Operations (SOC Feed)</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('analytics')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === 'analytics'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <BarChart3 className="w-4 h-4" />
            <span>Fraud Analytics & Trends</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('model')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === 'model'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <BrainCircuit className="w-4 h-4" />
            <span>Feature Diagnostics</span>
          </button>

          <button
            type="button"
            onClick={() => setActiveTab('comparison')}
            className={`flex items-center space-x-2 px-3.5 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              activeTab === 'comparison'
                ? 'bg-blue-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Model Comparison (4 Architectures)</span>
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'live' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left 2 Cols: Live Streaming Transaction Table */}
            <div className="lg:col-span-2">
              <LiveTransactionFeed
                transactions={transactions}
                onSelectTransaction={(tx) => setSelectedTx(tx)}
              />
            </div>

            {/* Right 1 Col: Active Fraud Alerts Panel */}
            <div className="lg:col-span-1">
              <AlertPanel
                alerts={alerts}
                onSelectAlert={(alt) => setSelectedTx(alt)}
                onStatusUpdated={loadInitialData}
              />
            </div>
          </div>
        )}

        {activeTab === 'analytics' && (
          <FraudAnalytics
            distributions={distributions}
            timeseries={timeseries}
          />
        )}

        {activeTab === 'model' && (
          <ModelDiagnostics modelInfo={modelInfo} />
        )}

        {activeTab === 'comparison' && (
          <ModelComparisonView />
        )}

      </main>

      {/* Transaction Details & Explainability Modal */}
      {selectedTx && (
        <TransactionModal
          transaction={selectedTx}
          onClose={() => setSelectedTx(null)}
        />
      )}

      {/* Telemetry & Monitoring Modal */}
      <TelemetryModal
        isOpen={telemetryState.isOpen}
        initialTab={telemetryState.tab}
        onClose={() => setTelemetryState({ isOpen: false, tab: 'prometheus' })}
      />

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-4 mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between text-xs text-slate-500 gap-2">
          <span>FraudShield Enterprise Risk Platform • PaySim ML Architecture v2.0.0</span>
          <span className="font-mono text-slate-400">Kafka ➔ Multi-Model ML + Behavioral Profiling ➔ DB ➔ React</span>
        </div>
      </footer>

    </div>
  );
}
