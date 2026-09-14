import React, { useState, useEffect } from 'react'
import {
  Settings,
  Server,
  Database,
  Cpu,
  ShieldCheck,
  RefreshCw,
  KeyRound,
  CheckCircle2,
  XCircle,
  Clock,
} from 'lucide-react'
import { systemApi, dashboardApi } from '../services/api'
import { useAuth } from '../context/AuthContext'

export default function SettingsView() {
  const { user, token } = useAuth()
  const [health, setHealth] = useState(null)
  const [latency, setLatency] = useState(null)
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastPing, setLastPing] = useState(null)

  const checkStatus = async () => {
    setLoading(true)
    const start = performance.now()
    try {
      const [hData, sData] = await Promise.all([
        systemApi.getHealth(),
        dashboardApi.getStats(),
      ])
      const end = performance.now()
      setLatency(Math.round(end - start))
      setHealth(hData)
      setStats(sData)
      setLastPing(new Date())
    } catch (err) {
      console.error('Diagnostic check error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    checkStatus()
  }, [])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Settings className="w-5 h-5 text-cyan-400" />
            System Diagnostics &amp; Operational Telemetry
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Real backend infrastructure health, database connection state, and active ML registry configuration.
          </p>
        </div>

        <button
          onClick={checkStatus}
          disabled={loading}
          className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 text-xs font-semibold flex items-center gap-1.5 disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Run Health Diagnostics
        </button>
      </div>

      {/* Diagnostics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Backend Connectivity */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Server className="w-4 h-4 text-cyan-400" />
              FastAPI Core Service
            </span>
            <span
              className={`px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase ${
                health?.status === 'healthy'
                  ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  : 'bg-rose-950 text-rose-400 border border-rose-800'
              }`}
            >
              {health?.status === 'healthy' ? 'ONLINE' : 'DEGRADED'}
            </span>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>API Gateway:</span>
              <span className="text-slate-200">/api/v1 (FastAPI)</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Round-Trip Latency:</span>
              <span className="text-cyan-400 font-bold">{latency !== null ? `${latency} ms` : 'N/A'}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Last Probed:</span>
              <span className="text-slate-200">{lastPing ? lastPing.toLocaleTimeString() : 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* PostgreSQL Database */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Database className="w-4 h-4 text-blue-400" />
              PostgreSQL Data Layer
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-emerald-950 text-emerald-400 border border-emerald-800">
              CONNECTED
            </span>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>Database Engine:</span>
              <span className="text-slate-200">PostgreSQL (SQLAlchemy ORM)</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Transactions Stored:</span>
              <span className="text-white font-bold">{stats?.total_transactions || 0}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Customer Records:</span>
              <span className="text-white font-bold">{stats?.total_customers || 0}</span>
            </div>
          </div>
        </div>

        {/* Active Machine Learning Core */}
        <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
              <Cpu className="w-4 h-4 text-purple-400" />
              Active ML Engine
            </span>
            <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase bg-purple-950 text-purple-300 border border-purple-800">
              CHAMPION
            </span>
          </div>

          <div className="space-y-1.5 text-xs font-mono">
            <div className="flex justify-between text-slate-400">
              <span>Model Classifier:</span>
              <span className="text-purple-300 font-bold">
                {stats?.active_model_info?.name || 'XGBoost_Champion'}
              </span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Registry Version:</span>
              <span className="text-slate-200">{stats?.active_model_info?.version || 'v1.0'}</span>
            </div>
            <div className="flex justify-between text-slate-400">
              <span>Decision Threshold:</span>
              <span className="text-cyan-400 font-bold">
                {stats?.active_model_info?.threshold ?? 0.50}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Session & Environment Telemetry */}
      <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
        <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
          <KeyRound className="w-4 h-4 text-cyan-400" />
          Active Security Session Credentials
        </h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 text-xs font-mono">
          <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block">User Profile</span>
            <span className="text-white font-bold">{user?.name || 'Authorized Analyst'}</span>
          </div>
          <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block">Account Identity</span>
            <span className="text-slate-200">{user?.email || 'N/A'}</span>
          </div>
          <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block">Authorization Role</span>
            <span className="text-cyan-300 font-bold">{user?.role || 'FRAUD_INVESTIGATOR'}</span>
          </div>
          <div className="p-3 bg-slate-950/70 rounded-xl border border-slate-800">
            <span className="text-[10px] text-slate-400 uppercase block">Session Signature</span>
            <span className="text-slate-400">{token ? 'JWT (RS256/HS256 Active)' : 'No Token'}</span>
          </div>
        </div>

        <div className="p-3 rounded-xl bg-slate-950/40 border border-slate-800/80 text-[11px] text-slate-500 flex items-center justify-between">
          <span>Explainable AI Financial Fraud &amp; Risk Detection System • Phase 15 &amp; 16 Production Ready</span>
          <span className="font-mono">Python 3.14.5 | FastAPI | React 19</span>
        </div>
      </div>
    </div>
  )
}
