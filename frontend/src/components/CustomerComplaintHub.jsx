import React, { useState, useEffect } from 'react'
import {
  ShieldAlert,
  CheckCircle2,
  Clock,
  AlertTriangle,
  ArrowRight,
  FileText,
  RefreshCw,
  Search,
  Sparkles,
  HelpCircle,
  ChevronRight,
  ShieldCheck,
  Send,
  XCircle,
} from 'lucide-react'
import { investigationsApi } from '../services/api'
import { formatINR } from '../utils/formatters'
import { getCustomerPersona } from '../utils/customerHelper'

const COMPLAINT_REASONS = [
  {
    id: 'unauthorized',
    label: 'Unauthorized Transaction / Stolen Card',
    description: 'I did not initiate or authorize this charge.',
  },
  {
    id: 'incorrect_amount',
    label: 'Charged Incorrect / Excess Amount',
    description: 'The billed amount is higher than agreed or authorized.',
  },
  {
    id: 'duplicate_charge',
    label: 'Duplicate Debit / Multiple Charges',
    description: 'Charged multiple times for a single purchase.',
  },
  {
    id: 'merchant_scam',
    label: 'Merchant Fraud / Goods Not Received',
    description: 'Paid merchant but services/goods were fraudulent or not delivered.',
  },
  {
    id: 'account_takeover',
    label: 'Account Takeover / Phishing Suspicion',
    description: 'Suspect my credentials or session were compromised.',
  },
  {
    id: 'other',
    label: 'Other Suspicious Activity',
    description: 'Unusual velocity or unfamiliar merchant activity.',
  },
]

