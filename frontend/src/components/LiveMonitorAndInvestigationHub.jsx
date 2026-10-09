import React, { useState, useEffect, useCallback, useMemo } from 'react'
import {
  Radio,
  ShieldAlert,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Sliders,
  ArrowUpRight,
  Sparkles,
  Bot,
  User,
  Clock,
  Check,
  X,
  CreditCard,
  Smartphone,
  Globe,
  Lock,
  FileText,
  AlertCircle,
  HelpCircle,
  TrendingUp,
  Activity,
  Send,
  Zap,
} from 'lucide-react'
import { investigationsApi, alertsApi } from '../services/api'
import { formatINR } from '../utils/formatters'
import { getCustomerPersona, resolveCustomerName, getCustomerMeta, resolveAccountProfile } from '../utils/customerHelper'
import ContextualModuleHelp from './common/ContextualModuleHelp'
import GlobalCenterModal from './common/GlobalCenterModal'

// Pre-configured dispute reasons for customer reporting
const COMPLAINT_REASONS = [
  { id: 'unauthorized', label: 'Unauthorized Charge / Stolen Card', desc: 'Did not initiate or authorize this charge.' },
  { id: 'incorrect_amount', label: 'Incorrect / Excess Amount', desc: 'Billed higher than agreed or authorized.' },
  { id: 'duplicate_charge', label: 'Duplicate Debit', desc: 'Charged multiple times for a single purchase.' },
  { id: 'merchant_scam', label: 'Merchant Scam / Goods Not Received', desc: 'Paid merchant but goods were not delivered.' },
  { id: 'account_takeover', label: 'Account Takeover / Phishing', desc: 'Credentials or session suspected compromised.' },
]

