import React, { useState, useEffect, useCallback } from 'react'
import {
  FileSpreadsheet,
  CheckCircle2,
  AlertTriangle,
  Clock,
  RefreshCw,
  Search,
  Lock,
  ShieldCheck,
  Filter,
} from 'lucide-react'
import { premiumApi } from '../../services/api'

export default function PremiumAuditTrail({ user }) {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [actionFilter, setActionFilter] = useState('')

  const loadLogs = useCallback(async () => {
    try {
      setLoading(true)
      const res = await premiumApi.getAuditTrail({ action: actionFilter, limit: 50 })
      setLogs(res.logs || [])
      setTotal(res.total || 0)
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load audit logs.')
    } finally {
      setLoading(false)
    }
  }, [actionFilter])

  useEffect(() => {
    loadLogs()
  }, [loadLogs])

  return (
    <div className="space-y-6 animate-fade-in text-slate-100">
      {/* Header */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-white font-mono tracking-tight flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-indigo-400" />
              IMMUTABLE COMPLIANCE AUDIT TRAIL (SECTION 23 SPEC)
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700 font-bold">
              TAMPER PROOF
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Complete cryptographic audit log capturing auth, transaction staging, risk evaluations, and step-up challenge verifications.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded-xl px-3 py-2 text-xs font-mono text-slate-200 outline-none"
          >
            <option value="">All Security Actions</option>
            <option value="VERIFICATION_SUCCESS">Verification Success</option>
            <option value="VERIFICATION_CHALLENGE_ISSUED">Challenges Issued</option>
            <option value="TRANSACTION_EVALUATION">Risk Evaluations</option>
            <option value="DEVICE_TRUST_UPDATED">Device Trust Changes</option>
            <option value="SESSION_REVOKED">Session Revocations</option>
          </select>

          <button
            onClick={loadLogs}
            disabled={loading}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white flex items-center gap-2 transition"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-indigo-400' : ''}`} />
            <span>Refresh Logs</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-2xl bg-rose-950/80 border border-rose-600 text-rose-200 text-xs flex items-center gap-2 font-mono">
          <AlertTriangle className="w-4 h-4 text-rose-400" />
          <span>{error}</span>
        </div>
      )}

      {/* Logs Table */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/60">
                <th className="p-3">TIMESTAMP</th>
                <th className="p-3">ACTION EVENT</th>
                <th className="p-3">RESOURCE TYPE</th>
                <th className="p-3">RESOURCE / ENTITY ID</th>
                <th className="p-3">RESULT</th>
                <th className="p-3">DETAILS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {logs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-6 text-center text-slate-500">
                    No audit records registered for current filter.
                  </td>
                </tr>
              ) : (
                logs.map((lg) => (
                  <tr key={lg.id} className="hover:bg-slate-800/40 transition">
                    <td className="p-3 text-slate-400">
                      {lg.timestamp ? new Date(lg.timestamp).toLocaleString() : 'Recent'}
                    </td>
                    <td className="p-3 font-bold text-white flex items-center gap-1.5">
                      <Lock className="w-3 h-3 text-indigo-400 shrink-0" />
                      <span>{lg.action}</span>
                    </td>
                    <td className="p-3 text-indigo-300 font-semibold">{lg.resource_type || lg.entity}</td>
                    <td className="p-3 text-cyan-400">{lg.resource_id || lg.entity_id || '-'}</td>
                    <td className="p-3">
                      <span
                        className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border ${
                          lg.result === 'SUCCESS'
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                            : 'bg-amber-950 text-amber-300 border-amber-700'
                        }`}
                      >
                        {lg.result || 'RECORDED'}
                      </span>
                    </td>
                    <td className="p-3 text-slate-400 max-w-xs truncate font-mono text-[11px]">
                      {lg.details || '-'}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
