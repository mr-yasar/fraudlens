import React, { useState, useEffect, useCallback } from 'react'
import {
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  RefreshCw,
  Filter,
  Info,
  Shield,
  ShieldCheck,
} from 'lucide-react'
import { premiumApi } from '../../services/api'

export default function PremiumAlertCenter({ user }) {
  const [alerts, setAlerts] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionMsg, setActionMsg] = useState(null)
  const [selectedSeverity, setSelectedSeverity] = useState('')

  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true)
      const res = await premiumApi.getAlerts({ severity: selectedSeverity })
      setAlerts(res)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load security alerts.')
    } finally {
      setLoading(false)
    }
  }, [selectedSeverity])

  useEffect(() => {
    loadAlerts()
  }, [loadAlerts])

  const handleAcknowledge = async (alertId) => {
    try {
      const res = await premiumApi.acknowledgeAlert(alertId)
      setActionMsg(res.message || 'Alert acknowledged.')
      setTimeout(() => setActionMsg(null), 2500)
      loadAlerts()
    } catch (err) {
      setError(err.message || 'Failed to acknowledge alert.')
    }
  }

  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'INFO':
        return 'bg-cyan-950 text-cyan-300 border-cyan-700'
      case 'WARNING':
        return 'bg-amber-950 text-amber-300 border-amber-700'
      case 'HIGH':
        return 'bg-rose-950 text-rose-300 border-rose-700'
      case 'CRITICAL':
        return 'bg-purple-950 text-purple-200 border-purple-500 shadow-[0_0_15px_rgba(168,85,247,0.4)]'
      default:
        return 'bg-slate-900 text-slate-300 border-slate-700'
    }
  }

  return (
    <div className="space-y-6 animate-fade-in text-slate-100">
      {/* Header */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-white font-mono tracking-tight flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-amber-400" />
              SECURITY ALERT CENTER (SECTION 22 SPEC)
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-700 font-bold">
              REAL-TIME THREAT LOG
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Triaged security alerts categorized by INFO, WARNING, HIGH, and CRITICAL severities with instant verification resolution.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {/* Severity Filter */}
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 outline-none"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical Only</option>
            <option value="HIGH">High Only</option>
            <option value="WARNING">Warning Only</option>
            <option value="INFO">Info Only</option>
          </select>

          <button
            onClick={loadAlerts}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white flex items-center gap-2 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-amber-400' : ''}`} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3.5 rounded-2xl bg-emerald-950/80 border border-emerald-600 text-emerald-200 text-xs flex items-center gap-2 font-mono">
          <CheckCircle2 className="w-4 h-4 text-emerald-400" />
          <span>{actionMsg}</span>
        </div>
      )}

      {error && (
        <div className="p-3.5 rounded-2xl bg-rose-950/80 border border-rose-600 text-rose-200 text-xs flex items-center gap-2 font-mono">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Alerts Feed */}
      <div className="space-y-3">
        {alerts.length === 0 ? (
          <div className="p-12 rounded-3xl bg-slate-900/60 border border-slate-800 text-center text-xs font-mono text-slate-400">
            No security alerts matching criteria. All systems operating within baseline parameters.
          </div>
        ) : (
          alerts.map((al) => {
            const isResolved = al.status === 'RESOLVED' || al.status === 'ACKNOWLEDGED' || al.is_acknowledged

            return (
              <div
                key={al.id || al.alert_id}
                className={`p-5 rounded-3xl bg-slate-900/90 border-2 transition-all flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-lg ${
                  isResolved ? 'border-slate-800/80 opacity-75' : 'border-amber-500/50 shadow-[0_0_20px_rgba(245,158,11,0.15)]'
                }`}
              >
                <div className="space-y-1.5 max-w-2xl">
                  <div className="flex items-center gap-2.5">
                    <span className={`text-[9px] font-mono font-extrabold px-2 py-0.5 rounded border ${getSeverityBadge(al.severity)}`}>
                      {al.severity}
                    </span>
                    <h4 className="text-sm font-bold text-white font-mono">{al.title}</h4>
                    <span className="text-[10px] font-mono text-slate-500">
                      {al.created_at ? new Date(al.created_at).toLocaleString() : 'Recent'}
                    </span>
                  </div>

                  <p className="text-xs text-slate-300 leading-relaxed font-sans">
                    {al.message}
                  </p>

                  <div className="text-[10px] font-mono text-slate-500 flex items-center gap-2 pt-1">
                    <span>Alert ID: {al.alert_id}</span>
                    <span>•</span>
                    <span>Status: <strong className={isResolved ? 'text-emerald-400' : 'text-amber-400'}>{al.status}</strong></span>
                  </div>
                </div>

                <div className="flex items-center gap-2 self-end md:self-auto">
                  {!isResolved ? (
                    <button
                      type="button"
                      onClick={() => handleAcknowledge(al.id || al.alert_id)}
                      className="py-2 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 font-mono text-xs font-bold uppercase transition flex items-center gap-1.5"
                    >
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Acknowledge</span>
                    </button>
                  ) : (
                    <div className="text-xs font-mono text-emerald-400 flex items-center gap-1.5 bg-emerald-950/60 px-3 py-1.5 rounded-xl border border-emerald-800">
                      <ShieldCheck className="w-4 h-4" />
                      <span>Resolved</span>
                    </div>
                  )}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
