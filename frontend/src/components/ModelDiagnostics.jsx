import React from 'react';
import { BrainCircuit, CheckCircle2, AlertCircle, BarChart2, Shield } from 'lucide-react';

export default function ModelDiagnostics({ modelInfo }) {
  if (!modelInfo) {
    return (
      <div className="enterprise-card p-8 text-center text-slate-400 text-xs">
        Loading Machine Learning Model Diagnostics...
      </div>
    );
  }

  const metrics = modelInfo.metrics || {};
  const cm = metrics.confusion_matrix || {
    true_negative: 0,
    false_positive: 0,
    false_negative: 0,
    true_positive: 0
  };

  const featImp = modelInfo.feature_importances || [];

  return (
    <div className="enterprise-card p-6 space-y-6">
      
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 border-b border-slate-200 pb-4">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-lg bg-indigo-50 text-indigo-600 border border-indigo-100">
            <BrainCircuit className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-slate-900 tracking-tight">{modelInfo.model_name || 'XGBoost Classifier'}</h3>
            <p className="text-xs text-slate-500">
              Dataset: {modelInfo.dataset_source} ({modelInfo.train_samples?.toLocaleString()} train / {modelInfo.test_samples?.toLocaleString()} test holdout samples)
            </p>
          </div>
        </div>

        <div className="text-right">
          <span className="text-[10px] uppercase font-semibold text-slate-400">Model Status</span>
          <div className="text-xs font-semibold text-emerald-700 flex items-center space-x-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
            <span>Calibrated & Active</span>
          </div>
        </div>
      </div>

      {/* Metric Score Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
          <span className="text-[10px] text-slate-500 uppercase font-semibold">Precision</span>
          <div className="text-lg font-bold font-mono text-slate-900 mt-1">
            {((metrics.precision || 0) * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-slate-400">Low False Positives</span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
          <span className="text-[10px] text-slate-500 uppercase font-semibold">Recall (Sensitivity)</span>
          <div className="text-lg font-bold font-mono text-emerald-700 mt-1">
            {((metrics.recall || 0) * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-slate-400">Low Missed Fraud</span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
          <span className="text-[10px] text-slate-500 uppercase font-semibold">F1-Score</span>
          <div className="text-lg font-bold font-mono text-slate-900 mt-1">
            {((metrics.f1_score || 0) * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-slate-400">Harmonic Balance</span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-center">
          <span className="text-[10px] text-slate-500 uppercase font-semibold">ROC-AUC</span>
          <div className="text-lg font-bold font-mono text-slate-900 mt-1">
            {((metrics.roc_auc || 0) * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-slate-400">Class Separability</span>
        </div>

        <div className="p-3.5 rounded-lg bg-slate-50 border border-slate-200 text-center col-span-2 sm:col-span-1">
          <span className="text-[10px] text-slate-500 uppercase font-semibold">PR-AUC</span>
          <div className="text-lg font-bold font-mono text-slate-900 mt-1">
            {((metrics.pr_auc || 0) * 100).toFixed(2)}%
          </div>
          <span className="text-[10px] text-slate-400">Imbalance Metric</span>
        </div>
      </div>

      {/* Confusion Matrix & Feature Importance Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Confusion Matrix */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 flex flex-col justify-between">
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-1">
              Confusion Matrix (Holdout Test Set)
            </h4>
            <p className="text-[11px] text-slate-500 mb-3">
              Evaluated on stratified holdout test split.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-2 text-center font-mono">
            {/* True Negative */}
            <div className="p-3 rounded-lg bg-white border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase block font-sans">True Negative (Normal)</span>
              <span className="text-lg font-bold text-slate-800">{cm.true_negative?.toLocaleString()}</span>
            </div>

            {/* False Positive */}
            <div className="p-3 rounded-lg bg-white border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase block font-sans">False Positive (False Alarm)</span>
              <span className="text-lg font-bold text-amber-700">{cm.false_positive?.toLocaleString()}</span>
            </div>

            {/* False Negative */}
            <div className="p-3 rounded-lg bg-white border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase block font-sans">False Negative (Missed Fraud)</span>
              <span className="text-lg font-bold text-rose-600">{cm.false_negative?.toLocaleString()}</span>
            </div>

            {/* True Positive */}
            <div className="p-3 rounded-lg bg-white border border-slate-200">
              <span className="text-[10px] text-slate-500 uppercase block font-sans">True Positive (Intercepted)</span>
              <span className="text-lg font-bold text-emerald-700">{cm.true_positive?.toLocaleString()}</span>
            </div>
          </div>
        </div>

        {/* Feature Importance Rankings */}
        <div className="p-4 rounded-xl bg-slate-50 border border-slate-200">
          <div className="flex items-center justify-between mb-1">
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Top Feature Importances
            </h4>
            <BarChart2 className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-[11px] text-slate-500 mb-3">Key predictive drivers learned during XGBoost tree splitting.</p>

          <div className="space-y-2.5 max-h-48 overflow-y-auto pr-1">
            {featImp.slice(0, 7).map((feat, idx) => (
              <div key={idx} className="space-y-1">
                <div className="flex justify-between text-xs font-mono">
                  <span className="text-slate-700">{feat.feature}</span>
                  <span className="text-indigo-700 font-semibold">{(feat.importance * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-full rounded-full"
                    style={{ width: `${Math.min(100, feat.importance * 200)}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

      </div>

    </div>
  );
}
