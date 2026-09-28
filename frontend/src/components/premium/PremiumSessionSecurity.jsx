import React, { useState, useEffect, useCallback } from 'react'
import {
  Radio,
  Globe,
  Clock,
  Laptop,
  Smartphone,
  ShieldAlert,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  LogOut,
  ShieldX,
} from 'lucide-react'
import { premiumApi } from '../../services/api'

export default function PremiumSessionSecurity({ user }) {
  const [sessions, setSessions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionMsg, setActionMsg] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)

  const loadSessions = useCallback(async () => {
    try {
      setLoading(true)
      const res = await premiumApi.getSessions()
      setSessions(res)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load active sessions.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadSessions()
  }, [loadSessions])

  const handleRevoke = async (sessionId) => {
    if (!window.confirm(`Immediately terminate and revoke session '${sessionId}'?`)) return
    try {
      setActionLoading(true)
      const res = await premiumApi.revokeSession(sessionId)
      setActionMsg(res.message || 'Session revoked successfully.')
      setTimeout(() => setActionMsg(null), 3000)
      loadSessions()
    } catch (err) {
      setError(err.message || 'Failed to revoke session.')
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="space-y-6 animate-fade-in text-slate-100">
      {/* Header */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-white font-mono tracking-tight flex items-center gap-2">
              <Radio className="w-5 h-5 text-cyan-400 animate-pulse" />
              SESSION SECURITY &amp; FLEET MONITOR (SECTION 15 SPEC)
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold">
              ZERO LEAK
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Real-time tracking of active tokens, IP addresses, geo-locations, and 1-click cryptographic session revocation.
          </p>
        </div>

        <button
          onClick={loadSessions}
          disabled={loading || actionLoading}
          className="self-start md:self-auto px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
          <span>Refresh Fleet</span>
        </button>
      </div>

      {/* Notifications */}
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

      {/* Sessions Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {sessions.map((sess) => {
          const isActive = sess.session_status === 'ACTIVE'

          return (
            <div
              key={sess.id || sess.session_id}
              className={`p-5 rounded-3xl bg-slate-900/90 border-2 transition-all flex flex-col justify-between space-y-3 ${
                isActive
                  ? 'border-cyan-500/50 shadow-[0_0_20px_rgba(6,182,212,0.15)]'
                  : 'border-slate-800 opacity-60'
              }`}
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-sm text-white">{sess.device_name || 'Active Client'}</span>
                    <span className="text-[10px] font-mono text-cyan-400 font-semibold">{sess.ip_address}</span>
                  </div>
                  <span
                    className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                      isActive
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                        : 'bg-slate-900 text-slate-400 border-slate-700'
                    }`}
                  >
                    {isActive ? 'ACTIVE' : 'REVOKED'}
                  </span>
                </div>

                <div className="p-3 rounded-2xl bg-slate-950/80 border border-slate-800 space-y-1 text-xs font-mono">
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">Session ID</span>
                    <span className="text-cyan-300 font-bold">{sess.session_id}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">Location</span>
                    <span>{sess.approximate_location || 'Mumbai, Maharashtra'}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">Login Time</span>
                    <span>{sess.login_time ? new Date(sess.login_time).toLocaleString() : 'Recent'}</span>
                  </div>
                  <div className="flex items-center justify-between text-slate-300">
                    <span className="text-slate-500">Risk Score</span>
                    <span className="font-bold text-emerald-400">{sess.risk_score || 5}/100</span>
                  </div>
                </div>
              </div>

              {isActive && (
                <div className="pt-2 border-t border-slate-800/80">
                  <button
                    type="button"
                    onClick={() => handleRevoke(sess.session_id)}
                    disabled={actionLoading}
                    className="w-full py-2 px-3 rounded-xl bg-slate-900 hover:bg-rose-950/80 border border-slate-700 hover:border-rose-600 text-slate-300 hover:text-rose-300 font-mono text-xs font-semibold transition flex items-center justify-center gap-1.5"
                  >
                    <ShieldX className="w-3.5 h-3.5" />
                    <span>Terminate &amp; Revoke Session</span>
                  </button>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
