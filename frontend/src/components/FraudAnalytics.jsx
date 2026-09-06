import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid
} from 'recharts';
import { BarChart3, PieChart as PieIcon, TrendingUp, Layers } from 'lucide-react';

const RISK_COLORS = {
  LOW: '#16A34A',
  MEDIUM: '#D97706',
  HIGH: '#EA580C',
  CRITICAL: '#DC2626'
};

export default function FraudAnalytics({ distributions, timeseries }) {
  const fraudVsNormal = distributions?.fraud_vs_normal || [
    { name: 'Normal', value: 100, color: '#16A34A' },
    { name: 'Fraud', value: 0, color: '#DC2626' }
  ];

  const riskDist = distributions?.risk_distribution || [];
  const typeDist = distributions?.type_distribution || [];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
      
      {/* Chart 1: Transaction Volume & Fraud Rate Over Time */}
      <div className="enterprise-card p-5 flex flex-col h-[330px]">
        <div className="flex items-center space-x-2 mb-3">
          <div className="p-1.5 rounded-md bg-blue-50 text-blue-600">
            <TrendingUp className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Stream Activity & Fraud Rate Over Time</h3>
            <p className="text-[11px] text-slate-500">Transaction throughput and flagged anomalies</p>
          </div>
        </div>

        <div className="flex-1 w-full min-h-0">
          {timeseries && timeseries.length > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timeseries} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorVolume" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#2563EB" stopOpacity={0.25}/>
                    <stop offset="95%" stopColor="#2563EB" stopOpacity={0}/>
                  </linearGradient>
                  <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#DC2626" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#DC2626" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis dataKey="timestamp" stroke="#94A3B8" fontSize={10} />
                <YAxis stroke="#94A3B8" fontSize={10} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
                />
                <Area type="monotone" dataKey="tx_count" name="Total Transactions" stroke="#2563EB" strokeWidth={2} fillOpacity={1} fill="url(#colorVolume)" />
                <Area type="monotone" dataKey="fraud_count" name="Fraud Alerts" stroke="#DC2626" strokeWidth={2} fillOpacity={1} fill="url(#colorFraud)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full flex items-center justify-center text-xs text-slate-400">
              Awaiting stream time-series telemetry...
            </div>
          )}
        </div>
      </div>

      {/* Chart 2: Fraud vs Normal Classification Ratio */}
      <div className="enterprise-card p-5 flex flex-col h-[330px]">
        <div className="flex items-center space-x-2 mb-3">
          <div className="p-1.5 rounded-md bg-emerald-50 text-emerald-600">
            <PieIcon className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Fraud vs. Normal Classification</h3>
            <p className="text-[11px] text-slate-500">Class balance representation across dataset</p>
          </div>
        </div>

        <div className="flex-1 w-full min-h-0 flex items-center">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={fraudVsNormal}
                cx="50%"
                cy="50%"
                innerRadius={55}
                outerRadius={80}
                paddingAngle={4}
                dataKey="value"
              >
                {fraudVsNormal.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color || (index === 0 ? '#16A34A' : '#DC2626')} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
              />
              <Legend
                formatter={(value, entry) => (
                  <span className="text-xs text-slate-700 font-medium">{value} ({entry.payload.value})</span>
                )}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 3: Risk Tier Distribution */}
      <div className="enterprise-card p-5 flex flex-col h-[330px]">
        <div className="flex items-center space-x-2 mb-3">
          <div className="p-1.5 rounded-md bg-amber-50 text-amber-600">
            <BarChart3 className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Risk Tier Distribution</h3>
            <p className="text-[11px] text-slate-500">Categorization by ML fraud probability thresholds</p>
          </div>
        </div>

        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={riskDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="name" stroke="#94A3B8" fontSize={10} />
              <YAxis stroke="#94A3B8" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
              />
              <Bar dataKey="value" name="Count" radius={[4, 4, 0, 0]}>
                {riskDist.map((entry, index) => (
                  <Cell key={`risk-cell-${index}`} fill={RISK_COLORS[entry.name] || '#2563EB'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Chart 4: Transaction Type Breakdown */}
      <div className="enterprise-card p-5 flex flex-col h-[330px]">
        <div className="flex items-center space-x-2 mb-3">
          <div className="p-1.5 rounded-md bg-indigo-50 text-indigo-600">
            <Layers className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Transaction Type Breakdown</h3>
            <p className="text-[11px] text-slate-500">Volume and fraud distribution by PaySim transaction type</p>
          </div>
        </div>

        <div className="flex-1 w-full min-h-0">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={typeDist} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
              <XAxis dataKey="name" stroke="#94A3B8" fontSize={10} />
              <YAxis stroke="#94A3B8" fontSize={10} />
              <Tooltip
                contentStyle={{ backgroundColor: '#FFFFFF', borderColor: '#E2E8F0', borderRadius: '8px', fontSize: '11px', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
              />
              <Legend />
              <Bar dataKey="value" name="Total Transactions" fill="#4F46E5" radius={[4, 4, 0, 0]} />
              <Bar dataKey="fraud_count" name="Fraud Detected" fill="#DC2626" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
}
