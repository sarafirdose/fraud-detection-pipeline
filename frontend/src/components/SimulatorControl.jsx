import React, { useState, useEffect } from 'react';
import { Play, Pause, Square, Zap, Sliders, AlertOctagon, CheckCircle2, Cpu } from 'lucide-react';
import { controlSimulator, injectDemoFraud, fetchModelMode, updateModelMode } from '../services/api';

export default function SimulatorControl({ simStatus, onStatusRefresh, onModelModeChange }) {
  const [speed, setSpeed] = useState(5);
  const [fraudType, setFraudType] = useState('TRANSFER');
  const [fraudAmount, setFraudAmount] = useState(750000);
  const [isInjecting, setIsInjecting] = useState(false);
  const [notification, setNotification] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [modelMode, setModelMode] = useState('SUPERVISED_XGBOOST');

  useEffect(() => {
    if (simStatus) {
      if (simStatus.rate && !isPaused) setSpeed(simStatus.rate);
      setIsRunning(!!simStatus.running);
      setIsPaused(!!simStatus.paused);
    }
  }, [simStatus]);

  useEffect(() => {
    fetchModelMode()
      .then(res => {
        if (res?.active_mode) {
          setModelMode(res.active_mode);
          onModelModeChange?.(res.active_mode);
        }
      })
      .catch(() => {});
  }, []);

  const showToast = (msg, type = 'success') => {
    setNotification({ msg, type });
    setTimeout(() => setNotification(null), 4000);
  };

  const handleAction = async (action) => {
    try {
      if (action === 'start') {
        setIsRunning(true);
        setIsPaused(false);
      } else if (action === 'pause') {
        setIsPaused(true);
      } else if (action === 'resume') {
        setIsPaused(false);
      } else if (action === 'stop') {
        setIsRunning(false);
        setIsPaused(false);
      }

      const res = await controlSimulator(action, { rate: speed });
      showToast(`Simulator: ${res.message || action.toUpperCase()}`);
      onStatusRefresh?.();
    } catch (e) {
      showToast(`Action failed: ${e.message}`, 'error');
    }
  };

  const handleSpeedChange = async (newSpeed) => {
    const val = parseFloat(newSpeed);
    setSpeed(val);
    try {
      await controlSimulator('set_rate', { rate: val });
    } catch (e) {
      // Ignore transient slider errors
    }
  };

  const handleModelModeChange = async (newMode) => {
    try {
      await updateModelMode(newMode);
      setModelMode(newMode);
      onModelModeChange?.(newMode);
      showToast(`Scoring Engine switched to: ${newMode}`);
    } catch (e) {
      showToast(`Mode switch failed: ${e.message}`, 'error');
    }
  };

  const handleInjectDemo = async () => {
    setIsInjecting(true);
    try {
      const res = await injectDemoFraud(fraudType, fraudAmount, true);
      showToast(`🚨 DEMO FRAUD sent: ${res.transaction?.transaction_id || 'DEMO-TX'} ($${fraudAmount.toLocaleString()})`, 'alert');
      onStatusRefresh?.();
    } catch (e) {
      showToast(`Fraud injection failed: ${e.message}`, 'error');
    } finally {
      setIsInjecting(false);
    }
  };

  return (
    <div className="enterprise-card p-4 relative">
      
      {/* Toast banner */}
      {notification && (
        <div className={`absolute -top-12 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded-lg text-xs font-semibold shadow-md border flex items-center space-x-2 z-50 animate-bounce ${
          notification.type === 'alert'
            ? 'bg-rose-50 text-rose-800 border-rose-200'
            : notification.type === 'error'
            ? 'bg-red-50 text-red-800 border-red-200'
            : 'bg-emerald-50 text-emerald-800 border-emerald-200'
        }`}>
          {notification.type === 'alert' ? <AlertOctagon className="w-4 h-4 text-rose-600" /> : <CheckCircle2 className="w-4 h-4 text-emerald-600" />}
          <span>{notification.msg}</span>
        </div>
      )}

      <div className="flex flex-col lg:flex-row items-center justify-between gap-4">
        
        {/* Left: Stream Control State */}
        <div className="flex items-center space-x-3 w-full lg:w-auto">
          <div className="p-2.5 rounded-lg bg-slate-100 text-slate-700 border border-slate-200">
            <Sliders className="w-4 h-4 text-slate-600" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="text-sm font-bold text-slate-900">Stream Controller</span>
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md ${
                isRunning && !isPaused
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : isPaused
                  ? 'bg-amber-50 text-amber-700 border border-amber-200'
                  : 'bg-slate-100 text-slate-600 border border-slate-200'
              }`}>
                {isRunning ? (isPaused ? 'PAUSED' : 'STREAMING') : 'IDLE'}
              </span>
            </div>
            <p className="text-xs text-slate-500">Kafka Ingestion → Feature Profiler → ML Engine</p>
          </div>
        </div>

        {/* Center: Play/Pause/Stop, Speed Slider, and Model Mode Selector */}
        <div className="flex flex-wrap items-center gap-3 w-full lg:w-auto justify-center">
          
          {/* Action Buttons */}
          <div className="flex items-center space-x-1.5 bg-slate-50 p-1 rounded-lg border border-slate-200">
            {!isRunning || isPaused ? (
              <button
                type="button"
                onClick={() => handleAction(isRunning ? 'resume' : 'start')}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                <span>{isRunning ? 'Resume' : 'Start'}</span>
              </button>
            ) : (
              <button
                type="button"
                onClick={() => handleAction('pause')}
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded-md bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold shadow-xs transition-colors cursor-pointer"
              >
                <Pause className="w-3.5 h-3.5" />
                <span>Pause</span>
              </button>
            )}

            {isRunning && (
              <button
                type="button"
                onClick={() => handleAction('stop')}
                className="flex items-center space-x-1 px-2.5 py-1.5 rounded-md bg-white hover:bg-slate-100 border border-slate-200 text-slate-700 text-xs font-semibold transition-colors cursor-pointer"
              >
                <Square className="w-3 h-3 fill-current" />
                <span>Stop</span>
              </button>
            )}
          </div>

          {/* Speed Slider */}
          <div className="flex items-center space-x-2 bg-slate-50 px-3 py-1.5 rounded-lg border border-slate-200">
            <span className="text-xs text-slate-500 font-medium whitespace-nowrap">Speed:</span>
            <input
              type="range"
              min="1"
              max="40"
              step="1"
              value={speed}
              onChange={(e) => handleSpeedChange(e.target.value)}
              className="w-20 sm:w-28 h-1.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
            <span className="text-xs font-mono font-bold text-blue-700 w-12 text-right">{speed} TPS</span>
          </div>

          {/* Model Architecture Selector Dropdown */}
          <div className="flex items-center space-x-1.5 bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200">
            <Cpu className="w-3.5 h-3.5 text-slate-500" />
            <select
              value={modelMode}
              onChange={(e) => handleModelModeChange(e.target.value)}
              className="bg-transparent text-slate-800 text-xs font-medium focus:outline-none cursor-pointer"
            >
              <option value="SUPERVISED_XGBOOST">XGBoost (Supervised)</option>
              <option value="SUPERVISED_RANDOM_FOREST">Random Forest (Supervised)</option>
              <option value="UNSUPERVISED_ISOLATION_FOREST">Isolation Forest (Anomaly)</option>
              <option value="UNSUPERVISED_AUTOENCODER">Autoencoder (Reconstruction)</option>
              <option value="ENSEMBLE">★ Hybrid Ensemble Mode</option>
            </select>
          </div>

        </div>

        {/* Right: Inject Demo Fraud Button & Config */}
        <div className="flex items-center space-x-2 w-full lg:w-auto justify-end border-t lg:border-t-0 border-slate-200 pt-3 lg:pt-0">
          
          <select
            value={fraudType}
            onChange={(e) => setFraudType(e.target.value)}
            className="bg-white border border-slate-200 text-slate-800 text-xs rounded-lg px-2.5 py-1.5 focus:outline-none focus:border-blue-500 font-mono shadow-xs"
          >
            <option value="TRANSFER">TRANSFER (Account Drain)</option>
            <option value="CASH_OUT">CASH_OUT (Sweep Funds)</option>
          </select>

          <button
            type="button"
            onClick={handleInjectDemo}
            disabled={isInjecting}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-700 text-white text-xs font-semibold shadow-xs transition-colors disabled:opacity-50 cursor-pointer"
          >
            <Zap className={`w-3.5 h-3.5 ${isInjecting ? 'animate-spin' : ''}`} />
            <span>Inject Demo Fraud</span>
          </button>

        </div>

      </div>
    </div>
  );
}
