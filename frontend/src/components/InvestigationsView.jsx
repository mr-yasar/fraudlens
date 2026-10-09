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
  Bot,
  Sparkles,
  Volume2,
  Mic,
} from 'lucide-react'
import { investigationsApi } from '../services/api'
import AiInvestigationModal from './AiInvestigationModal'
import GlobalCenterModal from './common/GlobalCenterModal'
import { getCustomerPersona } from '../utils/customerHelper'

export default function InvestigationsView({
  onInspectExplanation,
  initialTxId = null,
  initialCaseId = null,
  onSwitchToRadar = null,
  user = null,
  isAdmin = false,
}) {
  const customerPersona = getCustomerPersona(user) || {}
  const isCustomer = !isAdmin && Boolean(customerPersona.isCustomer)

  const [cases, setCases] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit, setLimit] = useState(15)
  const [statusFilter, setStatusFilter] = useState('')
  const [decisionFilter, setDecisionFilter] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)


  // Target transaction from Live Radar stream
  const [targetTx, setTargetTx] = useState(initialTxId)
  const [creatingCase, setCreatingCase] = useState(false)

  // AI Copilot Modal State
  const [aiModalCaseId, setAiModalCaseId] = useState(null)

  // Case Detail modal state
  const [selectedCase, setSelectedCase] = useState(null)
  const [caseLoading, setCaseLoading] = useState(false)
  const [updateMsg, setUpdateMsg] = useState(null)

  // Edit form state
  const [editStatus, setEditStatus] = useState('')
  const [editDecision, setEditDecision] = useState('')
  const [editNotes, setEditNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)

  // Bulk Decision state
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkToast, setBulkToast] = useState(null)

  const handleBulkApproveAll = async () => {
    const confirmed = window.confirm(
      'Approve All Decisions: Are you sure you want to approve all pending cases and allow all held transactions as GENUINE?'
    )
    if (!confirmed) return

    setBulkLoading(true)
    try {
      const res = await investigationsApi.bulkDecision({
        decision: 'GENUINE',
        status: 'RESOLVED',
        notes: 'Bulk approved and allowed by Administrator.',
      })
      setBulkToast(`✓ Successfully approved and allowed ${res.processed_count} decisions!`)
      setTimeout(() => setBulkToast(null), 4500)
      fetchCases()
    } catch (err) {
      alert(`Bulk approval failed: ${err.message}`)
    } finally {
      setBulkLoading(false)
    }
  }

  useEffect(() => {
    if (initialTxId) {
      setTargetTx(initialTxId)
    }
  }, [initialTxId])

  useEffect(() => {
    if (initialCaseId) {
      handleOpenCase(initialCaseId)
    }
  }, [initialCaseId])

  // If targetTx matches an existing case, open it
  useEffect(() => {
    if (targetTx && cases.length > 0) {
      const match = cases.find((c) => c.transaction_id === targetTx)
      if (match) {
        handleOpenCase(match.case_id)
      }
    }
  }, [targetTx, cases])

  const handleCreateCaseForTx = async (txId) => {
    setCreatingCase(true)
    try {
      const newCase = await investigationsApi.create({
        transaction_id: txId,
        notes: `Escalated from Live Fraud Monitor radar by ${user?.username || 'investigator'}. Immediate risk review required.`,
      })
      fetchCases()
      if (newCase && newCase.case_id) {
        handleOpenCase(newCase.case_id)
      }
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to create investigation case')
    } finally {
      setCreatingCase(false)
    }
  }

  const fetchCases = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await investigationsApi.list({
        page,
        limit,
        status: statusFilter || undefined,
        decision: decisionFilter || undefined,
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
  }, [page, statusFilter, decisionFilter])

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

  // Direct adjudication handler: updates backend SQLite DB and refreshes state
  const handleQuickAdjudicate = async (caseId, decision, targetStatus = 'RESOLVED', customNotes = null) => {
    setSubmitting(true)
    setUpdateMsg(null)
    try {
      const isFraud = decision === 'CONFIRMED_FRAUD'
      const isGenuine = decision === 'GENUINE'
      const notes = customNotes || editNotes?.trim() || (isFraud
        ? 'Confirmed fraud determination by investigator. Transaction flagged, session terminated, and funds frozen.'
        : isGenuine
        ? 'Investigator verified transaction telemetry as genuine / false positive.'
        : 'Case moved to active investigation review.')

      const payload = {
        status: targetStatus,
        decision: decision || null,
        notes: notes,
      }
      const updated = await investigationsApi.update(caseId, payload)
      if (selectedCase && selectedCase.case_id === caseId) {
        setSelectedCase(updated)
        setEditStatus(updated.status)
        setEditDecision(updated.decision || '')
        setEditNotes(updated.notes || '')
      }
      setUpdateMsg(
        isFraud
          ? '✓ Decision Persisted: FRAUD CONFIRMED (Status: RESOLVED)'
          : isGenuine
          ? '✓ Decision Persisted: NOT FRAUD / GENUINE (Status: RESOLVED)'
          : `✓ Case status updated to ${targetStatus}`
      )
      fetchCases()
      setTimeout(() => setUpdateMsg(null), 4000)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to apply investigation decision')
    } finally {
      setSubmitting(false)
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
      setUpdateMsg('✓ Case record and determinations saved successfully to database')
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
          <span>Fraud Investigation &amp; Case Adjudication Operations</span>
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          End-to-end case tracking, evidence logging, status transitions, and final fraud adjudications across customer transactions and reported complaints.
        </p>
      </div>


      {/* Target Transaction Escalation Card from Live Radar */}
      {targetTx && (
        <div className="p-3.5 rounded-2xl bg-indigo-950/70 border border-indigo-700/80 flex flex-wrap items-center justify-between gap-3 text-xs shadow-lg">
          <div className="flex items-center gap-2">
            <span className="font-mono text-indigo-300 font-bold">Escalated from Live Radar:</span>
            <span className="font-mono bg-indigo-900/90 px-2 py-0.5 rounded text-white font-bold border border-indigo-500">
              {targetTx}
            </span>
            {cases.some((c) => c.transaction_id === targetTx) ? (
              <span className="text-[10px] font-mono text-emerald-400 bg-emerald-950/80 px-2 py-0.5 rounded border border-emerald-800">
                Case Linked #{cases.find((c) => c.transaction_id === targetTx)?.case_id}
              </span>
            ) : (
              <span className="text-[10px] font-mono text-amber-300 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800">
                No active case opened yet
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {!cases.some((c) => c.transaction_id === targetTx) && (
              <button
                type="button"
                disabled={creatingCase}
                onClick={() => handleCreateCaseForTx(targetTx)}
                className="px-3 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-mono font-bold text-xs transition flex items-center gap-1.5 shadow"
              >
                <ShieldAlert className="w-3.5 h-3.5" />
                <span>{creatingCase ? 'Creating Case...' : 'Open New Case for this TX'}</span>
              </button>
            )}

            {onSwitchToRadar && (
              <button
                type="button"
                onClick={onSwitchToRadar}
                className="px-3 py-1.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-cyan-300 border border-cyan-800 font-mono text-xs transition flex items-center gap-1"
              >
                <span>Live Radar Stream</span>
                <span>&rarr;</span>
              </button>
            )}

            <button
              type="button"
              onClick={() => setTargetTx(null)}
              className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-900 transition"
              title="Clear Target"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Filter Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-xs font-mono text-slate-400 uppercase">Case Filter:</span>
          <div className="flex flex-wrap gap-1.5">
            {[
              { label: 'ALL CASES', status: '', decision: '' },
              { label: 'NEW / OPEN', status: 'OPEN', decision: '' },
              { label: 'UNDER INVESTIGATION', status: 'UNDER_REVIEW', decision: '' },
              { label: 'FRAUD CONFIRMED', status: '', decision: 'CONFIRMED_FRAUD' },
              { label: 'NOT FRAUD', status: '', decision: 'GENUINE' },
              { label: 'RESOLVED', status: 'RESOLVED', decision: '' },
            ].map((f) => {
              const isActive = statusFilter === f.status && decisionFilter === f.decision
              return (
                <button
                  key={f.label}
                  onClick={() => {
                    setStatusFilter(f.status)
                    setDecisionFilter(f.decision)
                    setPage(1)
                  }}
                  className={`px-3 py-1 rounded-xl text-xs font-medium font-mono transition cursor-pointer ${
                    isActive
                      ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 font-bold shadow'
                      : 'bg-slate-950/60 text-slate-400 border border-slate-800 hover:text-white hover:bg-slate-900'
                  }`}
                >
                  {f.label}
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Bulk Approve All / Allow All Decisions Button */}
          <button
            onClick={handleBulkApproveAll}
            disabled={bulkLoading}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-xs shadow-md transition disabled:opacity-50 cursor-pointer"
            title="Approve All Decisions and Allow Pending Holds"
          >
            <CheckCircle2 className="w-3.5 h-3.5" />
            <span>{bulkLoading ? 'Adjudicating...' : 'Approve All Decisions (Allow All)'}</span>
          </button>

          <button
            onClick={fetchCases}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition cursor-pointer"
            title="Refresh Cases"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Bulk Feedback Banner */}
      {bulkToast && (
        <div className="p-3 rounded-xl bg-emerald-950/80 border border-emerald-500/60 text-emerald-200 text-xs font-mono flex items-center justify-between shadow-lg animate-fadeIn">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
            <span className="font-bold">{bulkToast}</span>
          </div>
          <button
            onClick={() => setBulkToast(null)}
            className="text-emerald-400 hover:text-white"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

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
                  <th className="py-3 px-4 text-right">Actions &amp; AI</th>
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
                        <div className="flex items-center justify-end gap-1.5">
                          {/* Fast Adjudication Buttons on Row */}
                          {c.status !== 'RESOLVED' && (
                            <>
                              <button
                                type="button"
                                disabled={submitting}
                                onClick={() => handleQuickAdjudicate(c.case_id, 'CONFIRMED_FRAUD', 'RESOLVED')}
                                className="px-2 py-1 rounded-lg bg-rose-950/80 hover:bg-rose-900 text-rose-300 hover:text-white border border-rose-800/80 hover:border-rose-600 text-[10px] font-mono font-bold transition flex items-center gap-1 cursor-pointer disabled:opacity-50"
                                title="Confirm Fraud & Resolve Case"
                              >
                                <span>Confirm Fraud</span>
                              </button>
                              <button
                                type="button"
                                disabled={submitting}
                                onClick={() => handleQuickAdjudicate(c.case_id, 'GENUINE', 'RESOLVED')}
                                className="px-2 py-1 rounded-lg bg-emerald-950/80 hover:bg-emerald-900 text-emerald-300 hover:text-white border border-emerald-800/80 hover:border-emerald-600 text-[10px] font-mono font-bold transition flex items-center gap-1 cursor-pointer disabled:opacity-50"
                                title="Mark Not Fraud / Genuine"
                              >
                                <span>Not Fraud</span>
                              </button>
                            </>
                          )}

                          <button
                            onClick={() => setAiModalCaseId(c.case_id)}
                            className="px-2.5 py-1 rounded-lg bg-gradient-to-r from-purple-700 via-indigo-700 to-cyan-700 hover:from-purple-600 hover:to-cyan-600 text-white text-xs font-bold shadow flex items-center gap-1.5 transition active:scale-95 cursor-pointer"
                            title="Launch AI Forensic Copilot (Gemini, Grok, Siri Voice & Attack Diagrams)"
                          >
                            <Bot className="w-3.5 h-3.5 text-cyan-300" />
                            <span className="hidden sm:inline">AI Copilot</span>
                          </button>
                          <button
                            onClick={() => handleOpenCase(c.case_id)}
                            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-medium transition cursor-pointer"
                          >
                            Manage &rarr;
                          </button>
                        </div>
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
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Case Management Modal */}
      {selectedCase && (
        <GlobalCenterModal
          isOpen={Boolean(selectedCase)}
          onClose={() => setSelectedCase(null)}
          title={`Investigation Dossier: ${selectedCase.case_id}`}
          subtitle={`Created: ${new Date(selectedCase.created_at).toLocaleString()}`}
          icon={ShieldAlert}
          badge={selectedCase.status || 'OPEN'}
          badgeType={selectedCase.status === 'RESOLVED' ? 'success' : 'danger'}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-5">

            {/* AI Copilot & Voice Briefing Feature Banner */}
            <div className="p-3.5 rounded-xl bg-gradient-to-r from-purple-950/80 via-indigo-950/70 to-slate-900 border border-purple-700/60 flex flex-wrap items-center justify-between gap-3 shadow-lg">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-purple-600/30 border border-purple-500/40 flex items-center justify-center text-purple-300 shadow-inner shrink-0">
                  <Bot className="w-5 h-5 animate-pulse text-cyan-300" />
                </div>
                <div>
                  <div className="text-xs font-bold text-white flex items-center gap-2">
                    <span>Autonomous AI Forensic Agent &amp; Diagrams</span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800">
                      Gemini 1.5 Pro &bull; Grok-2 &bull; Siri Voice
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    Generate attack kill-chain diagrams, hear spoken audio briefings, and file regulatory SARs.
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setAiModalCaseId(selectedCase.case_id)}
                className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white text-xs font-bold shadow-lg flex items-center gap-1.5 transition active:scale-95 shrink-0 cursor-pointer"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                <span>Launch AI Briefing &amp; Voice</span>
              </button>
            </div>

            {/* Fast-Track Immediate Case Determination Bar */}
            <div className="p-4 rounded-2xl bg-slate-950 border border-indigo-900/60 shadow-lg space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono uppercase font-bold text-slate-300 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-amber-400" />
                  <span>Fast-Track Adjudication Actions (Persists to Database):</span>
                </span>
                <span className="text-[10px] font-mono text-slate-500">Immediate Database Save</span>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => handleQuickAdjudicate(selectedCase.case_id, 'CONFIRMED_FRAUD', 'RESOLVED')}
                  className="px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-mono font-bold text-xs transition flex items-center justify-center gap-1.5 shadow-md shadow-rose-950/40 disabled:opacity-50 cursor-pointer active:scale-95"
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>Confirm Fraud</span>
                </button>
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => handleQuickAdjudicate(selectedCase.case_id, 'GENUINE', 'RESOLVED')}
                  className="px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white font-mono font-bold text-xs transition flex items-center justify-center gap-1.5 shadow-md shadow-emerald-950/40 disabled:opacity-50 cursor-pointer active:scale-95"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Not Fraud (Genuine)</span>
                </button>
                <button
                  type="button"
                  disabled={submitting}
                  onClick={() => handleQuickAdjudicate(selectedCase.case_id, null, 'UNDER_REVIEW')}
                  className="px-3.5 py-2.5 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white font-mono font-bold text-xs transition flex items-center justify-center gap-1.5 shadow-md shadow-amber-950/40 disabled:opacity-50 cursor-pointer active:scale-95"
                >
                  <Clock className="w-4 h-4" />
                  <span>Under Investigation</span>
                </button>
              </div>
            </div>

            {updateMsg && (
              <div className="p-3.5 rounded-xl bg-emerald-950/80 border border-emerald-500/80 text-emerald-200 text-xs font-mono flex items-center gap-2 shadow-lg animate-fadeIn">
                <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                <span className="font-bold">{updateMsg}</span>
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
                    className="text-purple-400 hover:text-purple-300 text-xs font-mono flex items-center gap-1 cursor-pointer"
                  >
                    Inspect SHAP for this Transaction &rarr;
                  </button>
                )}

                <div className="flex gap-2 ml-auto">
                  <button
                    type="button"
                    onClick={() => setSelectedCase(null)}
                    className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 text-xs hover:bg-slate-700 cursor-pointer"
                  >
                    Close
                  </button>
                  <button
                    type="submit"
                    disabled={submitting}
                    className="px-4 py-1.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-1.5 cursor-pointer"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${submitting ? 'animate-spin' : ''}`} />
                    {submitting ? 'Saving...' : 'Update Investigation Record'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </GlobalCenterModal>
      )}

      {/* Autonomous AI Copilot, Diagrams & Voice Briefing Modal */}
      <AiInvestigationModal
        isOpen={Boolean(aiModalCaseId)}
        caseId={aiModalCaseId}
        onClose={() => setAiModalCaseId(null)}
        onDecisionApplied={(appliedDecision, newStatus, updatedCase) => {
          fetchCases()
          if (selectedCase && selectedCase.case_id === aiModalCaseId) {
            setSelectedCase((prev) => ({
              ...prev,
              decision: appliedDecision,
              status: newStatus,
              ...(updatedCase || {}),
            }))
            setEditStatus(newStatus)
            setEditDecision(appliedDecision)
          }
        }}
      />
    </div>
  )
}
