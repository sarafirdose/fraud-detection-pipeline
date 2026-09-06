import React, { useState, useEffect } from 'react';
import { Cpu, CheckCircle2, Zap, BarChart2, ShieldAlert, Sparkles, Sliders } from 'lucide-react';
import { fetchModelComparison, fetchModelMode, updateModelMode } from '../services/api';

export default function ModelComparisonView() {
  const [comparison, setComparison] = useState(null);
  const [activeMode, setActiveMode] = useState('SUPERVISED_XGBOOST');
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState(null);

  const loadData = async () => {
    try {
      setLoading(true);
      const [compRes, modeRes] = await Promise.all([
        fetchModelComparison(),
        fetchModelMode()
      ]);
      setComparison(compRes);
      if (modeRes?.active_mode) {
        setActiveMode(modeRes.active_mode);
      }
    } catch (e) {
      console.error('Failed loading model comparison:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleSelectMode = async (modeKey) => {
    try {
      await updateModelMode(modeKey);
      setActiveMode(modeKey);
      setToast(`Switched active inference model to: ${modeKey}`);
      setTimeout(() => setToast(null), 3500);
    } catch (e) {
      setToast(`Error switching mode: ${e.message}`);
    }
  };

  if (loading) {
    return (
      <div className="enterprise-card p-12 flex items-center justify-center space-x-3 text-slate-500 text-xs">
        <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        <span>Loading 4-Model Benchmarks & Comparison...</span>
      </div>
    );
  }

  const models = comparison?.models || {};

  return (
    <div className="space-y-6">
      
      {/* Toast */}
      {toast && (
        <div className="p-3 bg-blue-50 border border-blue-200 text-blue-800 text-xs font-semibold rounded-lg shadow-sm flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4 text-blue-600" />
          <span>{toast}</span>
        </div>
      )}

      {/* Header Banner */}
      <div className="enterprise-card p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-blue-600" />
            <h2 className="text-base font-bold text-slate-900">Multi-Model Architecture Comparison</h2>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Evaluation matrix comparing Supervised Classifiers and Unsupervised Anomaly Detectors on {comparison?.total_test_samples?.toLocaleString()} holdout PaySim transactions.
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-500 font-medium">Active Scoring Model:</span>
          <span className="px-2.5 py-1 bg-blue-50 text-blue-700 border border-blue-200 rounded-md text-xs font-mono font-semibold">
            {activeMode}
          </span>
        </div>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {Object.entries(models).map(([key, m]) => {
          const isSelected = activeMode === key;
          return (
            <div
              key={key}
              className={`p-4 rounded-xl border transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-blue-50/50 border-blue-500 shadow-sm ring-1 ring-blue-500'
                  : 'bg-white border-slate-200 hover:border-slate-300'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className={`text-[10px] uppercase font-bold px-2 py-0.5 rounded ${
                    m.paradigm === 'Supervised'
                      ? 'bg-blue-50 text-blue-700 border border-blue-200'
                      : 'bg-purple-50 text-purple-700 border border-purple-200'
                  }`}>
                    {m.paradigm}
                  </span>
                  <span className="text-[11px] font-mono text-slate-500">{m.avg_latency_ms} ms</span>
                </div>

                <h3 className="text-sm font-bold text-slate-900 mb-1">{m.model_name}</h3>

                {/* Metric Bars */}
                <div className="space-y-2.5 my-3 text-xs">
                  <div>
                    <div className="flex justify-between text-slate-500 text-[11px] mb-0.5">
                      <span>Recall (Fraud Catch Rate)</span>
                      <span className="font-bold text-emerald-700">{(m.recall * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-600 rounded-full" style={{ width: `${m.recall * 100}%` }}></div>
                    </div>
                  </div>

                  <div>
                    <div className="flex justify-between text-slate-500 text-[11px] mb-0.5">
                      <span>Precision</span>
                      <span className="font-bold text-blue-700">{(m.precision * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full bg-blue-600 rounded-full" style={{ width: `${m.precision * 100}%` }}></div>
                    </div>
                  </div>

                  <div className="flex justify-between text-slate-500 text-[11px]">
                    <span>ROC-AUC:</span>
                    <span className="font-mono font-semibold text-slate-800">{m.roc_auc.toFixed(4)}</span>
                  </div>

                  <div className="flex justify-between text-slate-500 text-[11px]">
                    <span>False Positive Rate (FPR):</span>
                    <span className="font-mono font-semibold text-slate-800">{(m.fpr * 100).toFixed(2)}%</span>
                  </div>
                </div>
              </div>

              <button
                type="button"
                onClick={() => handleSelectMode(key)}
                className={`w-full py-1.5 px-3 rounded-lg text-xs font-semibold mt-3 transition-colors cursor-pointer ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                }`}
              >
                {isSelected ? '✓ Active Model' : 'Switch to this Model'}
              </button>
            </div>
          );
        })}
      </div>

      {/* Ensemble Card Banner */}
      <div className={`p-4 rounded-xl border transition-all ${
        activeMode === 'ENSEMBLE'
          ? 'bg-indigo-50/60 border-indigo-400 shadow-sm ring-1 ring-indigo-400'
          : 'bg-white border-slate-200'
      }`}>
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="p-2.5 bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-200">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h3 className="text-sm font-bold text-slate-900">Multi-Model Ensemble Mode (Hybrid Engine)</h3>
                <span className="px-2 py-0.5 text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 rounded-md">
                  Supervised + Unsupervised + Behavioral
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                Combines XGBoost probability (65%), Isolation Forest & Autoencoder Anomaly score (35%), and Real-Time Behavioral Profile (20%) into one unified score.
              </p>
            </div>
          </div>

          <button
            type="button"
            onClick={() => handleSelectMode('ENSEMBLE')}
            className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
              activeMode === 'ENSEMBLE'
                ? 'bg-indigo-600 text-white shadow-xs'
                : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
            }`}
          >
            {activeMode === 'ENSEMBLE' ? '✓ Ensemble Mode Active' : 'Activate Hybrid Ensemble'}
          </button>
        </div>
      </div>

      {/* Detailed Benchmark Matrix */}
      <div className="enterprise-card p-5">
        <h3 className="text-sm font-bold text-slate-900 mb-3 flex items-center space-x-2">
          <BarChart2 className="w-4 h-4 text-blue-600" />
          <span>Full Evaluation Matrix</span>
        </h3>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 bg-slate-50">
                <th className="py-2.5 px-3 font-semibold">Architecture</th>
                <th className="py-2.5 px-3 font-semibold">Paradigm</th>
                <th className="py-2.5 px-3 font-semibold text-right">Recall</th>
                <th className="py-2.5 px-3 font-semibold text-right">Precision</th>
                <th className="py-2.5 px-3 font-semibold text-right">F1-Score</th>
                <th className="py-2.5 px-3 font-semibold text-right">ROC-AUC</th>
                <th className="py-2.5 px-3 font-semibold text-right">FPR</th>
                <th className="py-2.5 px-3 font-semibold text-right">FNR</th>
                <th className="py-2.5 px-3 font-semibold text-right">Latency</th>
                <th className="py-2.5 px-3 font-semibold text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {Object.entries(models).map(([key, m]) => (
                <tr key={key} className={activeMode === key ? 'bg-blue-50/40' : 'hover:bg-slate-50'}>
                  <td className="py-2.5 px-3 font-bold text-slate-900">{m.model_name}</td>
                  <td className="py-2.5 px-3 text-slate-500">{m.paradigm}</td>
                  <td className="py-2.5 px-3 text-right text-emerald-700 font-bold">{(m.recall * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-right text-blue-700 font-bold">{(m.precision * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-right text-slate-800">{m.f1_score.toFixed(4)}</td>
                  <td className="py-2.5 px-3 text-right text-slate-800">{m.roc_auc.toFixed(4)}</td>
                  <td className="py-2.5 px-3 text-right text-amber-700">{(m.fpr * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-right text-rose-700">{(m.fnr * 100).toFixed(2)}%</td>
                  <td className="py-2.5 px-3 text-right text-slate-600">{m.avg_latency_ms} ms</td>
                  <td className="py-2.5 px-3 text-center">
                    <button
                      type="button"
                      onClick={() => handleSelectMode(key)}
                      className={`px-2.5 py-1 rounded text-[11px] font-sans font-semibold cursor-pointer ${
                        activeMode === key
                          ? 'bg-blue-600 text-white'
                          : 'bg-slate-100 hover:bg-slate-200 text-slate-700'
                      }`}
                    >
                      {activeMode === key ? 'Active' : 'Select'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

    </div>
  );
}
