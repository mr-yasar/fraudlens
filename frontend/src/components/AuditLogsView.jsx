import React, { useState, useEffect } from 'react'
import {
  History,
  Search,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ShieldCheck,
  Eye,
  X,
} from 'lucide-react'
import { auditLogsApi } from '../services/api'


export default function AuditLogsView() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(15)
  const [actionFilter, setActionFilter] = useState('')
  const [resourceFilter, setResourceFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Selected Log Detail Modal
  const [selectedLog, setSelectedLog] = useState(null)

  const fetchLogs = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await auditLogsApi.list({
        page,
        limit,
        action: actionFilter,
        resource_type: resourceFilter,
        search: searchQuery,
      })
      setLogs(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve audit trail')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [page, actionFilter, resourceFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    setPage(1)
    fetchLogs()
  }

  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <History className="w-5 h-5 text-cyan-400" />
          Enterprise Compliance Audit Trail
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Immutable ledger of security actions, transaction evaluations, investigation updates, and model activations.
        </p>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex flex-wrap items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search audit trail by user, resource ID, or keyword..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          {/* Action Filter */}
          <select
            value={actionFilter}
            onChange={(e) => {
              setActionFilter(e.target.value)
              setPage(1)
            }}
            className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Actions</option>
            <option value="CREATE">CREATE</option>
            <option value="UPDATE">UPDATE</option>
            <option value="EVALUATE">EVALUATE</option>
            <option value="ACTIVATE">ACTIVATE</option>
            <option value="TRAIN">TRAIN</option>
            <option value="LOGIN">LOGIN</option>
          </select>

          {/* Resource Filter */}
          <select
            value={resourceFilter}
            onChange={(e) => {
              setResourceFilter(e.target.value)
              setPage(1)
            }}
            className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Resources</option>
            <option value="TRANSACTION">TRANSACTION</option>
            <option value="INVESTIGATION">INVESTIGATION</option>
            <option value="MODEL">MODEL</option>
            <option value="DATASET">DATASET</option>
            <option value="AUTH">AUTH</option>
          </select>

          <button
            onClick={fetchLogs}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh Logs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Audit Logs Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
            <span>Scanning compliance audit ledger...</span>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-xs text-rose-400">{error}</div>
        ) : logs.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 space-y-2">
            <History className="w-8 h-8 mx-auto text-slate-600" />
            <div className="font-semibold text-slate-300">No audit records found</div>
            <p>Actions performed across the application are recorded here automatically.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Timestamp (UTC)</th>
                  <th className="py-3 px-4">User / Operator</th>
                  <th className="py-3 px-4">Action</th>
                  <th className="py-3 px-4">Resource Type</th>
                  <th className="py-3 px-4">Resource ID</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {logs.map((log) => {
                  const isCreate = log.action === 'CREATE'
                  const isUpdate = log.action === 'UPDATE'
                  const isActivate = log.action === 'ACTIVATE'

                  return (
                    <tr key={log.id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        {log.created_at ? new Date(log.created_at).toISOString().replace('T', ' ').slice(0, 19) : 'N/A'}
                      </td>
                      <td className="py-3 px-4 font-semibold text-slate-200">
                        {log.user_email || (log.user_id ? `User #${log.user_id}` : 'System / Auto')}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            isActivate
                              ? 'bg-purple-950 text-purple-300 border border-purple-800'
                              : isCreate
                              ? 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                              : isUpdate
                              ? 'bg-amber-950 text-amber-300 border border-amber-800'
                              : 'bg-slate-800 text-slate-300 border border-slate-700'
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-300 font-semibold">{log.resource_type}</td>
                      <td className="py-3 px-4 text-cyan-400 font-bold">{log.resource_id || 'N/A'}</td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => setSelectedLog(log)}
                          className="p-1 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition"
                          title="Inspect Details"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-3 bg-slate-950/40 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <span className="text-white font-mono">{page}</span> of{' '}
            <span className="text-white font-mono">{totalPages}</span> ({total} log entries)
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Log Detail Modal */}
      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="max-w-lg w-full rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white font-mono">
                  Audit Entry #{selectedLog.id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedLog(null)}
                className="p-1 text-slate-400 hover:text-white rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-2 text-xs font-mono">
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Timestamp:</span>
                <span className="text-white">{selectedLog.created_at}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Operator Email:</span>
                <span className="text-cyan-400">{selectedLog.user_email || `ID ${selectedLog.user_id}`}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Action:</span>
                <span className="text-emerald-400 font-bold">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/60">
                <span className="text-slate-400">Target Resource:</span>
                <span className="text-white">{selectedLog.resource_type} : {selectedLog.resource_id}</span>
              </div>
            </div>

            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">
                Sanitized Payload Details
              </span>
              <pre className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-slate-300 max-h-48 overflow-y-auto">
                {typeof selectedLog.details === 'object'
                  ? JSON.stringify(selectedLog.details, null, 2)
                  : selectedLog.details || 'No additional metadata'}
              </pre>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedLog(null)}
                className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
