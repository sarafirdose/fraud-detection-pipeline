import React from 'react';
import { ArrowUpRight, ShieldAlert, CheckCircle, Clock, DollarSign, Activity, AlertTriangle, Cpu } from 'lucide-react';

export default function KpiCards({ stats }) {
  const totalTx = stats?.total_transactions || 0;
  const fraudAlerts = stats?.fraud_alerts || 0;
  const fraudRate = stats?.fraud_rate_pct || 0;
  const highCritical = stats?.high_critical_alerts || 0;
  const avgLatency = stats?.avg_latency_ms || 0;
  const totalAmount = stats?.total_amount_processed || 0;
  const fraudAmount = stats?.fraud_amount_detected || 0;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      
      {/* 1. Total Transactions */}
      <div className="enterprise-card p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Total Transactions</span>
            <div className="p-1.5 rounded-md bg-blue-50 text-blue-600">
              <Activity className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono tracking-tight">
            {totalTx.toLocaleString()}
          </div>
        </div>
        <div className="mt-2 text-xs text-slate-500 truncate">
          ${totalAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} processed
        </div>
      </div>

      {/* 2. Fraud Alerts Detected */}
      <div className="enterprise-card p-4 flex flex-col justify-between border-l-4 border-l-rose-500">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Fraud Alerts</span>
            <div className="p-1.5 rounded-md bg-rose-50 text-rose-600">
              <ShieldAlert className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-rose-600 font-mono tracking-tight">
            {fraudAlerts.toLocaleString()}
          </div>
        </div>
        <div className="mt-2 text-xs text-rose-700 truncate font-medium">
          ${fraudAmount.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} intercepted
        </div>
      </div>

      {/* 3. Fraud Rate % */}
      <div className="enterprise-card p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Fraud Rate</span>
            <div className="p-1.5 rounded-md bg-emerald-50 text-emerald-600">
              <CheckCircle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono tracking-tight">
            {fraudRate.toFixed(2)}%
          </div>
        </div>
        <div className="mt-2 text-xs text-slate-500 truncate">
          {(totalTx - fraudAlerts).toLocaleString()} normal transactions
        </div>
      </div>

      {/* 4. High & Critical Alerts */}
      <div className="enterprise-card p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">High / Critical</span>
            <div className="p-1.5 rounded-md bg-amber-50 text-amber-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono tracking-tight">
            {highCritical.toLocaleString()}
          </div>
        </div>
        <div className="mt-2 text-xs text-amber-700 truncate font-medium">
          Requiring immediate analyst review
        </div>
      </div>

      {/* 5. Average Latency */}
      <div className="enterprise-card p-4 flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">Avg Latency</span>
            <div className="p-1.5 rounded-md bg-indigo-50 text-indigo-600">
              <Clock className="w-4 h-4" />
            </div>
          </div>
          <div className="text-2xl font-bold text-slate-900 font-mono tracking-tight">
            {avgLatency.toFixed(1)} <span className="text-sm font-sans text-slate-500 font-normal">ms</span>
          </div>
        </div>
        <div className="mt-2 text-xs text-slate-500 truncate">
          Model inference + stream pipeline
        </div>
      </div>

    </div>
  );
}
