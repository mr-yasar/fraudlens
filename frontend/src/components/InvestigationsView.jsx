import React, { useState, useEffect } from 'react'
import {
  ShieldAlert,
  Search,
  Clock,
  CheckCircle2,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Eye,
  FileText,
  X,
  UserCheck,
} from 'lucide-react'
import { investigationsApi } from '../services/api'

export default function InvestigationsView({ onInspectExplanation }) {
  const [cases, setCases] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(15)
  const [statusFilter, setStatusFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Case Detail modal state
  const [selectedCase, setSelectedCase] = useState(null)
  const [caseLoading, setCaseLoading] = useState(false)
  const [updateMsg, setUpdateMsg] = useState(null)

  // Edit form state
  const [editStatus, setEditStatus] = useState('')
  const [editDecision, setEditDecision] = useState('')
  const [editNotes, setEditNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const fetchCases = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await investigationsApi.list({
        page,
        limit,
        status: statusFilter,
      })
      setCases(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve investigations')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCases()
  }, [page, statusFilter])

  const handleOpenCase = async (caseId) => {
    setCaseLoading(true)
    setUpdateMsg(null)
    try {
      const data = await investigationsApi.get(caseId)
      setSelectedCase(data)
      setEditStatus(data.status || 'OPEN')
      setEditDecision(data.decision || '')
      setEditNotes(data.notes || '')
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to load case detail')
    } finally {
      setCaseLoading(false)
    }
  }

  const handleSaveCase = async (e) => {
    e.preventDefault()
    if (!selectedCase) return

    setSubmitting(true)
    try {
      const payload = {
        status: editStatus,
        decision: editDecision || null,
        notes: editNotes,
      }
      const updated = await investigationsApi.update(selectedCase.case_id, payload)
      setSelectedCase(updated)
      setUpdateMsg('Case updated and logged successfully')
      fetchCases()
      setTimeout(() => setUpdateMsg(null), 3500)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to update investigation case')
    } finally {
      setSubmitting(false)
    }
  }

  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <ShieldAlert className="w-5 h-5 text-cyan-400" />
          Investigation &amp; Case Management Operations
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          End-to-end case tracking, evidence logging, status transitions, and final fraud adjudications.
        </p>
      </div>

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-slate-400 uppercase">Status:</span>
          <div className="flex gap-1.5">
            {['', 'OPEN', 'UNDER_REVIEW', 'RESOLVED'].map((st) => (
              <button
                key={st}
                onClick={() => {
                  setStatusFilter(st)
                  setPage(1)
                }}
                className={`px-3 py-1 rounded-xl text-xs font-medium font-mono transition ${
                  statusFilter === st
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 font-bold'
                    : 'bg-slate-950/60 text-slate-400 border border-slate-800 hover:text-white'
                }`}
              >
                {st === '' ? 'ALL' : st}
              </button>
            ))}
          </div>
        </div>

        <button
          onClick={fetchCases}
          className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          title="Refresh Cases"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Cases Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
            <span>Retrieving investigation cases...</span>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-xs text-rose-400">{error}</div>
        ) : cases.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 space-y-2">
            <ShieldAlert className="w-8 h-8 mx-auto text-slate-600" />
            <div className="font-semibold text-slate-300">No active investigations</div>
            <p>Flagged high-risk transactions can be converted into investigation cases.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Case ID</th>
                  <th className="py-3 px-4">Transaction ID</th>
                  <th className="py-3 px-4">Created Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Adjudication</th>
                  <th className="py-3 px-4">Assigned Investigator</th>
                  <th className="py-3 px-4 text-right">Inspect</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {cases.map((c) => {
                  const isResolved = c.status === 'RESOLVED'
                  const isReview = c.status === 'UNDER_REVIEW'
                  const isFraud = c.decision === 'CONFIRMED_FRAUD'
                  const isGenuine = c.decision === 'GENUINE'

                  return (
                    <tr key={c.id || c.case_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono font-bold text-cyan-400">
                        {c.case_id}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">
                        {c.transaction_id}
                      </td>
                      <td className="py-3 px-4 text-slate-400 font-mono text-[11px]">
                        {c.created_at ? new Date(c.created_at).toLocaleString() : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                            isResolved
                              ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                              : isReview
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-cyan-950 text-cyan-400 border border-cyan-800'
                          }`}
                        >
                          {c.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {c.decision ? (
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                              isFraud
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            }`}
                          >
                            {c.decision}
                          </span>
                        ) : (
                          <span className="text-slate-500 font-mono text-[11px]">Pending</span>
                        )}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">
                        {c.investigator_name || (c.investigator_id ? `Analyst #${c.investigator_id}` : 'Unassigned')}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleOpenCase(c.case_id)}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-cyan-300 border border-slate-700 text-xs font-medium transition"
                        >
                          Manage &rarr;
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination */}
        <div className="p-3 bg-slate-950/40 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <span className="text-white font-mono">{page}</span> of{' '}
            <span className="text-white font-mono">{totalPages}</span> ({total} cases)
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Case Management Drawer / Modal */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="max-w-2xl w-full rounded-2xl bg-slate-900 border border-cyan-800/70 shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <ShieldAlert className="w-5 h-5 text-cyan-400" />
                <div>
                  <h3 className="text-base font-bold text-white">
                    Investigation Dossier: <span className="font-mono text-cyan-400">{selectedCase.case_id}</span>
                  </h3>
                  <div className="text-[10px] text-slate-400 font-mono">
                    Created: {new Date(selectedCase.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedCase(null)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                  Back to Cases
                </button>
                <button
                  onClick={() => setSelectedCase(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {updateMsg && (
              <div className="p-3 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4" />
                <span>{updateMsg}</span>
              </div>
            )}

            {/* Target Transaction Profile */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-300">
                <span>Associated Transaction Data</span>
                <span className="font-mono text-cyan-400">{selectedCase.transaction_id}</span>
              </div>
              {selectedCase.transaction && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1 font-mono text-xs">
                  <div className="p-2 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-slate-400 block">Customer</span>
                    <span className="text-slate-200">{selectedCase.transaction.customer_id}</span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-slate-400 block">Amount</span>
                    <span className="font-bold text-white">${Number(selectedCase.transaction.amount).toFixed(2)}</span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-slate-400 block">Probability</span>
                    <span className="text-rose-400">
                      {(Number(selectedCase.transaction.fraud_probability || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded-lg">
                    <span className="text-[10px] text-slate-400 block">Risk Score</span>
                    <span className="text-cyan-400">{selectedCase.transaction.risk_score} / 100</span>
                  </div>
                </div>
              )}
            </div>

            {/* Investigator Action Form */}
            <form onSubmit={handleSaveCase} className="space-y-4 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">Lifecycle Status</label>
                  <select
                    value={editStatus}
                    onChange={(e) => setEditStatus(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="OPEN">OPEN (Under Active Triage)</option>
                    <option value="UNDER_REVIEW">UNDER_REVIEW (Evidence Gathering)</option>
                    <option value="RESOLVED">RESOLVED (Case Closed)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-[11px] font-medium text-slate-300 mb-1">
                    Final Adjudication Determination
                  </label>
                  <select
                    value={editDecision}
                    onChange={(e) => setEditDecision(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="">-- No Decision (Pending) --</option>
                    <option value="CONFIRMED_FRAUD">CONFIRMED_FRAUD</option>
                    <option value="GENUINE">GENUINE (False Positive)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-[11px] font-medium text-slate-300 mb-1">
                  Investigator Findings &amp; Evidentiary Notes
                </label>
                <textarea
                  rows={4}
                  value={editNotes}
                  onChange={(e) => setEditNotes(e.target.value)}
                  placeholder="Document merchant contact, device telemetry confirmation, or rationale for final determination..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                {onInspectExplanation && (
                  <button
                    type="button"
                    onClick={() => {
                      const txId = selectedCase.transaction_id
                      setSelectedCase(null)
                      onInspectExplanation(txId)
                    }}
                    className="text-purple-400 hover:text-purple-300 text-xs font-mono flex items-center gap-1"
                  >
                    Inspect SHAP for this Transaction &rarr;
                  </button>
                )}

                <div className="flex gap-2 ml-auto">
                  <button
                    type="button"
                    onClick={() => setSelectedCase(null)}
                    className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
                  >
                    Close
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-1.5"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${submitting ? 'animate-spin' : ''}`} />
                    {submitting ? 'Saving...' : 'Update Investigation Record'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
