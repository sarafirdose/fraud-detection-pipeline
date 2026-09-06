import React from 'react';
import { X, ShieldAlert, AlertOctagon, CheckCircle2, ArrowRight, DollarSign, Clock, Cpu, UserCheck, Activity } from 'lucide-react';

export default function TransactionModal({ transaction, onClose }) {
  if (!transaction) return null;

  const isFraud = transaction.is_fraud;
  const isCritical = transaction.risk_level === 'CRITICAL';
  const isHigh = transaction.risk_level === 'HIGH';

  const origError = (Number(transaction.newbalanceOrig || 0) + Number(transaction.amount || 0) - Number(transaction.oldbalanceOrg || 0));
  const destError = (Number(transaction.oldbalanceDest || 0) + Number(transaction.amount || 0) - Number(transaction.newbalanceDest || 0));

  const beh = transaction.behavioral_profile || {};

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full shadow-xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="p-5 border-b border-slate-200 flex items-center justify-between bg-slate-50">
          <div className="flex items-center space-x-3">
            <div className={`p-2.5 rounded-xl ${
              isCritical ? 'bg-rose-50 text-rose-600 border border-rose-200' : 'bg-blue-50 text-blue-600 border border-blue-200'
            }`}>
              {isFraud ? <AlertOctagon className="w-5 h-5" /> : <ShieldAlert className="w-5 h-5" />}
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-base font-bold text-slate-900 font-mono">{transaction.transaction_id}</h3>
                {transaction.is_demo && (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-indigo-50 text-indigo-700 border border-indigo-200">
                    DEMO TRANSACTION
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500">Forensic Ledger & Multi-Layer Feature Diagnostics</p>
            </div>
          </div>

          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg bg-white hover:bg-slate-100 border border-slate-200 text-slate-500 hover:text-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-6 overflow-y-auto space-y-5">
          
          {/* Top Risk & Verdict Banner */}
          <div className={`p-4 rounded-xl border flex items-center justify-between ${
            isCritical
              ? 'bg-rose-50/70 border-rose-200'
              : isHigh
              ? 'bg-amber-50/70 border-amber-200'
              : 'bg-emerald-50/60 border-emerald-200'
          }`}>
            <div>
              <span className="text-[11px] uppercase font-bold tracking-wider text-slate-500">Unified Risk Assessment</span>
              <div className="flex items-center space-x-2 mt-0.5">
                <span className={`text-xl font-bold ${
                  isCritical ? 'text-rose-700' : isHigh ? 'text-amber-700' : 'text-emerald-700'
                }`}>
                  {transaction.risk_level} RISK ({transaction.risk_score || transaction.final_risk_score}%)
                </span>
              </div>
              <p className="text-xs text-slate-600 mt-0.5">
                Evaluated by: <span className="font-semibold text-slate-900">{transaction.model_used || 'XGBoost'}</span>
              </p>
            </div>

            <div className="text-right font-mono">
              <span className="text-[11px] uppercase text-slate-500">Transfer Amount</span>
              <div className="text-xl font-bold text-slate-900">
                ${Number(transaction.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </div>
            </div>
          </div>

          {/* Multi-Layer Score Breakdown */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Supervised Probability</span>
              <p className="text-sm font-bold text-blue-700 mt-1">
                {transaction.fraud_probability ? (transaction.fraud_probability * 100).toFixed(1) : 0}%
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Anomaly Score</span>
              <p className="text-sm font-bold text-purple-700 mt-1">
                {transaction.anomaly_score !== undefined ? transaction.anomaly_score : 0}%
              </p>
            </div>
            <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-center">
              <span className="text-[10px] text-slate-500 uppercase font-semibold">Behavioral Risk</span>
              <p className="text-sm font-bold text-amber-700 mt-1">
                {transaction.behavioral_risk !== undefined ? transaction.behavioral_risk : 0}%
              </p>
            </div>
          </div>

          {/* Stateful User Behavioral Profiling Box */}
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <UserCheck className="w-4 h-4 text-emerald-600" />
              <span>Real-Time User Behavioral Profile ({transaction.nameOrigMasked})</span>
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs font-mono">
              <div className="p-2 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-sans">1h Velocity:</span>
                <p className="font-bold text-slate-900">{beh.velocity_1h || 1} tx/hr</p>
              </div>
              <div className="p-2 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-sans">24h Velocity:</span>
                <p className="font-bold text-slate-900">{beh.velocity_24h || 1} tx/day</p>
              </div>
              <div className="p-2 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-sans">Hist. Avg:</span>
                <p className="font-bold text-slate-900">${beh.avg_amount?.toLocaleString() || Number(transaction.amount).toLocaleString()}</p>
              </div>
              <div className="p-2 bg-white rounded-lg border border-slate-200">
                <span className="text-[10px] text-slate-500 font-sans">Deviation:</span>
                <p className={`font-bold ${beh.amount_deviation_ratio >= 3 ? 'text-rose-600' : 'text-emerald-700'}`}>
                  {beh.amount_deviation_ratio ? `${beh.amount_deviation_ratio}x` : '1.0x'}
                </p>
              </div>
            </div>
          </div>

          {/* Explainability Risk Factors */}
          <div>
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
              <Activity className="w-4 h-4 text-rose-600" />
              <span>Identified Risk & Explainability Factors</span>
            </h4>
            <div className="space-y-1.5">
              {(transaction.explanation || transaction.risk_factors) && (transaction.explanation || transaction.risk_factors).length > 0 ? (
                (transaction.explanation || transaction.risk_factors).map((factor, idx) => (
                  <div key={idx} className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 flex items-start space-x-2 text-xs text-slate-700">
                    <span className="text-rose-600 font-bold mt-0.5">•</span>
                    <span>{factor}</span>
                  </div>
                ))
              ) : (
                <div className="p-2.5 rounded-lg bg-slate-50 border border-slate-200 text-xs text-slate-500">
                  Standard transaction pattern within statistical bounds.
                </div>
              )}
            </div>
          </div>

          {/* Double-Entry Ledger Analysis */}
          <div>
            <h4 className="text-xs font-bold text-slate-800 uppercase tracking-wider mb-2">
              PaySim Double-Entry Ledger Analysis
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
              
              {/* Origin Account */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <div className="text-slate-800 font-bold mb-2 font-sans">Origin Account ({transaction.nameOrigMasked})</div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-sans">Initial Balance:</span>
                    <span className="text-slate-800">${Number(transaction.oldbalanceOrg || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-rose-600 font-semibold">
                    <span className="font-sans">Amount Sent:</span>
                    <span>-${Number(transaction.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between border-t border-slate-200 pt-1 font-bold">
                    <span className="text-slate-700 font-sans">Final Balance:</span>
                    <span className="text-emerald-700">${Number(transaction.newbalanceOrig || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>

              {/* Destination Account */}
              <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200">
                <div className="text-slate-800 font-bold mb-2 font-sans">Destination Account ({transaction.nameDestMasked})</div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <span className="text-slate-500 font-sans">Initial Balance:</span>
                    <span className="text-slate-800">${Number(transaction.oldbalanceDest || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between text-emerald-600 font-semibold">
                    <span className="font-sans">Amount Received:</span>
                    <span>+${Number(transaction.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  </div>
                  <div className="flex justify-between border-t border-slate-200 pt-1 font-bold">
                    <span className="text-slate-700 font-sans">Final Balance:</span>
                    <span className="text-emerald-700">${Number(transaction.newbalanceDest || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</span>
                  </div>
                </div>
              </div>

            </div>
          </div>

        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-slate-200 bg-slate-50 flex justify-end">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-900 text-white text-xs font-semibold transition-colors cursor-pointer"
          >
            Close Investigation
          </button>
        </div>

      </div>
    </div>
  );
}
