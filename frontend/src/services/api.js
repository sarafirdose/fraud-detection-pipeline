import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || (
  window.location.protocol === 'https:'
    ? `wss://${window.location.hostname}:8000/ws/live`
    : `ws://${window.location.hostname}:8000/ws/live`
);

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// REST API Endpoints
export const fetchHealth = async () => (await api.get('/api/health')).data;
export const fetchStats = async () => (await api.get('/api/stats')).data;
export const fetchRecentTransactions = async (limit = 30) => (await api.get(`/api/transactions/recent?limit=${limit}`)).data;
export const fetchTransactions = async (params = {}) => (await api.get('/api/transactions', { params })).data;
export const fetchRecentAlerts = async (limit = 15) => (await api.get(`/api/fraud-alerts/recent?limit=${limit}`)).data;
export const fetchAlerts = async (params = {}) => (await api.get('/api/fraud-alerts', { params })).data;
export const updateAlertStatus = async (alertId, status) => (await api.patch(`/api/fraud-alerts/${alertId}/status`, { status })).data;
export const fetchTimeseriesAnalytics = async () => (await api.get('/api/analytics/timeseries')).data;
export const fetchDistributions = async () => (await api.get('/api/analytics/distributions')).data;
export const fetchModelInfo = async () => (await api.get('/api/model-info')).data;
export const fetchModelMode = async () => (await api.get('/api/model-mode')).data;
export const updateModelMode = async (mode) => (await api.post('/api/model-mode', { mode })).data;
export const fetchModelComparison = async () => (await api.get('/api/model-comparison')).data;
export const fetchSimulatorStatus = async () => (await api.get('/api/simulator/status')).data;

export const controlSimulator = async (action, options = {}) => {
  return (await api.post('/api/simulator/control', {
    action,
    rate: options.rate,
    fraud_type: options.fraud_type,
    amount: options.amount,
    drain_account: options.drain_account
  })).data;
};

export const injectDemoFraud = async (fraudType = 'TRANSFER', amount = 650000.0, drainAccount = true) => {
  return (await api.post('/api/simulator/inject-fraud', null, {
    params: {
      tx_type: fraudType,
      amount,
      drain_account: drainAccount
    }
  })).data;
};

// WebSocket Service with Auto-Reconnect
export class LiveStreamWebSocket {
  constructor(onEvent, onStatusChange) {
    this.onEvent = onEvent;
    this.onStatusChange = onStatusChange;
    this.ws = null;
    this.reconnectTimer = null;
    this.pingInterval = null;
    this.isExplicitlyClosed = false;
  }

  connect() {
    this.isExplicitlyClosed = false;
    try {
      this.onStatusChange?.('connecting');
      this.ws = new WebSocket(WS_BASE_URL);

      this.ws.onopen = () => {
        this.onStatusChange?.('connected');
        // Start ping heartbeat
        this.pingInterval = setInterval(() => {
          if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send('ping');
          }
        }, 15000);
      };

      this.ws.onmessage = (event) => {
        try {
          const parsed = JSON.parse(event.data);
          this.onEvent?.(parsed);
        } catch (e) {
          // Non-JSON message
        }
      };

      this.ws.onerror = () => {
        this.onStatusChange?.('error');
      };

      this.ws.onclose = () => {
        clearInterval(this.pingInterval);
        this.onStatusChange?.('disconnected');
        if (!this.isExplicitlyClosed) {
          this.reconnectTimer = setTimeout(() => this.connect(), 2500);
        }
      };
    } catch (err) {
      this.onStatusChange?.('disconnected');
      this.reconnectTimer = setTimeout(() => this.connect(), 3000);
    }
  }

  disconnect() {
    this.isExplicitlyClosed = true;
    clearInterval(this.pingInterval);
    clearTimeout(this.reconnectTimer);
    if (this.ws) {
      this.ws.close();
    }
  }
}
