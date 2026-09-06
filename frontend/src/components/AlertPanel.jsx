import React, { useState } from 'react';
import { AlertOctagon, CheckCircle2, Clock, ChevronRight, Eye, ShieldAlert } from 'lucide-react';
import { updateAlertStatus } from '../services/api';

export default function AlertPanel({ alerts = [], onSelectAlert, onStatusUpdated }) {
  const [updatingId, setUpdatingId] = useState(null);

  const handleStatusChange = async (alertId, newStatus) => {
    try {
      setUpdatingId(alertId);
      await updateAlertStatus(alertId, newStatus);
      onStatusUpdated?.();
    } catch (e) {
      console.error('Failed to update alert status:', e);
    } finally {
      setUpdatingId(null);
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'CONFIRMED':
        return 'bg-rose-50 text-rose-700 border-rose-200 font-semibold';
      case 'INVESTIGATING':
        return 'bg-amber-50 text-amber-700 border-amber-200 font-semibold';
      case 'DISMISSED':
        return 'bg-slate-100 text-slate-600 border-slate-200';
      default:
        return 'bg-blue-50 text-blue-700 border-blue-200 font-bold';
    }
  };

  return (
    <div className="enterprise-card flex flex-col h-[580px]">
      
      {/* Header */}
      <div className="p-4 border-b border-slate-200 flex items-center justify-between bg-white rounded-t-xl">
        <div className="flex items-center space-x-2">
          <ShieldAlert className="w-4 h-4 text-rose-600" />
          <h3 className="text-sm font-bold text-slate-900">Fraud Alert Queue</h3>
        </div>
        <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-rose-50 text-rose-700 border border-rose-200 font-bold">
          {alerts.length} Flagged
        </span>
      </div>

      {/* Alert Feed List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 bg-white">
        {alerts.length === 0 ? (
          <div className="py-16 text-center text-slate-400 text-xs">
            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto mb-2 opacity-80" />
            <p>No active fraud alerts in queue.</p>
            <p className="text-[11px] text-slate-400 mt-0.5">Stream is clean or demo fraud not yet triggered.</p>
          </div>
        ) : (
          alerts.map((alert) => {
            const isCritical = alert.risk_level === 'CRITICAL';
            return (
              <div
                key={alert.alert_id}
                className="p-3.5 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="flex items-center space-x-1.5">
                      <span className="font-mono text-xs font-bold text-slate-900">
                        ${Number(alert.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}
                      </span>
                      <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-slate-100 text-slate-600">
                        {alert.type}
                      </span>
                      {alert.is_demo && (
                        <span className="text-[9px] font-bold px-1.5 py-0.2 rounded bg-indigo-50 text-indigo-600 border border-indigo-200">
                          DEMO
                        </span>
                      )}
                    </div>
                    <div className="text-[11px] font-mono text-slate-500 mt-0.5">
                      {alert.nameOrigMasked} ➔ {alert.nameDestMasked}
                    </div>
                  </div>

                  <div className="text-right">
                    <span className={`inline-flex px-1.5 py-0.5 rounded text-[10px] font-semibold ${
                      isCritical ? 'bg-rose-50 text-rose-700 border border-rose-200' : 'bg-amber-50 text-amber-700 border border-amber-200'
                    }`}>
                      {alert.risk_score}% ({alert.risk_level})
                    </span>
                  </div>
                </div>

                {/* Primary Explainability Factor */}
                {alert.risk_factors && alert.risk_factors.length > 0 && (
                  <p className="text-[11px] text-rose-600 mt-1.5 line-clamp-1">
                    • {alert.risk_factors[0]}
                  </p>
                )}

                {/* Status Selector & Inspect Action */}
                <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-slate-100">
                  <select
                    value={alert.status || 'NEW'}
                    onChange={(e) => handleStatusChange(alert.alert_id, e.target.value)}
                    disabled={updatingId === alert.alert_id}
                    className={`text-[11px] rounded px-2 py-1 border focus:outline-none cursor-pointer ${getStatusBadge(alert.status)}`}
                  >
                    <option value="NEW">NEW</option>
                    <option value="INVESTIGATING">INVESTIGATING</option>
                    <option value="CONFIRMED">CONFIRMED</option>
                    <option value="DISMISSED">DISMISSED</option>
                  </select>

                  <button
                    type="button"
                    onClick={() => onSelectAlert(alert)}
                    className="flex items-center space-x-1 text-xs text-blue-600 hover:text-blue-800 font-medium cursor-pointer"
                  >
                    <span>Inspect</span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

    </div>
  );
}