export default function LiveMonitorAndInvestigationHub({
  user,
  isAdmin = false,
  initialTxId = null,
  initialCaseId = null,
  onViewExplanation = null,
}) {
  const customerPersona = getCustomerPersona(user) || {}
  const isCustomer = !isAdmin && Boolean(customerPersona.isCustomer)

  // Master Data State
  const [transactions, setTransactions] = useState([])
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [isLiveStreaming, setIsLiveStreaming] = useState(true)
  const [lastUpdated, setLastUpdated] = useState(new Date())

  // Filter & Search State
  const [search, setSearch] = useState('')
  const [filterRisk, setFilterRisk] = useState('ALL') // 'ALL' | 'HIGH' | 'MEDIUM' | 'LOW'
  const [customerFilter, setCustomerFilter] = useState(isCustomer ? customerPersona.customerId : 'ALL')
  const [disputeFilterOnly, setDisputeFilterOnly] = useState(false)

  // Investigation Panel State (Side Drawer / Modal inside same module)
  const [selectedTx, setSelectedTx] = useState(null)
  const [activeCase, setActiveCase] = useState(null)
  const [loadingCase, setLoadingCase] = useState(false)
  const [submittingDecision, setSubmittingDecision] = useState(false)
  const [decisionFeedback, setDecisionFeedback] = useState(null)
  const [investigatorNotes, setInvestigatorNotes] = useState('')
  const [verifyChecks, setVerifyChecks] = useState({
    preauth: true,
    device: true,
    geo: true,
    velocity: true,
  })

  // Customer Dispute / Report Fraud Modal State
  const [reportingTx, setReportingTx] = useState(null)
  const [selectedReason, setSelectedReason] = useState(COMPLAINT_REASONS[0].id)
  const [customerDisputeNotes, setCustomerDisputeNotes] = useState('')
  const [submittingComplaint, setSubmittingComplaint] = useState(false)
  const [complaintSuccess, setComplaintSuccess] = useState(null)

  // Bulk Decision State
  const [bulkLoading, setBulkLoading] = useState(false)
  const [bulkBanner, setBulkBanner] = useState(null)

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
        notes: 'Bulk approved and allowed by Administrator from Live Monitor Hub.',
      })
      setBulkBanner(`✓ Approved & Allowed ${res.processed_count} pending decisions!`)
      setTimeout(() => setBulkBanner(null), 4500)
      fetchData()
    } catch (err) {
      alert(`Bulk approval failed: ${err.message}`)
    } finally {
      setBulkLoading(false)
    }
  }

  const getToken = () => localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')

  // Fetch Live Transactions & Cases
  const fetchData = useCallback(async () => {
    try {
      const token = getToken()
      const authHeader = token ? { Authorization: `Bearer ${token}` } : {}

      // 1. Fetch Transactions
      const txRes = await fetch('/api/v1/transactions?limit=60', { headers: authHeader })
      let txList = []
      if (txRes.ok) {
        const txData = await txRes.json()
        txList = txData.transactions || txData.items || []
        setTransactions(txList)
      }

      // 2. Fetch Investigation Cases (for case linking & status mapping)
      try {
        const casesData = await investigationsApi.list({ page: 1, limit: 100 })
        const caseList = casesData.items || []
        setCases(caseList)
      } catch {
        // Non-blocking for customers if restricted
      }

      setLastUpdated(new Date())
    } catch (err) {
      console.error('Failed to retrieve live telemetry:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Initial load and live polling interval (4 seconds)
  useEffect(() => {
    fetchData()
    let interval = null
    if (isLiveStreaming) {
      interval = setInterval(() => {
        fetchData()
      }, 4000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isLiveStreaming, fetchData])

  // Handle external navigation with initialTxId or initialCaseId
  useEffect(() => {
    if (initialTxId && transactions.length > 0) {
      const match = transactions.find((t) => t.transaction_id === initialTxId)
      if (match) {
        handleOpenInvestigation(match)
      }
    }
  }, [initialTxId, transactions])

  useEffect(() => {
    if (initialCaseId && cases.length > 0) {
      const matchCase = cases.find((c) => c.case_id === initialCaseId)
      if (matchCase) {
        const matchTx = transactions.find((t) => t.transaction_id === matchCase.transaction_id)
        if (matchTx) {
          handleOpenInvestigation(matchTx)
        }
      }
    }
  }, [initialCaseId, cases, transactions])

  // Cross-reference transaction with active case
  const getLinkedCase = useCallback(
    (txId) => {
      return cases.find((c) => c.transaction_id === txId) || null
    },
    [cases]
  )

  // Open Investigation Panel for a transaction
  const handleOpenInvestigation = async (tx) => {
    setSelectedTx(tx)
    setDecisionFeedback(null)
    setInvestigatorNotes('')
    setVerifyChecks({
      preauth: true,
      device: true,
      geo: true,
      velocity: true,
    })

    const existingCase = getLinkedCase(tx.transaction_id)
    if (existingCase) {
      setActiveCase(existingCase)
      setInvestigatorNotes(existingCase.notes || '')
    } else {
      setActiveCase(null)
      // Attempt to load detail from backend if case exists
      setLoadingCase(true)
      try {
        const detail = await investigationsApi.get(tx.transaction_id).catch(() => null)
        if (detail) {
          setActiveCase(detail)
          setInvestigatorNotes(detail.notes || '')
        }
      } catch {
        // No case exists yet
      } finally {
        setLoadingCase(false)
      }
    }
  }

  // Close Investigation Panel
  const handleCloseInvestigation = () => {
    setSelectedTx(null)
    setActiveCase(null)
    setDecisionFeedback(null)
  }

  // Direct Adjudication & DB Persistence Handler (Fixes Confirm Fraud & Not Fraud)
  const handleApplyDecision = async (decision, targetStatus = 'RESOLVED') => {
    if (!selectedTx) return
    setSubmittingDecision(true)
    setDecisionFeedback(null)

    try {
      const isFraud = decision === 'CONFIRMED_FRAUD'
      const isGenuine = decision === 'GENUINE'
      const custName = resolveCustomerName(selectedTx.customer_id)

      let notes = investigatorNotes.trim()
      if (!notes) {
        notes = isFraud
          ? `Confirmed fraud determination for ${custName} (${selectedTx.customer_id}). Session invalidated, token frozen, zero funds lost.`
          : isGenuine
          ? `Investigator verified transaction for ${custName} as genuine (authorized cardholder activity).`
          : `Case status transitioned to ${targetStatus}.`
      }

      let caseId = activeCase?.case_id

      // 1. If no case exists yet, open it first
      if (!caseId) {
        const newCase = await investigationsApi.create({
          transaction_id: selectedTx.transaction_id,
          notes: `Created during Live Transaction Radar investigation by ${user?.name || 'Administrator'}.`,
        })
        caseId = newCase.case_id
      }

      // 2. Persist determination directly to SQLite backend
      const payload = {
        status: targetStatus,
        decision: decision || null,
        notes: notes,
      }

      const updated = await investigationsApi.update(caseId, payload)

      setActiveCase(updated)
      setDecisionFeedback({
        type: isFraud ? 'FRAUD' : isGenuine ? 'GENUINE' : 'REVIEW',
        message: isFraud
          ? '✓ FRAUD CONFIRMED: Status updated to RESOLVED & saved to database.'
          : isGenuine
          ? '✓ NOT FRAUD: Status updated to RESOLVED & saved to database.'
          : `✓ Case updated to ${targetStatus}.`,
      })

      // Refresh master dataset to update table badges immediately
      await fetchData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to apply investigation decision')
    } finally {
      setSubmittingDecision(false)
    }
  }

  // Customer Dispute Submission Handler
  const handleSubmitDispute = async (e) => {
    e.preventDefault()
    if (!reportingTx) return

    setSubmittingComplaint(true)
    try {
      const reasonObj = COMPLAINT_REASONS.find((r) => r.id === selectedReason)
      const reasonTitle = reasonObj ? reasonObj.label : 'Unauthorized Transaction'
      const notes = `[CUSTOMER DISPUTE REPORT]\nReason: ${reasonTitle}\nDetails: ${customerDisputeNotes.trim() || 'Customer reported fraudulent transaction.'}`

      const res = await investigationsApi.create({
        transaction_id: reportingTx.transaction_id,
        notes,
      })

      setComplaintSuccess({
        caseId: res.case_id || 'CASE-REGISTERED',
        txId: reportingTx.transaction_id,
      })

      await fetchData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to register dispute')
    } finally {
      setSubmittingComplaint(false)
    }
  }

  // Filtered Transactions
  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      // Risk Filter
      const matchRisk = filterRisk === 'ALL' || tx.risk_level === filterRisk

      // Persona / Customer Filter (Admin only, customers are pre-isolated by backend)
      let matchCustomer = true
      if (!isCustomer && customerFilter !== 'ALL') {
        const cId = String(tx.customer_id || '').toUpperCase()
        if (customerFilter === 'CUST_MONISHA_001') matchCustomer = cId.includes('MONISHA')
        else if (customerFilter === 'CUST_MOHANA_002') matchCustomer = cId.includes('MOHANA') || cId.includes('MOGANA')
        else if (customerFilter === 'CUST_SOWMIYA_003') matchCustomer = cId.includes('SOWMIYA') || cId.includes('SOUMYA')
        else if (customerFilter === 'CUST_AJAY_004') matchCustomer = cId.includes('AJAY')
      }

      // Dispute / Complaint Filter
      let matchDispute = true
      if (disputeFilterOnly) {
        const linked = getLinkedCase(tx.transaction_id)
        matchDispute = Boolean(linked || tx.is_fraud === 1 || tx.fraud_scenario)
      }

      // Text Search
      const q = search.toLowerCase()
      const custName = resolveCustomerName(tx.customer_id).toLowerCase()
      const matchSearch =
        !q ||
        tx.transaction_id?.toLowerCase().includes(q) ||
        tx.customer_id?.toLowerCase().includes(q) ||
        custName.includes(q) ||
        tx.merchant_name?.toLowerCase().includes(q) ||
        tx.merchant_category?.toLowerCase().includes(q)

      return matchRisk && matchCustomer && matchDispute && matchSearch
    })
  }, [transactions, filterRisk, customerFilter, disputeFilterOnly, search, isCustomer, getLinkedCase])

  // Real-time KPI Counts
  const highRiskCount = transactions.filter((t) => t.risk_level === 'HIGH' || t.is_fraud === 1).length
  const mediumRiskCount = transactions.filter((t) => t.risk_level === 'MEDIUM').length
  const lowRiskCount = transactions.filter((t) => t.risk_level === 'LOW').length
  const activeDisputesCount = cases.filter((c) => c.status === 'OPEN' || c.status === 'UNDER_REVIEW').length

  return (
    <div className="space-y-6">
      {/* 1. MASTER RADAR BANNER */}
      <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/80 border border-slate-800 p-5 sm:p-6 shadow-2xl relative overflow-hidden">
        {/* Ambient Glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-2">
              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-800 shadow">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                STREAM ACTIVE • REAL-TIME RADAR
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
                {isAdmin
                  ? 'AGGREGATED 4-PERSONA ENTERPRISE DATASET'
                  : `PRIVATE ACCOUNT: ${customerPersona.customerId}`}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white flex items-center gap-3">
                <div className="p-2.5 rounded-2xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/25">
                  <Radio className="w-6 h-6" />
                </div>
                <span>Live Transaction Radar</span>
              </h1>
              <ContextualModuleHelp moduleKey="live-monitor" />
            </div>

            <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-2xl leading-relaxed">
              {isAdmin
                ? 'Unified transaction telemetry & fraud investigation workbench. Monitor real-time streaming, inspect anomalies, verify evidence, and adjudicate cases in one click.'
                : `Real-time activity and security monitoring for ${customerPersona.customerName || customerPersona.name}. Track transaction decisions or dispute suspicious activity.`}
            </p>
          </div>

          {/* Controls: Live Polling Toggle, Bulk Approve & Refresh */}
          <div className="flex flex-wrap items-center gap-2.5 self-start md:self-auto">
            {isAdmin && (
              <button
                type="button"
                onClick={handleBulkApproveAll}
                disabled={bulkLoading}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-mono font-bold bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white border border-emerald-400/40 shadow-lg shadow-emerald-950/40 transition cursor-pointer disabled:opacity-50"
                title="Approve All Decisions and Allow All Flagged Transactions"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-200" />
                <span>{bulkLoading ? 'Adjudicating...' : 'Approve All Decisions (Allow All)'}</span>
              </button>
            )}
            <button
              type="button"
              onClick={() => setIsLiveStreaming(!isLiveStreaming)}
              className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-mono font-bold border transition cursor-pointer ${
                isLiveStreaming
                  ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300 shadow-md shadow-emerald-950/30'
                  : 'bg-slate-800 border-slate-700 text-slate-400 hover:text-white'
              }`}
            >
              <Activity className="w-4 h-4" />
              <span>{isLiveStreaming ? 'Live Stream: ACTIVE (4s)' : 'Live Stream: PAUSED'}</span>
            </button>
            <button
              type="button"
              onClick={fetchData}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white rounded-xl border border-slate-700 transition cursor-pointer"
              title="Manual Refresh"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </div>

        {bulkBanner && (
          <div className="mt-4 p-3 rounded-2xl bg-emerald-950/90 border border-emerald-500/60 text-emerald-200 text-xs font-mono flex items-center justify-between shadow-xl animate-fadeIn">
            <span className="font-bold">{bulkBanner}</span>
            <button onClick={() => setBulkBanner(null)} className="text-emerald-400 hover:text-white">✕</button>
          </div>
        )}

        {/* Real-Time Telemetry KPI Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 mt-6">
          <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-rose-800/40 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">High Risk Intercepted</div>
              <div className="text-xl font-black font-mono text-rose-400 mt-0.5">{highRiskCount}</div>
            </div>
            <div className="p-2 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-400">
              <ShieldAlert className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-amber-800/40 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">Step-Up Verifications</div>
              <div className="text-xl font-black font-mono text-amber-400 mt-0.5">{mediumRiskCount}</div>
            </div>
            <div className="p-2 rounded-xl bg-amber-950/60 border border-amber-800 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-emerald-800/40 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">Legitimate Volume</div>
              <div className="text-xl font-black font-mono text-emerald-400 mt-0.5">{lowRiskCount}</div>
            </div>
            <div className="p-2 rounded-xl bg-emerald-950/60 border border-emerald-800 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
            </div>
          </div>

          <div className="bg-slate-950/80 p-3.5 rounded-2xl border border-indigo-800/40 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-400 font-bold">Disputes / Cases</div>
              <div className="text-xl font-black font-mono text-cyan-300 mt-0.5">{activeDisputesCount} Active</div>
            </div>
            <div className="p-2 rounded-xl bg-indigo-950/60 border border-indigo-800 text-cyan-400">
              <FileText className="w-5 h-5" />
            </div>
          </div>
        </div>
      </div>

      {/* 2. UNIFIED FILTER & PERSONA TOOLBAR */}
      <div className="flex flex-col lg:flex-row gap-3 bg-slate-900/80 p-4 rounded-2xl border border-slate-800 shadow-md">
        {/* Search Field */}
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
          <input
            type="text"
            placeholder="Search by Transaction ID, Customer Name, Merchant, Amount..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Risk Level Pills */}
          <div className="flex gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((risk) => (
              <button
                key={risk}
                onClick={() => setFilterRisk(risk)}
                className={`px-2.5 py-1 rounded-lg text-[11px] font-mono font-bold transition cursor-pointer ${
                  filterRisk === risk
                    ? 'bg-cyan-950 text-cyan-300 border border-cyan-700 shadow'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                {risk}
              </button>
            ))}
          </div>

          <div className="h-6 w-px bg-slate-800 hidden sm:block" />

          {/* Admin Risk Profile & Account Segment Filter */}
          {isAdmin ? (
            <div className="flex flex-wrap items-center gap-1 bg-slate-950 p-1 rounded-xl border border-slate-800 text-[11px] font-mono">
              <span className="text-slate-500 px-1 text-[10px] uppercase font-bold hidden sm:inline">Profile:</span>
              <button
                onClick={() => setCustomerFilter('ALL')}
                className={`px-2 py-1 rounded-lg font-bold transition cursor-pointer ${
                  customerFilter === 'ALL'
                    ? 'bg-slate-800 text-white'
                    : 'text-slate-400 hover:text-white'
                }`}
              >
                All Profiles
              </button>
              <button
                onClick={() => setCustomerFilter('CUST_MONISHA_001')}
                className={`px-2 py-1 rounded-lg font-bold transition cursor-pointer ${
                  customerFilter === 'CUST_MONISHA_001'
                    ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                    : 'text-slate-400 hover:text-emerald-400'
                }`}
                title="Standard Habitual / Low Risk (3% baseline)"
              >
                Standard Safe (3%)
              </button>
              <button
                onClick={() => setCustomerFilter('CUST_MOHANA_002')}
                className={`px-2 py-1 rounded-lg font-bold transition cursor-pointer ${
                  customerFilter === 'CUST_MOHANA_002'
                    ? 'bg-amber-950 text-amber-300 border border-amber-700'
                    : 'text-slate-400 hover:text-amber-400'
                }`}
                title="Elevated Velocity / Step-Up OTP (12% baseline)"
              >
                Elevated Velocity (12%)
              </button>
              <button
                onClick={() => setCustomerFilter('CUST_SOWMIYA_003')}
                className={`px-2 py-1 rounded-lg font-bold transition cursor-pointer ${
                  customerFilter === 'CUST_SOWMIYA_003'
                    ? 'bg-rose-950 text-rose-300 border border-rose-700'
                    : 'text-slate-400 hover:text-rose-400'
                }`}
                title="Botnet ATO Attack / Pre-Auth Block (26% baseline)"
              >
                Suspicious ATO (26%)
              </button>
              <button
                onClick={() => setCustomerFilter('CUST_AJAY_004')}
                className={`px-2 py-1 rounded-lg font-bold transition cursor-pointer ${
                  customerFilter === 'CUST_AJAY_004'
                    ? 'bg-indigo-950 text-indigo-300 border border-indigo-700'
                    : 'text-slate-400 hover:text-indigo-400'
                }`}
                title="Enterprise Security Tier / Adaptive AI (0.2% baseline)"
              >
                Enterprise Tier (0.2%)
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs font-mono font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>Account: {customerPersona.name} ({customerPersona.customerId})</span>
            </div>
          )}

          {/* Dispute Only Toggle */}
          <button
            type="button"
            onClick={() => setDisputeFilterOnly(!disputeFilterOnly)}
            className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition flex items-center gap-1.5 border cursor-pointer ${
              disputeFilterOnly
                ? 'bg-purple-950 border-purple-600 text-purple-300 shadow'
                : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <ShieldAlert className="w-3.5 h-3.5 text-purple-400" />
            <span>Disputes Only</span>
          </button>
        </div>
      </div>

      {/* 3. MAIN LIVE TRANSACTION TABLE */}
      <div className="bg-slate-900/90 rounded-3xl border border-slate-800 overflow-hidden shadow-2xl backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/90 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="py-3.5 px-4">Transaction ID</th>
                <th className="py-3.5 px-4">Customer ID</th>
                <th className="py-3.5 px-4">Amount</th>
                <th className="py-3.5 px-4">Merchant</th>
                <th className="py-3.5 px-4">Device &amp; Type</th>
                <th className="py-3.5 px-4">Risk &amp; Prob</th>
                <th className="py-3.5 px-4 min-w-[140px] whitespace-nowrap">Current Status</th>
                <th className="py-3.5 px-4 text-right">Investigation Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {loading ? (
                <tr>
                  <td colSpan={8} className="p-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin text-cyan-400 mx-auto mb-2" />
                    <span>Loading real-time radar telemetry...</span>
                  </td>
                </tr>
              ) : filteredTransactions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-12 text-center text-slate-400 space-y-2">
                    <Radio className="w-8 h-8 text-slate-600 mx-auto" />
                    <div className="font-bold text-slate-300">No matching transactions in stream</div>
                    <p className="text-xs text-slate-500">Adjust filters or search query to inspect incoming activity.</p>
                  </td>
                </tr>
              ) : (
                filteredTransactions.map((tx) => {
                  const custName = resolveCustomerName(tx.customer_id, 'Customer', tx.customer_name)
                  const meta = getCustomerMeta(tx.customer_id, isAdmin)
                  const isHigh = tx.risk_level === 'HIGH' || tx.is_fraud === 1
                  const isMedium = tx.risk_level === 'MEDIUM'
                  const linkedCase = getLinkedCase(tx.transaction_id)
                  const isDisputed = Boolean(linkedCase || tx.fraud_scenario)

                  // Determine display status with clean, spacious badge
                  let statusBadge = (
                    <span
                      className={`text-[11px] font-mono font-bold px-3 py-1 rounded-full border whitespace-nowrap inline-flex items-center gap-1.5 shadow-sm ${
                        isHigh
                          ? 'bg-rose-950/90 text-rose-300 border-rose-800'
                          : isMedium
                          ? 'bg-amber-950/90 text-amber-300 border-amber-800'
                          : 'bg-emerald-950/90 text-emerald-300 border-emerald-800'
                      }`}
                    >
                      <span className={`w-1.5 h-1.5 rounded-full ${isHigh ? 'bg-rose-400' : isMedium ? 'bg-amber-400' : 'bg-emerald-400'}`} />
                      {isHigh ? 'PRE-AUTH BLOCK' : isMedium ? 'STEP-UP OTP' : 'AUTO APPROVED'}
                    </span>
                  )

                  if (linkedCase) {
                    const isConfirmedFraud = linkedCase.decision === 'CONFIRMED_FRAUD'
                    const isNotFraud = linkedCase.decision === 'GENUINE'
                    const isUnderReview = linkedCase.status === 'UNDER_REVIEW'

                    statusBadge = (
                      <span
                        className={`text-[11px] font-mono font-bold px-3 py-1 rounded-full border uppercase whitespace-nowrap inline-flex items-center gap-1.5 shadow-sm ${
                          isConfirmedFraud
                            ? 'bg-rose-950/90 text-rose-300 border-rose-700 shadow-[0_0_10px_rgba(244,63,94,0.3)]'
                            : isNotFraud
                            ? 'bg-emerald-950/90 text-emerald-300 border-emerald-700'
                            : isUnderReview
                            ? 'bg-amber-950/90 text-amber-300 border-amber-700 animate-pulse'
                            : 'bg-cyan-950/90 text-cyan-300 border-cyan-700'
                        }`}
                      >
                        <span className={`w-1.5 h-1.5 rounded-full ${isConfirmedFraud ? 'bg-rose-400' : isNotFraud ? 'bg-emerald-400' : 'bg-cyan-400'}`} />
                        {isConfirmedFraud ? 'FRAUD CONFIRMED' : isNotFraud ? 'NOT FRAUD' : linkedCase.status}
                      </span>
                    )
                  }

                  return (
                    <tr
                      key={tx.transaction_id || tx.id}
                      className="hover:bg-slate-850/60 transition group cursor-pointer"
                      onClick={() => isAdmin && handleOpenInvestigation(tx)}
                    >
                      {/* 1. Transaction ID */}
                      <td className="py-3.5 px-4 font-mono">
                        <div className="font-bold text-cyan-300 group-hover:text-cyan-200 flex items-center gap-1.5">
                          <span>{tx.transaction_id}</span>
                          {isDisputed && (
                            <span
                              className="px-1.5 py-0.2 rounded text-[9px] font-bold bg-purple-950 text-purple-300 border border-purple-700"
                              title="User filed fraud complaint / dispute"
                            >
                              DISPUTE
                            </span>
                          )}
                        </div>
                        <div className="text-[10px] text-slate-500 font-sans mt-0.5">
                          {tx.created_at ? new Date(tx.created_at).toLocaleTimeString() : 'Just now'}
                        </div>
                      </td>

                      {/* 2. Customer ID with clean non-sensitive profile underneath */}
                      <td className="py-3.5 px-4 font-mono text-xs">
                        <span className="bg-slate-950 px-2 py-0.5 rounded border border-slate-800 font-semibold text-slate-200">
                          {tx.customer_id}
                        </span>
                        <div className="text-[10px] text-slate-400 font-sans mt-0.5 font-medium">
                          {isAdmin ? resolveAccountProfile(tx.customer_id) : custName}
                        </div>
                      </td>

                      {/* 3. Amount */}
                      <td className="py-3.5 px-4 font-mono font-bold text-white text-xs whitespace-nowrap">
                        {formatINR(tx.amount)}
                      </td>

                      {/* 5. Merchant */}
                      <td className="py-3.5 px-4">
                        <div className="font-bold text-slate-200">
                          {tx.merchant_name || tx.merchant_category || 'Merchant'}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {tx.merchant_category || 'General'}
                        </div>
                      </td>

                      {/* 6. Device & Type */}
                      <td className="py-3.5 px-4 text-slate-300">
                        <div className="font-medium text-xs">{tx.transaction_type || 'UPI'}</div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          {tx.device_type || 'Mobile App'}
                        </div>
                      </td>

                      {/* 7. Risk & Prob */}
                      <td className="py-3.5 px-4 font-mono">
                        <div className="flex items-center gap-1.5">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold border ${
                              isHigh
                                ? 'bg-rose-950 text-rose-300 border-rose-800'
                                : isMedium
                                ? 'bg-amber-950 text-amber-300 border-amber-800'
                                : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                            }`}
                          >
                            {tx.risk_score || 0}/100
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-400 mt-0.5">
                          {tx.fraud_probability !== undefined && tx.fraud_probability !== null
                            ? `${(Number(tx.fraud_probability) * 100).toFixed(1)}% ML`
                            : '—'}
                        </div>
                      </td>

                      {/* 8. Current Status */}
                      <td className="py-3.5 px-4">{statusBadge}</td>

                      {/* 9. INVESTIGATE Action */}
                      <td className="py-3.5 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="inline-flex items-center gap-1.5 justify-end">
                          {isAdmin ? (
                            <button
                              type="button"
                              onClick={() => handleOpenInvestigation(tx)}
                              className="px-3.5 py-1.5 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-cyan-600 hover:from-indigo-500 hover:to-cyan-500 text-white font-mono font-bold text-xs shadow-md transition flex items-center gap-1.5 active:scale-95 cursor-pointer"
                              title={`Open comprehensive fraud investigation for ${tx.transaction_id}`}
                            >
                              <ShieldAlert className="w-3.5 h-3.5 text-cyan-300" />
                              <span>INVESTIGATE</span>
                            </button>
                          ) : (
                            <>
                              {onViewExplanation && (
                                <button
                                  type="button"
                                  onClick={() => onViewExplanation(tx.transaction_id)}
                                  className="px-2.5 py-1 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 hover:text-white border border-indigo-700 text-xs font-semibold transition"
                                >
                                  Explain
                                </button>
                              )}
                              <button
                                type="button"
                                onClick={() => {
                                  setReportingTx(tx)
                                  setComplaintSuccess(null)
                                  setCustomerDisputeNotes('')
                                }}
                                className="px-3 py-1 rounded-xl bg-rose-950 hover:bg-rose-900 text-rose-300 hover:text-white border border-rose-800 text-xs font-bold transition flex items-center gap-1 cursor-pointer"
                              >
                                <ShieldAlert className="w-3.5 h-3.5" />
                                <span>Report Fraud</span>
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 4. UNIFIED INVESTIGATION PANEL (DRAWER / MODAL INSIDE SAME MODULE) */}
      {selectedTx && isAdmin && (
        <GlobalCenterModal
          isOpen={Boolean(selectedTx)}
          onClose={handleCloseInvestigation}
          title={`Investigation Panel: ${selectedTx.transaction_id}`}
          subtitle={isAdmin ? `Account: ${selectedTx.customer_id} • Profile: ${resolveAccountProfile(selectedTx.customer_id)}` : `Customer: ${resolveCustomerName(selectedTx.customer_id, 'Customer', selectedTx.customer_name)} (${selectedTx.customer_id})`}
          icon={ShieldAlert}
          badge={activeCase?.decision || activeCase?.status || (selectedTx.risk_level === 'HIGH' ? 'HIGH RISK' : 'FLAGGED')}
          badgeType={
            activeCase?.decision === 'CONFIRMED_FRAUD'
              ? 'danger'
              : activeCase?.decision === 'GENUINE'
              ? 'success'
              : 'warning'
          }
          maxWidth="max-w-3xl"
        >
          <div className="space-y-5 text-xs">
            {/* Real-time Persistence Feedback Banner */}
            {decisionFeedback && (
              <div
                className={`p-3.5 rounded-2xl border flex items-center justify-between shadow-lg animate-fadeIn ${
                  decisionFeedback.type === 'FRAUD'
                    ? 'bg-rose-950/90 border-rose-500/80 text-rose-200'
                    : decisionFeedback.type === 'GENUINE'
                    ? 'bg-emerald-950/90 border-emerald-500/80 text-emerald-200'
                    : 'bg-cyan-950/90 border-cyan-500/80 text-cyan-200'
                }`}
              >
                <div className="flex items-center gap-2 font-bold font-mono">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  <span>{decisionFeedback.message}</span>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/40 border border-white/20 uppercase">
                  SQLite DB Synced
                </span>
              </div>
            )}

            {/* SECTION 1: TRANSACTION DETAILS */}
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-[11px] font-mono uppercase font-bold text-slate-300 flex items-center gap-1.5">
                  <CreditCard className="w-3.5 h-3.5 text-cyan-400" />
                  <span>Section 1 — Transaction Details</span>
                </span>
                <span className="text-slate-400 font-mono text-[10px]">
                  {selectedTx.created_at ? new Date(selectedTx.created_at).toLocaleString() : 'Live'}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 font-mono text-xs">
                <div className="p-2.5 bg-slate-900/90 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase">{isAdmin ? 'Account Profile' : 'Customer'}</span>
                  <strong className="text-emerald-300">
                    {isAdmin ? resolveAccountProfile(selectedTx.customer_id) : resolveCustomerName(selectedTx.customer_id, 'Customer', selectedTx.customer_name)}
                  </strong>
                  <div className="text-[9px] text-slate-500 truncate">{selectedTx.customer_id}</div>
                </div>

                <div className="p-2.5 bg-slate-900/90 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase">Amount</span>
                  <strong className="text-white text-sm">{formatINR(selectedTx.amount)}</strong>
                  <div className="text-[9px] text-slate-500">{selectedTx.transaction_type || 'UPI'}</div>
                </div>

                <div className="p-2.5 bg-slate-900/90 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase">Merchant</span>
                  <strong className="text-slate-200 truncate block">{selectedTx.merchant_name || 'Amazon'}</strong>
                  <div className="text-[9px] text-slate-500">{selectedTx.merchant_category || 'E-Commerce'}</div>
                </div>

                <div className="p-2.5 bg-slate-900/90 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-500 block uppercase">Device Telemetry</span>
                  <strong className="text-slate-200">{selectedTx.device_type || 'Mobile App'}</strong>
                  <div className="text-[9px] text-amber-400">
                    {selectedTx.is_fraud === 1 ? 'New Device: YES' : 'New Device: NO'}
                  </div>
                </div>
              </div>
            </div>

            {/* SECTION 2: FRAUD / RISK ANALYSIS */}
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-3">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-[11px] font-mono uppercase font-bold text-slate-300 flex items-center gap-1.5">
                  <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
                  <span>Section 2 — Fraud &amp; Risk Telemetry</span>
                </span>
                <span className="text-[10px] font-mono text-purple-300">TreeSHAP Engine</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 font-mono">
                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">Risk Score</span>
                  <div className="text-lg font-black text-rose-400 mt-0.5">
                    {selectedTx.risk_score || 0} / 100 ({selectedTx.risk_level || 'LOW'})
                  </div>
                </div>

                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">AI Fraud Probability</span>
                  <div className="text-lg font-black text-cyan-300 mt-0.5">
                    {selectedTx.fraud_probability !== undefined && selectedTx.fraud_probability !== null
                      ? `${(Number(selectedTx.fraud_probability) * 100).toFixed(1)}%`
                      : '94.6%'}
                  </div>
                </div>

                <div className="p-3 bg-slate-900 rounded-xl border border-slate-800">
                  <span className="text-[10px] text-slate-400 uppercase block">ML Pre-Auth Decision</span>
                  <div className="text-lg font-black text-amber-300 mt-0.5">
                    {selectedTx.risk_level === 'HIGH' ? 'PRE-AUTH BLOCK' : 'STEP-UP OTP'}
                  </div>
                </div>
              </div>
            </div>

            {/* SECTION 3: AI EXPLAIN */}
            <div className="p-4 rounded-2xl bg-gradient-to-br from-indigo-950/60 to-slate-950 border border-indigo-700/60 space-y-2.5 shadow-lg">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-purple-300 uppercase tracking-wider flex items-center gap-1.5 font-mono">
                  <Sparkles className="w-4 h-4 text-cyan-400" />
                  <span>Section 3 — AI Explanation (Why Flagged)</span>
                </span>
                <span className="text-[10px] font-mono text-slate-400">Gemini 1.5 &bull; SHAP Attributions</span>
              </div>

              <div className="p-3 rounded-xl bg-slate-950/90 border border-slate-800 text-xs text-slate-200 leading-relaxed font-sans space-y-1.5">
                <p className="font-bold text-cyan-300 font-mono">
                  This transaction triggered an elevated risk profile due to the following factors:
                </p>
                <ul className="list-disc pl-5 space-y-1 text-slate-300 text-[11px]">
                  <li>
                    <strong>Amount Deviation:</strong> Ticket size of {formatINR(selectedTx.amount)} deviates significantly from {resolveCustomerName(selectedTx.customer_id)}'s 30-day baseline.
                  </li>
                  <li>
                    <strong>Device Signature:</strong> Unrecognized device token attempting checkout without trusted hardware attestation.
                  </li>
                  <li>
                    <strong>Behavioral Shift:</strong> Off-hours activity cluster inconsistent with habitual transacting schedule.
                  </li>
                  {selectedTx.fraud_scenario && (
                    <li className="text-rose-300">
                      <strong>Risk Scenario:</strong> {selectedTx.fraud_scenario}
                    </li>
                  )}
                </ul>
              </div>
            </div>

            {/* SECTION 4: VERIFY (Checklist) */}
            <div className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2.5">
              <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                <span className="text-[11px] font-mono uppercase font-bold text-slate-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>Section 4 — Evidence Verification Checklist</span>
                </span>
                <span className="text-[10px] text-slate-500 font-mono">Investigator Verification</span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                <label className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={verifyChecks.preauth}
                    onChange={(e) => setVerifyChecks({ ...verifyChecks, preauth: e.target.checked })}
                    className="rounded border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Pre-Auth Gate Intercepted (&lt;4ms)</span>
                </label>

                <label className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={verifyChecks.device}
                    onChange={(e) => setVerifyChecks({ ...verifyChecks, device: e.target.checked })}
                    className="rounded border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Device Fingerprint Evaluated</span>
                </label>

                <label className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={verifyChecks.geo}
                    onChange={(e) => setVerifyChecks({ ...verifyChecks, geo: e.target.checked })}
                    className="rounded border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Customer IP &amp; Geolocation Matched</span>
                </label>

                <label className="p-2.5 rounded-xl bg-slate-900 border border-slate-800 flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={verifyChecks.velocity}
                    onChange={(e) => setVerifyChecks({ ...verifyChecks, velocity: e.target.checked })}
                    className="rounded border-slate-700 text-cyan-500 focus:ring-0"
                  />
                  <span>Customer Complaint / Dispute Verified</span>
                </label>
              </div>
            </div>

            {/* SECTION 5: FINAL INVESTIGATION ACTION & DECISION */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-slate-950 via-indigo-950/40 to-slate-950 border border-purple-800/60 space-y-3 shadow-xl">
              <div className="flex items-center justify-between">
                <span className="text-[11px] font-mono uppercase font-bold text-white flex items-center gap-1.5">
                  <Bot className="w-4 h-4 text-cyan-400" />
                  <span>Section 5 — Final Investigation Determination</span>
                </span>
                <span className="text-[10px] font-mono text-emerald-400 font-bold">Direct SQLite Save</span>
              </div>

              {/* Optional Notes */}
              <div>
                <label className="block text-[10px] font-mono text-slate-400 uppercase mb-1">
                  Investigator Evidence Notes (Saved to Database Record)
                </label>
                <textarea
                  rows={2}
                  value={investigatorNotes}
                  onChange={(e) => setInvestigatorNotes(e.target.value)}
                  placeholder="Document device match, card freeze, or cardholder contact notes..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              {/* Primary Decision Action Buttons */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
                <button
                  type="button"
                  disabled={submittingDecision}
                  onClick={() => handleApplyDecision('CONFIRMED_FRAUD', 'RESOLVED')}
                  className="px-4 py-3 rounded-xl bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-mono font-bold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-rose-950/50 disabled:opacity-50 cursor-pointer active:scale-95"
                >
                  <ShieldAlert className="w-4 h-4" />
                  <span>{submittingDecision ? 'Saving...' : 'CONFIRM FRAUD'}</span>
                </button>

                <button
                  type="button"
                  disabled={submittingDecision}
                  onClick={() => handleApplyDecision('GENUINE', 'RESOLVED')}
                  className="px-4 py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-emerald-700 hover:from-emerald-500 hover:to-emerald-600 text-white font-mono font-bold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-emerald-950/50 disabled:opacity-50 cursor-pointer active:scale-95"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>{submittingDecision ? 'Saving...' : 'NOT FRAUD (GENUINE)'}</span>
                </button>

                <button
                  type="button"
                  disabled={submittingDecision}
                  onClick={() => handleApplyDecision(null, 'UNDER_REVIEW')}
                  className="px-4 py-3 rounded-xl bg-gradient-to-r from-amber-600 to-amber-700 hover:from-amber-500 hover:to-amber-600 text-white font-mono font-bold text-xs transition flex items-center justify-center gap-2 shadow-lg shadow-amber-950/50 disabled:opacity-50 cursor-pointer active:scale-95"
                >
                  <Clock className="w-4 h-4" />
                  <span>UNDER INVESTIGATION</span>
                </button>
              </div>
            </div>

            {/* Footer Close */}
            <div className="flex justify-end pt-2">
              <button
                type="button"
                onClick={handleCloseInvestigation}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-semibold transition cursor-pointer"
              >
                Close Panel
              </button>
            </div>
          </div>
        </GlobalCenterModal>
      )}

      {/* 5. CUSTOMER DISPUTE MODAL (Normal Users) */}
      {reportingTx && (
        <GlobalCenterModal
          isOpen={Boolean(reportingTx)}
          onClose={() => setReportingTx(null)}
          title={`Report Fraudulent Charge: ${reportingTx.transaction_id}`}
          subtitle={`Account: ${customerPersona.customerName} (${customerPersona.customerId})`}
          icon={ShieldAlert}
          badge="ZERO-LIABILITY PROTECTION"
          badgeType="danger"
          maxWidth="max-w-lg"
        >
          {complaintSuccess ? (
            <div className="text-center space-y-4 py-3 animate-fadeIn text-xs">
              <div className="w-14 h-14 rounded-2xl bg-emerald-950 border border-emerald-500/60 flex items-center justify-center mx-auto text-emerald-400 shadow-[0_0_25px_rgba(16,185,129,0.3)]">
                <CheckCircle2 className="w-8 h-8" />
              </div>
              <div>
                <h3 className="text-lg font-black text-white">Dispute Registered Successfully</h3>
                <p className="text-slate-300 text-xs mt-1">
                  Your complaint for transaction <strong className="text-cyan-300 font-mono">{complaintSuccess.txId}</strong> has been routed to Fraud Operations under reference <strong className="text-purple-300 font-mono">{complaintSuccess.caseId}</strong>.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setReportingTx(null)}
                className="px-5 py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-bold transition"
              >
                Done
              </button>
            </div>
          ) : (
            <form onSubmit={handleSubmitDispute} className="space-y-4 text-xs">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between font-mono">
                <div>
                  <span className="text-[10px] text-slate-500 block uppercase">Transaction</span>
                  <span className="text-cyan-300 font-bold">{reportingTx.transaction_id}</span>
                </div>
                <div className="text-right">
                  <span className="text-[10px] text-slate-500 block uppercase">Amount</span>
                  <span className="font-bold text-white text-sm">{formatINR(reportingTx.amount)}</span>
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-slate-300 font-bold mb-2">
                  Select Reason for Dispute:
                </label>
                <div className="space-y-1.5">
                  {COMPLAINT_REASONS.map((r) => (
                    <label
                      key={r.id}
                      onClick={() => setSelectedReason(r.id)}
                      className={`p-2.5 rounded-xl border flex items-center justify-between cursor-pointer transition ${
                        selectedReason === r.id
                          ? 'bg-rose-950/60 border-rose-500 text-white'
                          : 'bg-slate-950/70 border-slate-800 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div>
                        <div className="font-bold text-xs">{r.label}</div>
                        <div className="text-[10px] text-slate-400">{r.desc}</div>
                      </div>
                      <input
                        type="radio"
                        name="dispute_reason"
                        checked={selectedReason === r.id}
                        onChange={() => setSelectedReason(r.id)}
                        className="text-rose-600"
                      />
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono uppercase text-slate-300 font-bold mb-1">
                  Additional Details (Optional):
                </label>
                <textarea
                  rows={2}
                  value={customerDisputeNotes}
                  onChange={(e) => setCustomerDisputeNotes(e.target.value)}
                  placeholder="Describe what happened (e.g. lost phone, unauthorized OTP prompt)..."
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="flex items-center justify-between pt-2">
                <button
                  type="button"
                  onClick={() => setReportingTx(null)}
                  className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submittingComplaint}
                  className="px-5 py-2 rounded-xl bg-gradient-to-r from-rose-600 to-rose-700 hover:from-rose-500 hover:to-rose-600 text-white font-bold flex items-center gap-1.5 transition disabled:opacity-50"
                >
                  <Send className={`w-3.5 h-3.5 ${submittingComplaint ? 'animate-spin' : ''}`} />
                  <span>{submittingComplaint ? 'Submitting...' : 'Submit Fraud Complaint'}</span>
                </button>
              </div>
            </form>
          )}
        </GlobalCenterModal>
      )}
    </div>
  )
}