export default function CustomerComplaintHub({
  user,
  initialTxId = null,
  initialTxObj = null,
  onViewExplanation = null,
  onSwitchToRadar = null,
}) {
  const customerPersona = getCustomerPersona(user) || {}

  const [activeTab, setActiveTab] = useState(initialTxId ? 'raise' : 'raise')
  const [transactions, setTransactions] = useState([])
  const [loadingTx, setLoadingTx] = useState(false)
  const [selectedTxId, setSelectedTxId] = useState(initialTxId || '')
  const [selectedReason, setSelectedReason] = useState(COMPLAINT_REASONS[0].id)
  const [userNotes, setUserNotes] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [submissionResult, setSubmissionResult] = useState(null)
  const [submitError, setSubmitError] = useState(null)

  // Tracking state
  const [complaints, setComplaints] = useState([])
  const [loadingComplaints, setLoadingComplaints] = useState(false)
  const [complaintError, setComplaintError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')

  const getToken = () => localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')

  // Fetch customer's own recent transactions for the dropdown/selector
  const fetchCustomerTransactions = async () => {
    setLoadingTx(true)
    try {
      const token = getToken()
      const res = await fetch('/api/v1/transactions?limit=30', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (res.ok) {
        const data = await res.json()
        const txList = data.transactions || data.items || []
        setTransactions(txList)
        if (!selectedTxId && txList.length > 0) {
          setSelectedTxId(txList[0].transaction_id)
        }
      }
    } catch (err) {
      console.error('Failed to load transactions:', err)
    } finally {
      setLoadingTx(false)
    }
  }

  // Fetch customer's submitted complaints
  const fetchComplaints = async () => {
    setLoadingComplaints(true)
    setComplaintError(null)
    try {
      const data = await investigationsApi.list({ page: 1, limit: 50 })
      setComplaints(data.items || [])
    } catch (err) {
      setComplaintError(err instanceof Error ? err.message : 'Failed to retrieve complaint records')
    } finally {
      setLoadingComplaints(false)
    }
  }

  useEffect(() => {
    fetchCustomerTransactions()
    fetchComplaints()
  }, [])

  useEffect(() => {
    if (initialTxId) {
      setSelectedTxId(initialTxId)
      setActiveTab('raise')
      setSubmissionResult(null)
    }
  }, [initialTxId])

  const selectedTx = transactions.find((t) => t.transaction_id === selectedTxId) || (initialTxObj?.transaction_id === selectedTxId ? initialTxObj : null)

  const handleSubmitComplaint = async (e) => {
    e.preventDefault()
    if (!selectedTxId) {
      setSubmitError('Please select a transaction to report.')
      return
    }

    setSubmitting(true)
    setSubmitError(null)

    const reasonObj = COMPLAINT_REASONS.find((r) => r.id === selectedReason)
    const reasonTitle = reasonObj ? reasonObj.label : 'Fraud Complaint'
    const formattedNotes = `[CUSTOMER REPORTED FRAUD]\nReason: ${reasonTitle}\nDetails: ${userNotes.trim() || 'No additional details provided by customer.'}`

    try {
      const res = await investigationsApi.create({
        transaction_id: selectedTxId.trim(),
        notes: formattedNotes,
      })
      setSubmissionResult({
        caseId: res.case_id || 'CASE-CONFIRMED',
        transactionId: selectedTxId,
        reason: reasonTitle,
        submittedAt: new Date().toISOString(),
      })
      fetchComplaints()
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Failed to submit fraud complaint')
    } finally {
      setSubmitting(false)
    }
  }

  const handleResetForm = () => {
    setSubmissionResult(null)
    setUserNotes('')
    setSubmitError(null)
  }

  const filteredComplaints = complaints.filter((c) => {
    if (!searchQuery) return true
    const q = searchQuery.toLowerCase()
    return (
      c.case_id?.toLowerCase().includes(q) ||
      c.transaction_id?.toLowerCase().includes(q) ||
      c.notes?.toLowerCase().includes(q) ||
      c.status?.toLowerCase().includes(q)
    )
  })

  return (
    <div className="space-y-6">
      {/* Sub-Header & Simple Tab Navigation */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 bg-slate-900/80 p-3 sm:p-4 rounded-2xl border border-slate-800 shadow-md">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => {
              setActiveTab('raise')
              setSubmissionResult(null)
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
              activeTab === 'raise'
                ? 'bg-rose-950 text-rose-300 border border-rose-700 shadow'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
            }`}
          >
            <ShieldAlert className="w-4 h-4 text-rose-400" />
            <span>Raise Fraud Complaint</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('tracking')
              fetchComplaints()
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-mono font-bold transition-all ${
              activeTab === 'tracking'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 shadow'
                : 'bg-slate-950 text-slate-400 border border-slate-800 hover:text-white'
            }`}
          >
            <Clock className="w-4 h-4 text-cyan-400" />
            <span>My Complaints &amp; Tracking ({complaints.length})</span>
          </button>
        </div>

        {onSwitchToRadar && (
          <button
            type="button"
            onClick={onSwitchToRadar}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-950 hover:bg-slate-800 text-slate-300 hover:text-cyan-300 border border-slate-800 text-xs font-mono transition"
          >
            <span>Back to Live Radar Stream</span>
            <ArrowRight className="w-3.5 h-3.5 text-cyan-400" />
          </button>
        )}
      </div>

      {/* TAB 1: RAISE COMPLAINT FLOW */}
      {activeTab === 'raise' && (
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Main Complaint Form (Left/Main Column) */}
          <div className="lg:col-span-8">
            {submissionResult ? (
              <div className="rounded-2xl bg-gradient-to-br from-slate-900 via-slate-950 to-emerald-950/40 border border-emerald-700/60 p-6 sm:p-8 shadow-2xl text-center space-y-6 animate-fade-in">
                <div className="w-16 h-16 rounded-2xl bg-emerald-950/80 border border-emerald-500/50 flex items-center justify-center mx-auto text-emerald-300 shadow-[0_0_30px_rgba(16,185,129,0.3)]">
                  <CheckCircle2 className="w-9 h-9 text-emerald-400" />
                </div>

                <div className="space-y-2">
                  <span className="px-3 py-1 rounded-full text-[11px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-700 uppercase">
                    Complaint Successfully Registered
                  </span>
                  <h2 className="text-2xl font-black text-white">Complaint Submitted to Fraud Operations</h2>
                  <p className="text-xs text-slate-300 max-w-lg mx-auto leading-relaxed">
                    Your fraud complaint for transaction <strong className="font-mono text-cyan-300">{submissionResult.transactionId}</strong> has been received. Our automated risk sentinel and fraud investigators are reviewing the transaction telemetry.
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-950/90 border border-slate-800 max-w-md mx-auto text-left space-y-2 font-mono text-xs">
                  <div className="flex justify-between items-center py-1 border-b border-slate-800">
                    <span className="text-slate-500">Complaint Reference:</span>
                    <span className="font-bold text-cyan-300">{submissionResult.caseId}</span>
                  </div>
                  <div className="flex justify-between items-center py-1 border-b border-slate-800">
                    <span className="text-slate-500">Reported Reason:</span>
                    <span className="font-bold text-slate-200">{submissionResult.reason}</span>
                  </div>
                  <div className="flex justify-between items-center py-1">
                    <span className="text-slate-500">Initial Status:</span>
                    <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px] font-bold uppercase">
                      Submitted (Under Review)
                    </span>
                  </div>
                </div>

                {/* Stepper Preview */}
                <div className="max-w-md mx-auto pt-2">
                  <div className="flex items-center justify-between text-[11px] font-mono font-semibold">
                    <div className="flex flex-col items-center gap-1 text-emerald-400">
                      <div className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-500 flex items-center justify-center text-xs">✓</div>
                      <span>1. Submitted</span>
                    </div>
                    <div className="h-0.5 flex-1 bg-gradient-to-r from-emerald-500 to-amber-500 mx-2" />
                    <div className="flex flex-col items-center gap-1 text-amber-300">
                      <div className="w-6 h-6 rounded-full bg-amber-950 border border-amber-500 flex items-center justify-center text-xs animate-pulse">2</div>
                      <span>2. Under Review</span>
                    </div>
                    <div className="h-0.5 flex-1 bg-slate-800 mx-2" />
                    <div className="flex flex-col items-center gap-1 text-slate-500">
                      <div className="w-6 h-6 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-xs">3</div>
                      <span>3. Decision</span>
                    </div>
                  </div>
                </div>

                <div className="flex flex-wrap items-center justify-center gap-3 pt-4">
                  <button
                    type="button"
                    onClick={() => {
                      setActiveTab('tracking')
                      fetchComplaints()
                    }}
                    className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-mono font-bold text-xs transition flex items-center gap-2 shadow-lg shadow-cyan-600/30 cursor-pointer"
                  >
                    <Clock className="w-4 h-4" />
                    <span>Track Complaint Status</span>
                  </button>
                  <button
                    type="button"
                    onClick={handleResetForm}
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-mono font-bold transition cursor-pointer"
                  >
                    Report Another Transaction
                  </button>
                </div>
              </div>
            ) : (
              <form
                onSubmit={handleSubmitComplaint}
                className="rounded-2xl bg-slate-900/90 border border-slate-800 p-6 sm:p-7 shadow-xl space-y-6 backdrop-blur-md"
              >
                <div>
                  <h2 className="text-lg font-black text-white flex items-center gap-2">
                    <ShieldAlert className="w-5 h-5 text-rose-400" />
                    <span>Report Fraudulent or Suspicious Transaction</span>
                  </h2>
                  <p className="text-xs text-slate-400 mt-1">
                    If you see a transaction you did not authorize or recognize, report it here. Our fraud operations team will investigate and secure your account.
                  </p>
                </div>

                {submitError && (
                  <div className="p-3.5 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-300 text-xs flex items-center gap-2">
                    <XCircle className="w-4 h-4 shrink-0" />
                    <span>{submitError}</span>
                  </div>
                )}

                {/* Step 1: Select Transaction */}
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">
                    1. Select Suspicious Transaction
                  </label>
                  {loadingTx ? (
                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-400 flex items-center gap-2">
                      <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
                      <span>Loading recent transactions...</span>
                    </div>
                  ) : transactions.length === 0 ? (
                    <div className="p-3 bg-slate-950 rounded-xl border border-slate-800 text-xs text-slate-400">
                      No recent transactions found on account.
                    </div>
                  ) : (
                    <select
                      value={selectedTxId}
                      onChange={(e) => setSelectedTxId(e.target.value)}
                      className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500 transition"
                    >
                      {transactions.map((tx) => (
                        <option key={tx.transaction_id || tx.id} value={tx.transaction_id}>
                          {tx.transaction_id} — {formatINR(tx.amount)} ({tx.merchant_name || tx.merchant_category || 'Merchant'}) — {tx.risk_level || 'LOW'} Risk
                        </option>
                      ))}
                    </select>
                  )}
                </div>

                {/* Step 2: Complaint Reason Selection */}
                <div className="space-y-2.5">
                  <label className="block text-xs font-mono uppercase tracking-wider text-slate-300 font-bold">
                    2. Select Complaint Reason
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {COMPLAINT_REASONS.map((r) => {
                      const isSelected = selectedReason === r.id
                      return (
                        <div
                          key={r.id}
                          onClick={() => setSelectedReason(r.id)}
                          className={`p-3 rounded-xl border cursor-pointer transition-all duration-200 ${
                            isSelected
                              ? 'bg-rose-950/60 border-rose-500 shadow-md shadow-rose-950/40 text-white'
                              : 'bg-slate-950/70 border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-slate-950'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <span className="font-bold text-xs">{r.label}</span>
                            <span
                              className={`w-4 h-4 rounded-full border flex items-center justify-center text-[10px] ${
                                isSelected
                                  ? 'border-rose-400 bg-rose-500 text-white font-bold'
                                  : 'border-slate-700 bg-slate-900 text-transparent'
                              }`}
                            >
                              ✓
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-1 leading-snug">
                            {r.description}
                          </p>
                        </div>
                      )
                    })}
                  </div>
                </div>

                {/* Step 3: Optional Additional Details */}
                <div className="space-y-2">
                  <label className="block text-xs font-mono uppercase tracking-wider text-slate-300 font-bold flex items-center justify-between">
                    <span>3. Additional Details (Optional)</span>
                    <span className="text-[10px] text-slate-500 font-normal">Max 500 chars</span>
                  </label>
                  <textarea
                    rows={3}
                    value={userNotes}
                    onChange={(e) => setUserNotes(e.target.value)}
                    maxLength={500}
                    placeholder="Describe what happened (e.g. lost phone, unauthorized OTP prompt, suspicious SMS)..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
                  />
                </div>

                {/* Submit Action */}
                <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3">
                  <div className="text-[11px] text-slate-400 flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
                    <span>Protected by zero-liability fraud policy.</span>
                  </div>

                  <button
                    type="submit"
                    disabled={submitting || !selectedTxId}
                    className="w-full sm:w-auto px-6 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-mono font-bold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-rose-900/30 disabled:opacity-50 cursor-pointer"
                  >
                    <Send className={`w-3.5 h-3.5 ${submitting ? 'animate-spin' : ''}`} />
                    <span>{submitting ? 'Registering Complaint...' : 'Submit Fraud Complaint'}</span>
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Right Sidebar: Selected Transaction Card Preview */}
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <span className="text-xs font-mono uppercase text-slate-400 font-bold">Transaction Overview</span>
                {selectedTx && (
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                      selectedTx.risk_level === 'HIGH' || selectedTx.is_fraud === 1
                        ? 'bg-rose-950 text-rose-300 border-rose-800'
                        : selectedTx.risk_level === 'MEDIUM'
                        ? 'bg-amber-950 text-amber-300 border-amber-800'
                        : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                    }`}
                  >
                    {selectedTx.risk_level || 'LOW'} RISK
                  </span>
                )}
              </div>

              {selectedTx ? (
                <div className="space-y-3 font-mono text-xs">
                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">Reference ID</span>
                    <span className="text-cyan-300 font-bold">{selectedTx.transaction_id}</span>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Amount</span>
                      <span className="font-bold text-white text-sm">{formatINR(selectedTx.amount)}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800">
                      <span className="text-[10px] text-slate-500 block">Channel</span>
                      <span className="font-bold text-slate-300">{selectedTx.transaction_type || 'UPI'}</span>
                    </div>
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">Merchant</span>
                    <span className="text-slate-200 font-semibold">{selectedTx.merchant_name || selectedTx.merchant_category || 'Merchant'}</span>
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-500 block uppercase">Timestamp</span>
                    <span className="text-slate-400 text-[11px]">
                      {selectedTx.created_at ? new Date(selectedTx.created_at).toLocaleString() : 'Recent'}
                    </span>
                  </div>

                  {selectedTx.fraud_scenario && (
                    <div className="p-2.5 rounded-xl bg-rose-950/40 border border-rose-900/60 text-[11px] text-rose-300 font-sans">
                      <span className="font-bold font-mono block text-rose-400 text-[10px] uppercase mb-0.5">Automated Risk Signal</span>
                      {selectedTx.fraud_scenario}
                    </div>
                  )}

                  {onViewExplanation && (
                    <button
                      type="button"
                      onClick={() => onViewExplanation(selectedTx.transaction_id)}
                      className="w-full py-2 rounded-xl bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 hover:text-white border border-indigo-700/60 text-xs font-mono font-semibold transition flex items-center justify-center gap-1.5 cursor-pointer mt-2"
                    >
                      <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                      <span>View AI Explainability (SHAP)</span>
                    </button>
                  )}
                </div>
              ) : (
                <div className="p-8 text-center text-xs text-slate-500">
                  Select a transaction to inspect its risk profile.
                </div>
              )}
            </div>

            {/* Help Card */}
            <div className="rounded-2xl bg-gradient-to-br from-indigo-950/40 to-slate-950 border border-indigo-800/40 p-4 space-y-2 text-xs">
              <div className="flex items-center gap-2 text-indigo-300 font-bold">
                <HelpCircle className="w-4 h-4 text-cyan-400" />
                <span>How Complaint Resolution Works</span>
              </div>
              <ul className="text-slate-400 text-[11px] space-y-1.5 pl-4 list-disc">
                <li>Complaints are automatically routed to our 24/7 Fraud Investigation Desk.</li>
                <li>Your account protections and temporary hold mechanisms are engaged immediately.</li>
                <li>You can track the live review stage in the <strong>My Complaints &amp; Tracking</strong> tab anytime.</li>
              </ul>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: COMPLAINT TRACKING VIEW */}
      {activeTab === 'tracking' && (
        <div className="space-y-4">
          {/* Tracking Search & Refresh */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 bg-slate-900/70 p-4 rounded-2xl border border-slate-800">
            <div className="relative w-full sm:w-80">
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="Search complaints by Ref # or TX..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>

            <button
              type="button"
              onClick={fetchComplaints}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-mono font-bold transition flex items-center gap-1.5 self-end sm:self-auto cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingComplaints ? 'animate-spin' : ''}`} />
              <span>Refresh Status</span>
            </button>
          </div>

          {/* Complaints List Cards */}
          {loadingComplaints ? (
            <div className="p-12 text-center text-xs text-slate-400 flex flex-col items-center gap-3 bg-slate-900/40 rounded-2xl border border-slate-800">
              <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
              <span>Loading your complaint records...</span>
            </div>
          ) : complaintError ? (
            <div className="p-6 text-center text-xs text-rose-400 bg-slate-900/60 rounded-2xl border border-slate-800">
              {complaintError}
            </div>
          ) : filteredComplaints.length === 0 ? (
            <div className="p-12 text-center text-xs text-slate-400 bg-slate-900/50 rounded-2xl border border-slate-800 space-y-3">
              <ShieldCheck className="w-10 h-10 mx-auto text-emerald-500/60" />
              <div className="font-bold text-sm text-slate-200">No Complaints on Record</div>
              <p className="max-w-md mx-auto text-slate-400">
                You currently have no open fraud complaints. If you notice any unauthorized charge, you can file a report anytime under <strong>Raise Fraud Complaint</strong>.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredComplaints.map((c) => {
                const isResolved = c.status === 'RESOLVED'
                const isUnderReview = c.status === 'UNDER_REVIEW'
                const isOpen = c.status === 'OPEN'
                const isFraudConfirmed = c.decision === 'CONFIRMED_FRAUD'
                const isGenuineConfirmed = c.decision === 'GENUINE'

                return (
                  <div
                    key={c.id || c.case_id}
                    className="rounded-2xl bg-slate-900/80 border border-slate-800 p-5 sm:p-6 shadow-xl space-y-4 backdrop-blur-md transition hover:border-slate-700"
                  >
                    {/* Header Row */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800/80 pb-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-indigo-950 border border-indigo-800 text-cyan-400">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-mono font-black text-sm text-white">{c.case_id}</span>
                            <span className="text-slate-500">•</span>
                            <span className="font-mono text-xs text-cyan-300">TX: {c.transaction_id}</span>
                          </div>
                          <div className="text-[11px] text-slate-400 font-mono mt-0.5">
                            Reported on: {c.created_at ? new Date(c.created_at).toLocaleString() : 'N/A'}
                          </div>
                        </div>
                      </div>

                      {/* Current Status Badge */}
                      <div>
                        {isResolved ? (
                          <span
                            className={`px-3 py-1 rounded-full text-xs font-mono font-bold border uppercase flex items-center gap-1.5 ${
                              isFraudConfirmed
                                ? 'bg-rose-950 text-rose-300 border-rose-800'
                                : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                            }`}
                          >
                            <CheckCircle2 className="w-3.5 h-3.5" />
                            <span>Decision: {isFraudConfirmed ? 'Fraud Confirmed (Dispute Won)' : 'Verified Genuine'}</span>
                          </span>
                        ) : isUnderReview ? (
                          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-amber-950 text-amber-300 border border-amber-800 uppercase flex items-center gap-1.5">
                            <Clock className="w-3.5 h-3.5 animate-pulse" />
                            <span>Under Investigation</span>
                          </span>
                        ) : (
                          <span className="px-3 py-1 rounded-full text-xs font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800 uppercase flex items-center gap-1.5">
                            <ShieldAlert className="w-3.5 h-3.5" />
                            <span>Complaint Submitted</span>
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Progress Tracking Stepper */}
                    <div className="py-2">
                      <div className="flex items-center justify-between text-[11px] font-mono font-semibold max-w-xl">
                        {/* Step 1 */}
                        <div className="flex flex-col items-center gap-1 text-emerald-400">
                          <div className="w-6 h-6 rounded-full bg-emerald-950 border border-emerald-500 flex items-center justify-center text-xs">
                            ✓
                          </div>
                          <span>1. Submitted</span>
                        </div>

                        {/* Line 1 */}
                        <div
                          className={`h-0.5 flex-1 mx-2 ${
                            isUnderReview || isResolved ? 'bg-emerald-500' : 'bg-slate-800'
                          }`}
                        />

                        {/* Step 2 */}
                        <div
                          className={`flex flex-col items-center gap-1 ${
                            isUnderReview
                              ? 'text-amber-300'
                              : isResolved
                              ? 'text-emerald-400'
                              : 'text-slate-500'
                          }`}
                        >
                          <div
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border ${
                              isUnderReview
                                ? 'bg-amber-950 border-amber-500 animate-pulse'
                                : isResolved
                                ? 'bg-emerald-950 border-emerald-500'
                                : 'bg-slate-900 border-slate-700'
                            }`}
                          >
                            {isResolved ? '✓' : '2'}
                          </div>
                          <span>2. Under Review</span>
                        </div>

                        {/* Line 2 */}
                        <div
                          className={`h-0.5 flex-1 mx-2 ${
                            isResolved ? 'bg-emerald-500' : 'bg-slate-800'
                          }`}
                        />

                        {/* Step 3 */}
                        <div
                          className={`flex flex-col items-center gap-1 ${
                            isResolved ? 'text-emerald-400' : 'text-slate-500'
                          }`}
                        >
                          <div
                            className={`w-6 h-6 rounded-full flex items-center justify-center text-xs border ${
                              isResolved
                                ? 'bg-emerald-950 border-emerald-500'
                                : 'bg-slate-900 border-slate-700'
                            }`}
                          >
                            {isResolved ? '✓' : '3'}
                          </div>
                          <span>3. Decision Made</span>
                        </div>
                      </div>
                    </div>

                    {/* Summary Info */}
                    <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
                      <div>
                        <span className="text-[10px] text-slate-500 block uppercase">Reported Details</span>
                        <span className="text-slate-300 line-clamp-2">
                          {c.notes || 'Complaint filed for suspicious transaction review.'}
                        </span>
                      </div>

                      {c.amount && (
                        <div className="sm:text-right shrink-0">
                          <span className="text-[10px] text-slate-500 block uppercase">Amount</span>
                          <span className="font-bold text-white text-sm">{formatINR(c.amount)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
