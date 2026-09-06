import React, { useState } from 'react';
import { Eye, ArrowUpDown, Filter, ShieldAlert, CheckCircle, Clock } from 'lucide-react';

export default function LiveTransactionFeed({ transactions = [], onSelectTransaction }) {
  const [filterType, setFilterType] = useState('ALL');
  const [onlyFraud, setOnlyFraud] = useState(false);

  const filtered = transactions.filter((tx) => {
    if (onlyFraud && !tx.is_fraud && tx.risk_level === 'LOW') return false;
    if (filterType !== 'ALL' && tx.type !== filterType) return false;
    return true;
  });

  const getRiskBadge = (level, score) => {
    switch (level) {
      case 'CRITICAL':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
            CRITICAL ({score}%)
          </span>
        );
      case 'HIGH':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-700 border border-amber-200">
            HIGH ({score}%)
          </span>
        );
      case 'MEDIUM':
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-50 text-amber-600 border border-amber-200">
            MED ({score}%)
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            LOW ({score}%)
          </span>
        );
    }
  };

  const getTypeBadge = (type) => {
    const colors = {
      TRANSFER: 'bg-indigo-50 text-indigo-700 border-indigo-200',
      CASH_OUT: 'bg-orange-50 text-orange-700 border-orange-200',
      PAYMENT: 'bg-blue-50 text-blue-700 border-blue-200',
      CASH_IN: 'bg-slate-50 text-slate-700 border-slate-200',
      DEBIT: 'bg-emerald-50 text-emerald-700 border-emerald-200'
    };
    return (
      <span className={`inline-flex px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${colors[type] || 'bg-slate-100 text-slate-700 border-slate-200'}`}>
        {type}
      </span>
    );
  };

  return (
    <div className="enterprise-card flex flex-col h-[580px]">
      
      {/* Header & Filter Toolbar */}
      <div className="p-4 border-b border-slate-200 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-white rounded-t-xl">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-bold text-slate-900">Live Transaction Stream</h3>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-600 border border-slate-200">
              {filtered.length} in buffer
            </span>
          </div>
          <p className="text-xs text-slate-500">Real-time Kafka ingestion and sub-millisecond scoring</p>
        </div>

        {/* Filter Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-white border border-slate-200 text-slate-700 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500 shadow-xs cursor-pointer"
          >
            <option value="ALL">All Types</option>
            <option value="TRANSFER">TRANSFER</option>
            <option value="CASH_OUT">CASH_OUT</option>
            <option value="PAYMENT">PAYMENT</option>
            <option value="CASH_IN">CASH_IN</option>
            <option value="DEBIT">DEBIT</option>
          </select>

          <button
            type="button"
            onClick={() => setOnlyFraud(!onlyFraud)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-colors cursor-pointer ${
              onlyFraud
                ? 'bg-rose-50 text-rose-700 border-rose-300 font-semibold'
                : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-50'
            }`}
          >
            {onlyFraud ? '✓ Suspicious Only' : 'Show All'}
          </button>
        </div>
      </div>

      {/* Transaction Table */}
      <div className="flex-1 overflow-y-auto">
        <table className="w-full text-left text-xs">
          <thead className="sticky top-0 bg-slate-50 text-slate-500 font-semibold border-b border-slate-200 z-10">
            <tr>
              <th className="py-2.5 px-3">Transaction ID</th>
              <th className="py-2.5 px-3">Type</th>
              <th className="py-2.5 px-3">Amount</th>
              <th className="py-2.5 px-3">Origin / Dest</th>
              <th className="py-2.5 px-3">Risk Assessment</th>
              <th className="py-2.5 px-3 text-right">Latency</th>
              <th className="py-2.5 px-3 text-center">Inspect</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {filtered.length === 0 ? (
              <tr>
                <td colSpan="7" className="py-12 text-center text-slate-400">
                  Waiting for incoming live transactions...
                </td>
              </tr>
            ) : (
              filtered.map((tx) => {
                const isFraud = tx.is_fraud;
                return (
                  <tr
                    key={tx.transaction_id}
                    className={`hover:bg-slate-50 transition-colors ${
                      isFraud ? 'bg-rose-50/40' : ''
                    }`}
                  >
                    <td className="py-2.5 px-3 font-mono font-medium text-slate-800">
                      <div className="flex items-center space-x-1.5">
                        {isFraud && <ShieldAlert className="w-3.5 h-3.5 text-rose-600 flex-shrink-0" />}
                        <span className="truncate max-w-[130px]">{tx.transaction_id}</span>
                      </div>
                    </td>

                    <td className="py-2.5 px-3">
                      {getTypeBadge(tx.type)}
                    </td>

                    <td className="py-2.5 px-3 font-mono font-semibold text-slate-900">
                      ${Number(tx.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>

                    <td className="py-2.5 px-3 font-mono text-[11px] text-slate-500">
                      <div>{tx.nameOrigMasked || 'C***'}</div>
                      <div className="text-slate-400">↳ {tx.nameDestMasked || 'C***'}</div>
                    </td>

                    <td className="py-2.5 px-3">
                      {getRiskBadge(tx.risk_level, tx.risk_score || tx.final_risk_score)}
                    </td>

                    <td className="py-2.5 px-3 font-mono text-[11px] text-right text-slate-500">
                      {tx.processing_latency_ms || 1.2} ms
                    </td>

                    <td className="py-2.5 px-3 text-center">
                      <button
                        type="button"
                        onClick={() => onSelectTransaction(tx)}
                        className="p-1 rounded-md text-slate-400 hover:text-blue-600 hover:bg-slate-100 transition-colors cursor-pointer"
                        title="Inspect Transaction"
                      >
                        <Eye className="w-4 h-4" />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

    </div>
  );
}
