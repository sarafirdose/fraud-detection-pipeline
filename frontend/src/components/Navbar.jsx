import React from 'react';
import { ShieldCheck, Activity, Database, Cpu, Radio, BarChart3, LineChart } from 'lucide-react';

export default function Navbar({ wsStatus, health, activeMode, onOpenTelemetry }) {
  const isWsConnected = wsStatus === 'connected';

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-40 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        
        {/* Brand & Title */}
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-lg bg-blue-600 flex items-center justify-center shadow-xs">
            <ShieldCheck className="w-5 h-5 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-base text-slate-900 tracking-tight">FraudShield<span className="text-blue-600 font-semibold text-xs ml-1">Enterprise</span></span>
              <span className="text-[10px] font-semibold tracking-wider px-2 py-0.5 rounded-md bg-emerald-50 text-emerald-700 border border-emerald-200">
                SOC ACTIVE
              </span>
            </div>
            <p className="text-xs text-slate-500">Real-Time PaySim Financial Fraud & Risk Monitoring</p>
          </div>
        </div>

        {/* System Status Indicators & Telemetry Links */}
        <div className="hidden md:flex items-center space-x-2.5">
          
          {/* Active Model Badge */}
          {activeMode && (
            <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200 text-slate-700 text-xs font-mono">
              <Cpu className="w-3.5 h-3.5 text-slate-500" />
              <span className="font-medium text-[11px]">{activeMode.replace('SUPERVISED_', '').replace('UNSUPERVISED_', '')}</span>
            </div>
          )}

          {/* WebSocket Live Feed Status */}
          <div className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-slate-50 border border-slate-200 text-slate-700 text-xs">
            <span className={`w-2 h-2 rounded-full ${isWsConnected ? 'bg-emerald-500' : 'bg-amber-500'}`}></span>
            <span className="font-medium text-[11px] text-slate-600">Stream:</span>
            <span className={`font-semibold text-[11px] ${isWsConnected ? 'text-emerald-700' : 'text-amber-700'}`}>
              {isWsConnected ? 'Connected' : wsStatus}
            </span>
          </div>

          {/* Prometheus Metrics Link */}
          <button
            type="button"
            onClick={() => onOpenTelemetry?.('prometheus')}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-medium transition-colors cursor-pointer"
            title="Open Prometheus Metrics Telemetry Viewer"
          >
            <LineChart className="w-3.5 h-3.5 text-orange-600" />
            <span>Prometheus</span>
          </button>

          {/* Grafana Dashboard Link */}
          <button
            type="button"
            onClick={() => onOpenTelemetry?.('grafana')}
            className="flex items-center space-x-1.5 px-2.5 py-1 rounded-md bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-xs font-medium transition-colors cursor-pointer"
            title="Open Grafana SOC Monitoring Status"
          >
            <BarChart3 className="w-3.5 h-3.5 text-amber-600" />
            <span>Grafana</span>
          </button>

        </div>

      </div>
    </header>
  );
}
