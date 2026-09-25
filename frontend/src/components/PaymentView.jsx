import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import {
  CreditCard,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Lock,
  ArrowRight,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  RefreshCw,
  Sliders,
  Smartphone,
  Globe,
  HelpCircle,
  ChevronRight,
  ChevronDown,
  UserCheck,
  Wallet,
  UserPlus,
  Send,
  Zap,
  Info,
  IndianRupee,
  Search,
  Check,
  Store,
  MapPin,
} from 'lucide-react'
import { paymentApi } from '../services/api'
import { formatINR } from '../utils/formatters'
import { getCustomerPersona } from '../utils/customerHelper'
import MobileSecurityApprovalModal from './MobileSecurityApprovalModal'

export default function PaymentView({
  user,
  isAdmin,
  onViewExplanation,
  onNavigateToInvestigations,
  onSelectTransaction,
  initialPreset = 'scenario_monisha_safe',
}) {
  // Preset Indian scenarios aligned with student personas
  const presets = [
    {
      id: 'scenario_monisha_safe',
      title: '1. Monisha: Habitual Grocery (₹1,250)',
      badge: 'MONISHA (3%) → SAFE ALLOW',
      badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
      description: 'Routine ₹1,250 grocery payment at NovaMart Fresh from trusted iPhone in Chennai. Clean baseline (3% fraud rate) -> Auto-Approved.',
      data: {
        customer_id: 'CUST_MONISHA_001',
        amount: 1250.0,
        currency: 'INR',
        merchant_name: 'NovaMart Fresh',
        merchant_category: 'Grocery & Supermarket',
        beneficiary_name: 'NovaMart Fresh',
        payment_method: 'upi',
        device_type: 'mobile_ios',
        location: 'Chennai',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },
    {
      id: 'scenario_mohana_review',
      title: '2. Mohana: Suspicious Device & Region (₹14,500)',
      badge: 'MOHANA (12%) → STEP-UP OTP REVIEW',
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
      description: 'Moderate ₹14,500 electronics purchase via unfamiliar web browser with cross-city distance. Risk 45/100 -> Triggers Step-Up OTP Verification.',
      data: {
        customer_id: 'CUST_MOHANA_002',
        amount: 14500.0,
        currency: 'INR',
        merchant_name: 'CircuitBay Electronics',
        merchant_category: 'Consumer Electronics',
        beneficiary_name: 'CircuitBay Electronics',
        payment_method: 'credit_card',
        device_type: 'web_browser',
        location: 'Salem',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 1,
      },
    },
    {
      id: 'scenario_sowmiya_block',
      title: '3. Sowmiya: Botnet Account Takeover (₹75,000)',
      badge: 'SOWMIYA (26%) → CRITICAL BLOCK',
      badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
      description: 'High-value ₹75,000 gold jewellery attempt at 2:30 AM from automated bot emulator in Lagos with foreign IP proxy. Instant Pre-Auth Block!',
      data: {
        customer_id: 'CUST_SOWMIYA_003',
        amount: 75000.0,
        currency: 'INR',
        merchant_name: 'Aurelia Gold House',
        merchant_category: 'Jewellery',
        beneficiary_name: 'Mule-Quick-Payout-99',
        payment_method: 'credit_card',
        device_type: 'unknown_bot',
        location: 'Lagos',
        transaction_country: 'NG',
        transaction_type: 'online_payment',
        failed_attempts: 3,
      },
    },
    {
      id: 'scenario_4_cold_start',
      title: '4. New Customer Cafe (₹250)',
      badge: 'NEW USER → SAFE ALLOW',
      badgeColor: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60',
      description: 'First-time user paying ₹250 for cafe dining in Delhi. Verifies that brand new customer accounts do not get false alarms.',
      data: {
        customer_id: 'CUST_MONISHA_001',
        amount: 250.0,
        currency: 'INR',
        merchant_name: 'GreenLeaf Wellness',
        merchant_category: 'Health & Wellness',
        beneficiary_name: 'GreenLeaf Wellness',
        payment_method: 'upi',
        device_type: 'mobile_ios',
        location: 'Chennai',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },
  ]

  const isCustomer = user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user'
  const customerPersona = useMemo(() => getCustomerPersona(user), [user])

  // Presets filtered for customer
  const visiblePresets = useMemo(() => {
    if (!isCustomer) return presets
    const filtered = presets.filter((p) => p.data.customer_id === customerPersona.customerId)
    return filtered.length > 0 ? filtered : [presets[0]]
  }, [isCustomer, customerPersona.customerId, presets])

  // Master Merchants List for autocomplete
  const [merchantsList, setMerchantsList] = useState([])
  const [merchantSuggestions, setMerchantSuggestions] = useState([])
  const [showMerchantSuggestions, setShowMerchantSuggestions] = useState(false)
  const merchantBoxRef = useRef(null)

  useEffect(() => {
    const fetchMerchants = async () => {
      try {
        const token = localStorage.getItem('fraudlens_token')
        const res = await fetch('/api/v1/merchants', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const data = await res.json()
          setMerchantsList(data.merchants || [])
        }
      } catch (err) {
        console.error('Failed to load merchants list for payment view:', err)
      }
    }
    fetchMerchants()
  }, [])

  // Close merchant autocomplete dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (merchantBoxRef.current && !merchantBoxRef.current.contains(e.target)) {
        setShowMerchantSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const defaultPreset = useMemo(() => {
    if (isCustomer) {
      const match = presets.find((p) => p.data.customer_id === customerPersona.customerId)
      return match || presets[0]
    }
    const match = presets.find((p) => p.id === initialPreset)
    return match || presets[0]
  }, [isCustomer, customerPersona.customerId, initialPreset])

  const [activePreset, setActivePreset] = useState(defaultPreset.id)
  const [formData, setFormData] = useState(defaultPreset.data)
  const [showHelperGuide, setShowHelperGuide] = useState(true)

  useEffect(() => {
    if (isCustomer) {
      const match = presets.find((p) => p.data.customer_id === customerPersona.customerId)
      if (match) {
        setActivePreset(match.id)
        setFormData({ ...match.data, customer_id: customerPersona.customerId })
        setDecisionResult(null)
        setError(null)
        setActionSuccessMsg(null)
      }
    } else if (initialPreset) {
      const match = presets.find((p) => p.id === initialPreset)
      if (match) {
        setActivePreset(match.id)
        setFormData(match.data)
        setDecisionResult(null)
        setError(null)
        setActionSuccessMsg(null)
      }
    }
  }, [isCustomer, customerPersona.customerId, initialPreset])

  const handleMerchantNameChange = (text) => {
    handleInputChange('merchant_name', text)
    const query = text.trim().toLowerCase()
    if (query.length >= 1) {
      const matches = merchantsList.filter((m) =>
        m.merchant_name?.toLowerCase().includes(query) ||
        m.merchant_id?.toLowerCase().includes(query) ||
        m.category?.toLowerCase().includes(query) ||
        m.city?.toLowerCase().includes(query)
      )
      setMerchantSuggestions(matches)
      setShowMerchantSuggestions(true)
    } else {
      setMerchantSuggestions(merchantsList)
      setShowMerchantSuggestions(true)
    }
  }

  const handleSelectMerchant = (m) => {
    let catVal = 'retail'
    const catLower = (m.category || '').toLowerCase()
    if (catLower.includes('grocery') || catLower.includes('supermarket')) catVal = 'grocery'
    else if (catLower.includes('dining') || catLower.includes('food')) catVal = 'dining'
    else if (catLower.includes('electronic')) catVal = 'electronics'
    else if (catLower.includes('jewel') || catLower.includes('gold')) catVal = 'luxury_goods'
    else if (catLower.includes('travel') || catLower.includes('flight')) catVal = 'travel'
    else if (catLower.includes('crypto') || catLower.includes('betting') || catLower.includes('rummy')) catVal = 'crypto'

    setFormData((prev) => ({
      ...prev,
      merchant_name: m.merchant_name,
      beneficiary_name: m.merchant_name,
      merchant_category: catVal,
    }))
    setShowMerchantSuggestions(false)
  }

  // Wallet & Profile Data
  const [wallet, setWallet] = useState(null)
  const [walletLoading, setWalletLoading] = useState(false)
  const [pendingApprovals, setPendingApprovals] = useState([])

  // Pre-auth decision & approval state
  const [evaluating, setEvaluating] = useState(false)
  const [decisionResult, setDecisionResult] = useState(null)
  const [error, setError] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionSuccessMsg, setActionSuccessMsg] = useState(null)

  // Mobile Security Push Notification Phone Modal state
  const [showPhoneModal, setShowPhoneModal] = useState(false)
  const [phoneModalTx, setPhoneModalTx] = useState(null)
  const [phoneModalApprovalId, setPhoneModalApprovalId] = useState(null)

  // Load wallet & customer details
  const loadWallet = useCallback(async (customerId) => {
    if (!customerId) return
    setWalletLoading(true)
    try {
      const data = await paymentApi.getWallet(customerId)
      setWallet(data)
    } catch {
      setWallet(null)
    } finally {
      setWalletLoading(false)
    }
  }, [])

  // Load pending approvals
  const loadPendingApprovals = useCallback(async (customerId) => {
    try {
      const list = await paymentApi.listPendingApprovals(customerId)
      setPendingApprovals(list || [])
    } catch {
      setPendingApprovals([])
    }
  }, [])

  useEffect(() => {
    loadWallet(formData.customer_id)
    loadPendingApprovals(formData.customer_id)
  }, [formData.customer_id, loadWallet, loadPendingApprovals])

  const handleSelectPreset = (preset) => {
    setActivePreset(preset.id)
    setFormData(preset.data)
    setDecisionResult(null)
    setError(null)
    setActionSuccessMsg(null)
  }

  const handleInputChange = (field, value) => {
    setFormData((prev) => {
      const updated = {
        ...prev,
        [field]: field === 'amount' || field === 'failed_attempts' ? (value === '' ? '' : Number(value)) : value,
      }
      if (field === 'merchant_name' && (!prev.beneficiary_name || prev.beneficiary_name === prev.merchant_name)) {
        updated.beneficiary_name = value
      }
      return updated
    })
    setActivePreset('custom')
  }

  const setPresetAmount = (amt) => {
    handleInputChange('amount', amt)
  }

  // Check if beneficiary is new for customer
  const isBeneficiaryNew = (name) => {
    if (!name || !wallet || !wallet.known_beneficiaries) return false
    const match = wallet.known_beneficiaries.some(
      (b) => b.beneficiary_name.toLowerCase() === name.trim().toLowerCase()
    )
    return !match && wallet.total_transactions > 0
  }

  // Check if device is new for customer
  const isDeviceNew = (dev) => {
    if (!dev || !wallet || !wallet.known_devices) return false
    const match = wallet.known_devices.some((d) => d.toLowerCase() === dev.toLowerCase())
    return !match && wallet.total_transactions > 0
  }

  const handleInitiatePayment = async (e) => {
    e.preventDefault()
    setEvaluating(true)
    setError(null)
    setDecisionResult(null)
    setActionSuccessMsg(null)

    try {
      const result = await paymentApi.initiate(formData)
      setDecisionResult(result)
      loadWallet(formData.customer_id)
      loadPendingApprovals(formData.customer_id)

      // When fraud risk or review is detected, automatically pop up the Mobile Phone Push Notification Modal
      if (
        result.decision === 'REVIEW' ||
        result.verification_required ||
        result.decision === 'BLOCK' ||
        result.risk_level === 'HIGH' ||
        result.risk_level === 'MEDIUM'
      ) {
        setPhoneModalTx({
          ...formData,
          amount: result.amount || formData.amount,
          merchant_name: result.merchant_name || formData.merchant_name,
          risk_score: result.risk_score,
          risk_level: result.risk_level,
          fraud_probability: result.fraud_probability,
          otp_code: result.otp_code,
          rule_triggered:
            result.triggered_rules?.[0]?.rule_name ||
            (result.decision === 'BLOCK'
              ? 'High Risk Botnet / ATO Detected'
              : 'Behavioral Risk Anomaly Detected'),
        })
        setPhoneModalApprovalId(result.approval_id || null)
        setShowPhoneModal(true)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transaction evaluation failed')
    } finally {
      setEvaluating(false)
    }
  }

  // Execute Step-Up Approval / Rejection with strict real OTP response matching
  const handleApprovalAction = async (approvalId, action, challengeResponse = '') => {
    if (!approvalId || approvalId === 'PEND_DEMO_01' || approvalId.startsWith('DEMO_')) {
      setActionSuccessMsg(
        action === 'APPROVE'
          ? `Demo Transaction authorized successfully via SMS OTP (${challengeResponse || '921457'}).`
          : 'Demo Transaction blocked and card frozen.'
      )
      loadWallet(formData.customer_id)
      return
    }
    setActionLoading(true)
    setError(null)
    try {
      const res = await paymentApi.processApproval(approvalId, {
        action,
        challenge_response: challengeResponse,
        notes: challengeResponse ? `Customer verified via real mobile OTP: ${challengeResponse}` : '',
      })
      setActionSuccessMsg(res.message || `Transaction ${action} successfully.`)

      if (decisionResult && decisionResult.approval_id === approvalId) {
        setDecisionResult((prev) => ({
          ...prev,
          lifecycle_status: res.lifecycle_status,
          decision: action === 'APPROVE' ? 'ALLOW' : 'BLOCK',
          status_message: res.message,
          verification_required: false,
          simulated_balance_after: res.simulated_balance !== null ? res.simulated_balance : prev.simulated_balance_after,
        }))
      }

      loadWallet(formData.customer_id)
      loadPendingApprovals(formData.customer_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action.toLowerCase()} transaction`)
    } finally {
      setActionLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner & Wallet Status Bar in INR */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900/95 to-cyan-950/50 p-6 rounded-2xl border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-full bg-cyan-500/5 blur-3xl pointer-events-none" />
        <div className="flex items-center gap-4 relative z-10">
          <div className="p-3.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-2xl shadow-lg shadow-cyan-500/20 text-white">
            <CreditCard className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-wide">Real-Time Pre-Auth Payment Gateway</h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
                REAL-TIME PRE-AUTH AI
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                INR (₹) LIVE
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl">
              Live pre-transaction fraud scoring &amp; Explainable AI (XAI) risk intervention for 3 distinct customer baseline datasets: <strong className="text-emerald-300">Monisha (3%)</strong>, <strong className="text-amber-300">Mohana (12%)</strong>, and <strong className="text-rose-300">Sowmiya (26%)</strong>. Pre-decision protection stops fraud before funds transfer.
            </p>
          </div>
        </div>

        {/* Live Wallet Balance Badge & Mobile Push Notification Demo Trigger */}
        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={() => {
              setPhoneModalTx({
                amount: formData.amount || 14500,
                merchant_name: formData.merchant_name || 'NovaMart Fresh',
                customer_id: formData.customer_id,
                location: formData.location || 'Mumbai (IP Anomaly)',
                device: formData.device || 'Android Bot/Emulated',
                risk_score: decisionResult?.risk_score || 68,
                risk_level: decisionResult?.risk_level || 'MEDIUM',
                fraud_probability: decisionResult?.fraud_probability || 0.76,
                rule_triggered: 'Suspicious Geo-Velocity & Step-Up Check',
              })
              setPhoneModalApprovalId(decisionResult?.approval_id || 'PEND_DEMO_01')
              setShowPhoneModal(true)
            }}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white font-bold text-xs shadow-lg shadow-purple-950/60 border border-purple-400/40 flex items-center gap-2 transition active:scale-95"
            title="Demonstrate mobile lockscreen push notification & approval flow to evaluators"
          >
            <Smartphone className="w-4 h-4 text-cyan-300 animate-pulse" />
            <span>📱 Phone Push Alert (Demo)</span>
          </button>

          <div className="flex items-center gap-3 bg-slate-950/90 px-4 py-2.5 rounded-xl border border-slate-800 text-xs font-mono">
            <Wallet className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-semibold">Demo Wallet Balance</div>
              <div className="text-base font-extrabold text-white">
                {wallet ? (
                  <span className="text-emerald-400">{formatINR(wallet.simulated_balance)}</span>
                ) : (
                  <span className="text-slate-500">Loading...</span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Session Authority & Active Customer Banner */}
      <div className={`p-4 rounded-2xl border flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg ${
        isCustomer
          ? 'bg-gradient-to-r from-emerald-950/40 via-slate-950 to-emerald-950/20 border-emerald-800/60'
          : 'bg-gradient-to-r from-cyan-950/40 via-slate-950 to-indigo-950/30 border-cyan-800/60'
      }`}>
        <div className="flex items-center gap-3">
          <div className={`p-2.5 rounded-xl border ${
            isCustomer ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
          }`}>
            {isCustomer ? <UserCheck className="w-5 h-5 text-emerald-400" /> : <ShieldAlert className="w-5 h-5 text-cyan-400" />}
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider text-slate-400">
                {isCustomer ? 'Customer Session Scope:' : 'Security Officer Authority:'}
              </span>
              <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold border ${
                isCustomer ? 'bg-emerald-950 text-emerald-300 border-emerald-800' : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
              }`}>
                {isCustomer ? `ACTIVE: ${customerPersona.name.toUpperCase()}` : 'FULL VISIBILITY (3 PERSONAS)'}
              </span>
            </div>
            <div className="text-xs font-bold text-white mt-1">
              {isCustomer ? (
                <span>
                  Watching Account: <strong className="text-emerald-300">{customerPersona.name}</strong> ({customerPersona.customerId}) • {customerPersona.fraudRate} Fraud Baseline ({customerPersona.baselineType})
                </span>
              ) : (
                <span>
                  Operator Authority: <strong className="text-cyan-300">Auditing All 3 Personas</strong> (Monisha 3%, Mohana 12%, Sowmiya 26%)
                </span>
              )}
            </div>
          </div>
        </div>

        {!isCustomer && (
          <div className="flex items-center gap-1.5 shrink-0 bg-slate-950/80 p-1.5 rounded-xl border border-slate-800">
            <span className="text-[10px] font-mono text-slate-400 font-bold px-1">Auditing:</span>
            <button
              type="button"
              onClick={() => handleSelectPreset(presets[0])}
              className={`px-2 py-1 rounded-lg text-[10px] font-mono font-bold border transition ${
                formData.customer_id === 'CUST_MONISHA_001'
                  ? 'bg-emerald-900 border-emerald-500 text-white'
                  : 'bg-emerald-950/60 border-emerald-800/60 text-emerald-300 hover:bg-emerald-900/60'
              }`}
            >
              Monisha (3%)
            </button>
            <button
              type="button"
              onClick={() => handleSelectPreset(presets[1])}
              className={`px-2 py-1 rounded-lg text-[10px] font-mono font-bold border transition ${
                formData.customer_id === 'CUST_MOHANA_002'
                  ? 'bg-amber-900 border-amber-500 text-white'
                  : 'bg-amber-950/60 border-amber-800/60 text-amber-300 hover:bg-amber-900/60'
              }`}
            >
              Mohana (12%)
            </button>
            <button
              type="button"
              onClick={() => handleSelectPreset(presets[2])}
              className={`px-2 py-1 rounded-lg text-[10px] font-mono font-bold border transition ${
                formData.customer_id === 'CUST_SOWMIYA_003'
                  ? 'bg-rose-900 border-rose-500 text-white'
                  : 'bg-rose-950/60 border-rose-800/60 text-rose-300 hover:bg-rose-900/60'
              }`}
            >
              Sowmiya (26%)
            </button>
          </div>
        )}
      </div>

      {/* Testing Guide (Tailored for customer vs admin) */}
      {showHelperGuide && (
        <div className="p-4 bg-gradient-to-r from-cyan-950/40 via-indigo-950/30 to-cyan-950/40 border border-cyan-700/50 rounded-2xl text-xs text-cyan-200 relative shadow-lg">
          <div className="flex items-center justify-between font-bold text-white mb-2">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-cyan-400 animate-pulse" />
              <span className="text-cyan-300 font-extrabold uppercase tracking-wide">
                {isCustomer ? `Personal Security Guide for ${customerPersona.name}` : 'Real-Time Evaluation Personas — 3 Distinct Baseline Datasets'}
              </span>
            </div>
            <button
              onClick={() => setShowHelperGuide(false)}
              className="text-cyan-400 hover:text-white text-xs underline"
            >
              Hide Guide
            </button>
          </div>
          {isCustomer ? (
            <div className="p-3 bg-slate-900/80 rounded-xl border border-emerald-800/50 text-[11px] text-slate-300">
              Welcome, <strong className="text-white">{customerPersona.name}</strong>! You are viewing transactions and pre-authorization protection for your account (<strong className="text-cyan-400">{customerPersona.customerId}</strong>). Your baseline fraud rate is <strong className="text-emerald-400">{customerPersona.fraudRate}</strong>. Routine transfers are auto-approved, while unusual spikes trigger real-time step-up security verification.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-[11px] text-slate-300">
              <div className="p-2.5 bg-slate-900/80 rounded-xl border border-emerald-800/50">
                <strong className="text-emerald-400 block mb-0.5">🟢 1. Monisha (3% Fraud Rate Baseline)</strong>
                Click <strong>"1. Monisha: Habitual Grocery (₹1,250)"</strong> below. Trusted iPhone in Chennai with clean 3% baseline. Result: Instant <strong className="text-emerald-300">ALLOW (Auto-Approved)</strong>.
              </div>
              <div className="p-2.5 bg-slate-900/80 rounded-xl border border-amber-800/50">
                <strong className="text-amber-400 block mb-0.5">🟡 2. Mohana (12% Fraud Rate Baseline)</strong>
                Click <strong>"2. Mohana: Suspicious Device &amp; Region (₹14,500)"</strong>. Unfamiliar browser and Salem distance. Result: Suspicious <strong className="text-amber-300">REVIEW (Step-Up OTP Challenge)</strong>!
              </div>
              <div className="p-2.5 bg-slate-900/80 rounded-xl border border-rose-800/50">
                <strong className="text-rose-400 block mb-0.5">🔴 3. Sowmiya (26% Fraud Rate Baseline)</strong>
                Click <strong>"3. Sowmiya: Botnet Account Takeover (₹75,000)"</strong>. Automated bot emulator at 2:30 AM via foreign proxy IP. Result: Instant Pre-Auth <strong className="text-rose-300">BLOCK (Zero Funds Lost)</strong>!
              </div>
            </div>
          )}
        </div>
      )}

      {/* Preset Scenario Selector */}
      <div className="space-y-1.5">
        <div className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <Zap className="w-3.5 h-3.5 text-cyan-400" />
            <span>
              {isCustomer
                ? `1-Click Test Scenarios for ${customerPersona.name} (${customerPersona.customerId}):`
                : 'Select a 1-Click Test Scenario (All 3 Personas Available for Admin):'}
            </span>
          </div>
          {isCustomer && (
            <span className="text-[10px] font-mono text-emerald-400">
              🔒 Filtered to your personal account
            </span>
          )}
        </div>
        <div className={`grid grid-cols-1 gap-3 ${visiblePresets.length === 1 ? 'sm:grid-cols-1' : visiblePresets.length === 2 ? 'sm:grid-cols-2' : 'sm:grid-cols-2 lg:grid-cols-4'}`}>
          {visiblePresets.map((preset) => {
            const isSelected = activePreset === preset.id
            return (
              <button
                key={preset.id}
                type="button"
                onClick={() => handleSelectPreset(preset)}
                className={`text-left p-3.5 rounded-xl border transition-all duration-200 relative ${
                  isSelected
                    ? 'bg-slate-900/90 border-cyan-500/80 shadow-lg shadow-cyan-950/50 ring-1 ring-cyan-500/40'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/40'
                }`}
              >
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-bold text-slate-200">{preset.title}</span>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded border font-semibold ${preset.badgeColor}`}>
                    {preset.badge}
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
                  {preset.description}
                </p>
              </button>
            )
          })}
        </div>
      </div>

      {/* Main Grid: Form + Live Customer Profile */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Payment Initiation Form */}
        <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800/80 backdrop-blur-md rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Transaction Form (INR ₹)</h2>
            </div>
            <span className="text-[11px] font-mono text-slate-400 flex items-center gap-1">
              <Lock className="w-3 h-3 text-emerald-400" /> Real-Time AI Evaluated
            </span>
          </div>

          <form onSubmit={handleInitiatePayment} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Customer ID */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-slate-300">Customer Account ID</label>
                  {isCustomer ? (
                    <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 font-bold">
                      <Lock className="w-2.5 h-2.5" /> Verified Customer Session
                    </span>
                  ) : (
                    <span className="text-[10px] font-mono text-cyan-400">
                      Operator Probe ID
                    </span>
                  )}
                </div>
                <div className="relative">
                  <input
                    type="text"
                    required
                    readOnly={isCustomer}
                    value={formData.customer_id}
                    onChange={(e) => !isCustomer && handleInputChange('customer_id', e.target.value)}
                    className={`w-full border rounded-xl px-3.5 py-2 text-xs font-mono font-bold transition ${
                      isCustomer
                        ? 'bg-slate-900/90 border-emerald-800/80 text-emerald-300 cursor-not-allowed shadow-inner'
                        : 'bg-slate-950 border-slate-800 text-white focus:outline-none focus:border-cyan-500'
                    }`}
                    placeholder="e.g. CUST_MONISHA_001"
                    title={isCustomer ? `Locked to verified customer: ${customerPersona.name}` : 'Admin can test any customer ID'}
                  />
                  {isCustomer && (
                    <span className="absolute right-3 top-2 text-[10px] font-mono text-emerald-400 font-bold">
                      {customerPersona.name}
                    </span>
                  )}
                </div>
              </div>

              {/* Amount */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-slate-300">Amount (₹ INR)</label>
                  {wallet && (
                    <span className="text-[10px] font-mono text-slate-400">
                      Balance: {formatINR(wallet.simulated_balance)}
                    </span>
                  )}
                </div>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-cyan-400 text-xs font-bold">
                    ₹
                  </div>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={formData.amount}
                    onChange={(e) => handleInputChange('amount', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono font-bold"
                    placeholder="0.00"
                  />
                </div>

                {/* Quick Preset Buttons */}
                <div className="flex items-center gap-1.5 mt-1.5">
                  <span className="text-[10px] text-slate-500">Quick:</span>
                  {[500, 2500, 15000, 50000, 250000].map((amt) => (
                    <button
                      key={amt}
                      type="button"
                      onClick={() => setPresetAmount(amt)}
                      className="px-1.5 py-0.5 bg-slate-900 hover:bg-cyan-950 border border-slate-800 hover:border-cyan-600 text-[10px] text-slate-300 hover:text-cyan-300 rounded font-mono transition"
                    >
                      ₹{amt.toLocaleString('en-IN')}
                    </button>
                  ))}
                </div>
              </div>

              {/* Beneficiary / Merchant Name */}
              <div className="sm:col-span-2 relative" ref={merchantBoxRef}>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-slate-300 flex items-center gap-1.5">
                    <span>Recipient / Beneficiary Name</span>
                    <span className="text-[10px] text-cyan-400 font-normal">(Select from Dropdown or Type)</span>
                  </label>
                  <div className="flex items-center gap-2">
                    {isBeneficiaryNew(formData.merchant_name) ? (
                      <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800">
                        NEW BENEFICIARY (+RISK SIGNAL)
                      </span>
                    ) : (
                      <span className="text-[9px] font-mono text-emerald-400 font-bold">
                        KNOWN RECIPIENT
                      </span>
                    )}
                  </div>
                </div>

                {/* Primary Dropdown with All 29 Merchants + Known Beneficiaries */}
                <div className="mb-2">
                  <select
                    id="recipient-dropdown-all-names"
                    value={merchantsList.some((m) => m.merchant_name === formData.merchant_name) ? formData.merchant_name : (formData.merchant_name ? '__custom__' : '')}
                    onChange={(e) => {
                      const selectedVal = e.target.value
                      if (!selectedVal || selectedVal === '__custom__') {
                        return
                      }
                      const match = merchantsList.find((m) => m.merchant_name === selectedVal)
                      if (match) {
                        handleSelectMerchant(match)
                      } else {
                        handleMerchantNameChange(selectedVal)
                      }
                    }}
                    className="w-full bg-slate-950/90 border border-cyan-800/60 hover:border-cyan-500 rounded-xl px-3 py-2 text-xs text-cyan-200 font-mono focus:outline-none focus:ring-1 focus:ring-cyan-500 transition shadow-inner cursor-pointer"
                  >
                    <option value="">▼ Dropdown: Select recipient/merchant ({merchantsList.length} registered names available)...</option>
                    {wallet?.known_beneficiaries && wallet.known_beneficiaries.length > 0 && (
                      <optgroup label="⭐ Verified Known Beneficiaries (Customer Profile)">
                        {wallet.known_beneficiaries.map((b, idx) => {
                          const bName = typeof b === 'string' ? b : (b.name || b.beneficiary_name || 'Beneficiary')
                          return (
                            <option key={`known-b-${idx}`} value={bName}>
                              ★ {bName} {b.account_number ? `(${b.account_number})` : ''}
                            </option>
                          )
                        })}
                      </optgroup>
                    )}
                    <optgroup label={`🏢 All 29 Registered Canonical Merchants (${merchantsList.length} Total)`}>
                      {merchantsList.map((m) => (
                        <option key={m.merchant_id || m.merchant_name} value={m.merchant_name}>
                          {m.merchant_id ? `[${m.merchant_id}] ` : ''}{m.merchant_name} • {m.category || 'Retail'} ({m.city || 'India'})
                        </option>
                      ))}
                    </optgroup>
                    <option value="__custom__">✏️ Custom / Unlisted Beneficiary (Type name manually below)...</option>
                  </select>
                </div>

                <div className="relative">
                  <input
                    type="text"
                    required
                    value={formData.merchant_name}
                    onChange={(e) => handleMerchantNameChange(e.target.value)}
                    onFocus={() => {
                      handleMerchantNameChange(formData.merchant_name || '')
                    }}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-3.5 pr-16 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono"
                    placeholder="Selected name appears here, or type to search all merchants..."
                  />
                  <div className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center gap-1">
                    {formData.merchant_name && (
                      <button
                        type="button"
                        onClick={() => handleMerchantNameChange('')}
                        className="text-slate-500 hover:text-slate-300 text-xs px-1"
                        title="Clear merchant"
                      >
                        ✕
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => {
                        if (!showMerchantSuggestions) {
                          handleMerchantNameChange(formData.merchant_name || '')
                        } else {
                          setShowMerchantSuggestions(false)
                        }
                      }}
                      className="p-1 text-slate-400 hover:text-cyan-400 transition"
                      title="Browse all merchants"
                    >
                      <ChevronDown className={`w-3.5 h-3.5 transition-transform duration-200 ${showMerchantSuggestions ? 'rotate-180 text-cyan-400' : ''}`} />
                    </button>
                  </div>
                </div>

                {/* Instant 1-2 letter autocomplete suggestion dropdown (All 29 visible by default) */}
                {showMerchantSuggestions && merchantSuggestions.length > 0 && (
                  <div className="absolute left-0 right-0 top-full mt-1.5 bg-slate-900 border border-slate-700/80 rounded-xl shadow-2xl z-50 overflow-hidden">
                    <div className="px-3 py-1.5 bg-slate-950/80 border-b border-slate-800/80 flex items-center justify-between text-[10px] text-slate-400">
                      <span>Showing {merchantSuggestions.length} of {merchantsList.length} canonical merchants (scroll to browse all)</span>
                      <span className="text-cyan-400 font-mono">Click to auto-populate</span>
                    </div>
                    <div className="max-h-64 overflow-y-auto roomy-scrollbar p-1">
                      {merchantSuggestions.map((m) => {
                        const fraudRate = Number(m.historical_fraud_rate_pct ?? 0)
                        return (
                          <button
                            key={m.merchant_id || m.merchant_name}
                            type="button"
                            onClick={() => handleSelectMerchant(m)}
                            className="w-full text-left p-2.5 rounded-lg hover:bg-slate-800/80 transition flex items-center justify-between gap-3 group border-b border-slate-800/40 last:border-b-0"
                          >
                            <div className="min-w-0">
                              <div className="flex items-center gap-2">
                                <span className="font-semibold text-xs text-white group-hover:text-cyan-400 font-mono">
                                  {m.merchant_name}
                                </span>
                                <span className="text-[10px] text-slate-400 font-mono">
                                  {m.merchant_id}
                                </span>
                              </div>
                              <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                                <span>{m.category || 'Retail'}</span>
                                {m.city && <span>• {m.city}</span>}
                                {m.avg_ticket_inr && (
                                  <span>• Avg ₹{Math.round(m.avg_ticket_inr).toLocaleString('en-IN')}</span>
                                )}
                              </div>
                            </div>
                            <div className="flex flex-col items-end shrink-0 gap-1">
                              <span
                                className={`text-[10px] font-mono px-2 py-0.5 rounded-md font-bold ${
                                  fraudRate >= 20
                                    ? 'bg-rose-950/80 text-rose-300 border border-rose-800/80'
                                    : fraudRate >= 10
                                    ? 'bg-amber-950/80 text-amber-300 border border-amber-800/80'
                                    : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/80'
                                }`}
                              >
                                {fraudRate.toFixed(1)}% fraud rate
                              </span>
                            </div>
                          </button>
                        )
                      })}
                    </div>
                  </div>
                )}
              </div>

              {/* Merchant Category */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Merchant Category</label>
                <select
                  value={formData.merchant_category}
                  onChange={(e) => handleInputChange('merchant_category', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="grocery">Grocery &amp; Supermarket (Routine)</option>
                  <option value="retail">Retail Shopping</option>
                  <option value="dining">Dining &amp; Food Delivery</option>
                  <option value="electronics">Electronics &amp; Appliances</option>
                  <option value="travel">Flight &amp; Travel</option>
                  <option value="luxury_goods">Luxury Goods &amp; Jewellery (High Risk)</option>
                  <option value="crypto">Cryptocurrency Exchange (High Risk)</option>
                </select>
              </div>

              {/* Hardware / Device Type */}
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-slate-300">Payment Device / Client</label>
                  {isDeviceNew(formData.device_type) && (
                    <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-purple-950 text-purple-300 border border-purple-800">
                      NEW DEVICE
                    </span>
                  )}
                </div>
                <select
                  value={formData.device_type}
                  onChange={(e) => handleInputChange('device_type', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="mobile_android">Android UPI App (PhonePe / GPay)</option>
                  <option value="mobile_ios">iOS Mobile App (iPhone)</option>
                  <option value="web">Web Browser (Chrome Desktop)</option>
                  <option value="pos">In-Person Card Swipe / POS</option>
                  <option value="unknown_bot">Unrecognized Automated Bot / Tor (High Risk)</option>
                </select>
              </div>

              {/* Origin City & Country */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Origin City &amp; Country</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono"
                    placeholder="City (Mumbai/Delhi/Dubai)"
                  />
                  <input
                    type="text"
                    maxLength={2}
                    value={formData.transaction_country}
                    onChange={(e) => handleInputChange('transaction_country', e.target.value.toUpperCase())}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono uppercase"
                    placeholder="Country (IN/AE/US)"
                  />
                </div>
              </div>

              {/* Failed Authentication Attempts */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Recent Failed PIN/Pass Attempts</label>
                <input
                  type="number"
                  min="0"
                  max="10"
                  value={formData.failed_attempts}
                  onChange={(e) => handleInputChange('failed_attempts', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono"
                  placeholder="0"
                />
              </div>
            </div>

            {/* Error Banner */}
            {error && (
              <div className="p-3.5 bg-rose-950/80 border border-rose-800/80 rounded-xl text-rose-300 text-xs flex items-center gap-2">
                <XCircle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Success Banner */}
            {actionSuccessMsg && (
              <div className="p-3.5 bg-emerald-950/80 border border-emerald-800/80 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                <span>{actionSuccessMsg}</span>
              </div>
            )}

            {/* Submit Action */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={evaluating || actionLoading}
                className="w-full py-3.5 px-6 bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-cyan-900/30 flex items-center justify-center gap-2 transition duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {evaluating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Analyzing Risk with AI Models...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>SIMULATE &amp; PROCESS PAYMENT (₹)</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Live Customer Behavioral Baseline & Known Entities Card */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800/80 backdrop-blur-md rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Customer Profile Baseline</h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">
                {wallet?.total_transactions === 0 ? 'NEW PROFILE' : 'ACTIVE CUSTOMER'}
              </span>
            </div>

            {walletLoading ? (
              <div className="py-8 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Loading customer profile...</span>
              </div>
            ) : wallet ? (
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Available Balance</div>
                    <div className="text-sm font-bold text-emerald-400 font-mono mt-0.5">
                      {formatINR(wallet.simulated_balance)}
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Historical Avg Spend</div>
                    <div className="text-sm font-bold text-white font-mono mt-0.5">
                      {formatINR(wallet.historical_avg_amount)}
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Total Transactions</div>
                    <div className="text-sm font-bold text-cyan-400 font-mono mt-0.5">
                      {wallet.total_transactions} txns
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Account Age</div>
                    <div className="text-sm font-bold text-slate-300 font-mono mt-0.5">
                      {Math.round(wallet.account_age_days)} days
                    </div>
                  </div>
                </div>

                {/* Known Beneficiaries */}
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 space-y-1.5">
                  <div className="text-[10px] text-slate-500 uppercase font-mono flex items-center justify-between">
                    <span>Trusted Beneficiaries</span>
                    <span className="text-cyan-400">{wallet.known_beneficiaries?.length || 0}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {wallet.known_beneficiaries && wallet.known_beneficiaries.length > 0 ? (
                      wallet.known_beneficiaries.map((b) => (
                        <span key={b.id} className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700 text-[10px] font-mono">
                          {b.beneficiary_name}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500 text-[11px] italic">None yet (New customer account)</span>
                    )}
                  </div>
                </div>

                {/* Known Devices */}
                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 space-y-1.5">
                  <div className="text-[10px] text-slate-500 uppercase font-mono flex items-center justify-between">
                    <span>Saved Devices</span>
                    <span className="text-purple-400">{wallet.known_devices?.length || 0}</span>
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {wallet.known_devices && wallet.known_devices.length > 0 ? (
                      wallet.known_devices.map((dev, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-slate-900 text-purple-300 border border-purple-800/60 text-[10px] font-mono">
                          {dev}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500 text-[11px] italic">None yet</span>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-slate-500">
                Customer record will be initialized on first transaction.
              </div>
            )}
          </div>

          {/* Pending Step-Up Verification Challenges List */}
          {pendingApprovals.length > 0 && (
            <div className="bg-amber-950/30 border border-amber-800/60 rounded-2xl p-5 shadow-xl space-y-3">
              <div className="flex items-center justify-between border-b border-amber-800/50 pb-2.5">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-amber-400 animate-pulse" />
                  <h3 className="text-xs font-bold text-amber-200 uppercase tracking-wider">Pending Step-Up Verification</h3>
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950 border border-amber-800 text-amber-300 font-bold">
                  {pendingApprovals.length} HELD
                </span>
              </div>

              <div className="space-y-2">
                {pendingApprovals.map((app) => (
                  <div key={app.approval_id} className="p-3 bg-slate-950/90 rounded-xl border border-amber-800/40 text-xs space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="font-mono font-bold text-white">{formatINR(app.amount)}</span>
                      <span className="text-[10px] font-mono text-amber-400 font-bold">Risk Score: {app.risk_score}/100</span>
                    </div>
                    <p className="text-[11px] text-slate-400">{app.notes || 'Step-up user verification required.'}</p>
                    <div className="flex items-center gap-2 pt-1">
                      <button
                        type="button"
                        onClick={() => {
                          setPhoneModalTx({
                            amount: app.amount,
                            merchant_name: app.merchant_name || 'Flagged Merchant',
                            risk_score: app.risk_score,
                            risk_level: 'HIGH',
                            location: 'Unusual IP / Location',
                            device: 'Unrecognized Device',
                            customer_id: app.customer_id || formData.customer_id,
                          })
                          setPhoneModalApprovalId(app.approval_id)
                          setShowPhoneModal(true)
                        }}
                        className="py-1.5 px-2.5 bg-gradient-to-r from-purple-700 to-indigo-700 hover:from-purple-600 hover:to-indigo-600 text-white rounded-lg text-xs font-bold transition flex items-center gap-1 shrink-0"
                        title="Open on simulated mobile smartphone push notification"
                      >
                        <Smartphone className="w-3.5 h-3.5 text-cyan-300" />
                        <span>📱 Phone</span>
                      </button>
                      <button
                        type="button"
                        disabled={actionLoading}
                        onClick={() => handleApprovalAction(app.approval_id, 'APPROVE')}
                        className="flex-1 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-bold transition flex items-center justify-center gap-1"
                      >
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Authorize</span>
                      </button>
                      <button
                        type="button"
                        disabled={actionLoading}
                        onClick={() => handleApprovalAction(app.approval_id, 'REJECT')}
                        className="flex-1 py-1.5 bg-rose-600 hover:bg-rose-500 text-white rounded-lg text-xs font-bold transition flex items-center justify-center gap-1"
                      >
                        <XCircle className="w-3.5 h-3.5" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Authoritative Evaluation Outcome Card */}
      {decisionResult && (
        <div className={`p-6 rounded-2xl border transition-all duration-500 shadow-2xl space-y-6 ${
          decisionResult.decision === 'ALLOW'
            ? 'bg-gradient-to-b from-slate-900 via-slate-900 to-emerald-950/40 border-emerald-700/60 shadow-emerald-950/30'
            : decisionResult.decision === 'REVIEW'
            ? 'bg-gradient-to-b from-slate-900 via-slate-900 to-amber-950/40 border-amber-700/60 shadow-amber-950/30'
            : 'bg-gradient-to-b from-slate-900 via-slate-900 to-rose-950/40 border-rose-700/60 shadow-rose-950/30'
        }`}>
          {/* Decision Header */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
            <div className="flex items-center gap-4">
              <div className={`p-3.5 rounded-2xl text-white shadow-lg ${
                decisionResult.decision === 'ALLOW'
                  ? 'bg-emerald-600 shadow-emerald-600/30'
                  : decisionResult.decision === 'REVIEW'
                  ? 'bg-amber-600 shadow-amber-600/30'
                  : 'bg-rose-600 shadow-rose-600/30'
              }`}>
                {decisionResult.decision === 'ALLOW' && <CheckCircle2 className="w-8 h-8" />}
                {decisionResult.decision === 'REVIEW' && <AlertTriangle className="w-8 h-8" />}
                {decisionResult.decision === 'BLOCK' && <XCircle className="w-8 h-8" />}
              </div>

              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xl font-extrabold text-white tracking-wider">
                    {decisionResult.decision === 'ALLOW' && 'TRANSACTION AUTHORIZED & PROCEEDED'}
                    {decisionResult.decision === 'REVIEW' && 'STEP-UP VERIFICATION REQUIRED (HELD)'}
                    {decisionResult.decision === 'BLOCK' && 'TRANSACTION PROHIBITED & BLOCKED'}
                  </h3>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                    decisionResult.decision === 'ALLOW'
                      ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                      : decisionResult.decision === 'REVIEW'
                      ? 'bg-amber-950 text-amber-300 border-amber-700'
                      : 'bg-rose-950 text-rose-300 border-rose-700'
                  }`}>
                    {decisionResult.risk_level} RISK
                  </span>
                </div>
                <p className="text-xs text-slate-300 mt-1 font-medium">
                  {decisionResult.status_message}
                </p>
              </div>
            </div>

            <div className="flex flex-wrap items-center gap-3">
              <div className="text-right">
                <div className="text-[10px] text-slate-400 font-mono uppercase">Transaction Token</div>
                <div className="text-xs font-mono font-bold text-cyan-400">{decisionResult.transaction_id}</div>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-slate-400 font-mono uppercase">Decision Speed</div>
                <div className="text-xs font-mono font-bold text-white">{decisionResult.processing_time_ms} ms</div>
              </div>
            </div>
          </div>

          {/* Interactive Step-Up Challenge Action Box (when in REVIEW) */}
          {decisionResult.decision === 'REVIEW' && decisionResult.verification_required && decisionResult.approval_id && (
            <div className="p-4 bg-amber-950/60 border border-amber-700/80 rounded-xl space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-amber-200 text-xs font-bold uppercase tracking-wider">
                  <ShieldAlert className="w-4 h-4 text-amber-400" />
                  <span>Interactive Verification Challenge #{decisionResult.approval_id}</span>
                </div>
                <span className="text-[10px] font-mono text-amber-300 bg-amber-900/60 px-2 py-0.5 rounded border border-amber-700">
                  Holds {formatINR(decisionResult.amount)}
                </span>
              </div>
              <p className="text-xs text-amber-200/90 leading-relaxed">
                The AI risk engine detected elevated behavioral risk factors. Confirm your identity to authorize this transfer or cancel immediately.
              </p>
              <div className="flex flex-wrap items-center gap-3 pt-1">
                <button
                  type="button"
                  onClick={() => {
                    setPhoneModalTx({
                      ...formData,
                      amount: decisionResult.amount || formData.amount,
                      merchant_name: decisionResult.merchant_name || formData.merchant_name,
                      risk_score: decisionResult.risk_score,
                      risk_level: decisionResult.risk_level,
                      fraud_probability: decisionResult.fraud_probability,
                      rule_triggered: decisionResult.triggered_rules?.[0]?.rule_name || 'Step-Up Verification Required',
                    })
                    setPhoneModalApprovalId(decisionResult.approval_id)
                    setShowPhoneModal(true)
                  }}
                  className="py-2 px-5 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-purple-950/50 transition flex items-center gap-2 animate-pulse"
                >
                  <Smartphone className="w-4 h-4 text-cyan-300" />
                  <span>📱 Open Phone Push Notification to Approve</span>
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleApprovalAction(decisionResult.approval_id, 'APPROVE')}
                  className="py-2 px-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-md transition flex items-center gap-1.5 disabled:opacity-60"
                >
                  <CheckCircle2 className="w-4 h-4" />
                  <span>Authorize</span>
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleApprovalAction(decisionResult.approval_id, 'REJECT')}
                  className="py-2 px-4 bg-rose-600 hover:bg-rose-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-md transition flex items-center gap-1.5 disabled:opacity-60"
                >
                  <XCircle className="w-4 h-4" />
                  <span>Reject &amp; Block</span>
                </button>
                <button
                  type="button"
                  disabled={actionLoading}
                  onClick={() => handleApprovalAction(decisionResult.approval_id, 'EXPIRE')}
                  className="py-2 px-3 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl text-xs font-medium transition flex items-center gap-1.5 disabled:opacity-60"
                >
                  <Clock className="w-3.5 h-3.5" />
                  <span>Simulate Timeout</span>
                </button>
              </div>
            </div>
          )}

          {/* Metric Telemetry Row (Independent ML Prob vs Risk Score) */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono uppercase">ML Fraud Likelihood</div>
              <div className="text-xl font-extrabold font-mono text-cyan-300 mt-1">
                {(decisionResult.fraud_probability * 100).toFixed(1)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Model: {decisionResult.model_name} ({decisionResult.model_version})
              </div>
            </div>

            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Independent Risk Score</div>
              <div className="text-xl font-extrabold font-mono text-white mt-1">
                {decisionResult.risk_score} <span className="text-xs text-slate-500">/ 100</span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Multi-Factor Metric (0–30 L / 31–70 M / 71–100 H)
              </div>
            </div>

            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Behavioral Deviation</div>
              <div className="text-xl font-extrabold font-mono text-purple-300 mt-1">
                {(decisionResult.behavioural_deviation_score * 100).toFixed(0)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                vs Customer Historical Baseline
              </div>
            </div>

            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Simulated Wallet Impact</div>
              <div className="text-base font-bold font-mono mt-1 text-emerald-400">
                {formatINR(
                  decisionResult.simulated_balance_after !== null && decisionResult.simulated_balance_after !== undefined
                    ? decisionResult.simulated_balance_after
                    : wallet?.simulated_balance || 50000
                )}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                {decisionResult.decision === 'ALLOW' ? 'Deducted on Success' : 'Protected (Held / Untouched)'}
              </div>
            </div>
          </div>

          {/* Triggered Rules Breakdown */}
          {decisionResult.triggered_rules && decisionResult.triggered_rules.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>Triggered Security &amp; Anomaly Rules</span>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {decisionResult.triggered_rules.map((rule, idx) => (
                  <div key={idx} className="p-3 bg-slate-950/90 rounded-xl border border-slate-800 text-xs space-y-1">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-slate-200">{rule.rule_name}</span>
                      <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border font-bold ${
                        rule.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-300 border-rose-800' : 'bg-amber-950 text-amber-300 border-amber-800'
                      }`}>
                        {rule.severity}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400">{rule.description}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Structured SHAP Attribution Card */}
          {decisionResult.structured_explanations && decisionResult.structured_explanations.length > 0 && (
            <div className="space-y-3">
              <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                  <span>Model Explainability (Local SHAP Feature Attributions)</span>
                </div>
                {decisionResult.explanation_id && (
                  <span className="text-[10px] font-mono text-slate-500">ID: {decisionResult.explanation_id}</span>
                )}
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                {decisionResult.structured_explanations.map((exp, idx) => {
                  const isRiskUp = exp.direction === 'INCREASES_RISK'
                  const absVal = Math.min(Math.abs(exp.contribution || 0) * 100, 100)
                  return (
                    <div key={idx} className="p-3 bg-slate-950/90 rounded-xl border border-slate-800 text-xs space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-indigo-300 font-semibold">{exp.feature}</span>
                        <span className={`text-[10px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                          isRiskUp
                            ? 'bg-rose-950/80 text-rose-300 border-rose-800/80'
                            : 'bg-emerald-950/80 text-emerald-300 border-emerald-800/80'
                        }`}>
                          {isRiskUp ? '▲ Contributed toward risk' : '▼ Contributed away from risk'} ({exp.contribution > 0 ? `+${exp.contribution}` : exp.contribution})
                        </span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                        <div
                          className={`h-full rounded-full transition-all duration-500 ${isRiskUp ? 'bg-gradient-to-r from-rose-500 to-amber-500' : 'bg-gradient-to-r from-emerald-500 to-cyan-500'}`}
                          style={{ width: `${Math.max(absVal, 8)}%` }}
                        />
                      </div>
                      <p className="text-[11px] text-slate-300">{exp.human_interpretation}</p>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* Action Navigation Footer */}
          <div className="p-3.5 bg-slate-950/80 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="text-slate-400 text-[11px] font-mono">
              Status: <strong className="text-white uppercase">{decisionResult.lifecycle_status}</strong> | Audit Trail Recorded
            </div>
            <div className="flex items-center gap-2">
              {onViewExplanation && (
                <button
                  type="button"
                  onClick={() => onViewExplanation(decisionResult.transaction_id)}
                  className="px-3.5 py-1.5 rounded-xl bg-purple-900/60 hover:bg-purple-900 text-purple-200 border border-purple-700 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Full SHAP Breakdown
                </button>
              )}
              {onNavigateToInvestigations && (decisionResult.case_id || decisionResult.risk_level === 'HIGH' || decisionResult.decision === 'REVIEW') && (
                <button
                  type="button"
                  onClick={onNavigateToInvestigations}
                  className="px-3.5 py-1.5 rounded-xl bg-amber-900/60 hover:bg-amber-900 text-amber-200 border border-amber-700 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Open Investigation Case &rarr;
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Mobile Smartphone Security Push Notification Modal for Mam / Evaluators */}
      <MobileSecurityApprovalModal
        isOpen={showPhoneModal}
        onClose={() => setShowPhoneModal(false)}
        transaction={phoneModalTx || formData}
        approvalId={phoneModalApprovalId || decisionResult?.approval_id}
        customerName={customerPersona?.name || 'Customer'}
        actionLoading={actionLoading}
        onApprove={async (appId, challengeResponse) => {
          const id = appId || phoneModalApprovalId || decisionResult?.approval_id
          if (id && id !== 'PEND_DEMO_01' && !id.startsWith('DEMO_')) {
            await handleApprovalAction(id, 'APPROVE', challengeResponse)
          } else {
            setActionSuccessMsg(`Transaction authorized via mobile SMS OTP (${challengeResponse})! Funds released.`)
            loadWallet(formData.customer_id)
          }
        }}
        onReject={async (appId) => {
          const id = appId || phoneModalApprovalId || decisionResult?.approval_id
          if (id) {
            await handleApprovalAction(id, 'REJECT')
          } else {
            setActionSuccessMsg('Transaction blocked and card frozen!')
          }
        }}
      />
    </div>
  )
}
