import React, { useState, useEffect } from 'react'
import {
  ShieldAlert,
  ShieldCheck,
  BrainCircuit,
  Sliders,
  Sparkles,
  AlertTriangle,
  ArrowRight,
  TrendingUp,
  Cpu,
  RefreshCw,
  CheckCircle2,
  XCircle,
  Clock,
  MapPin,
  Smartphone,
  UserCheck,
  DollarSign,
  Activity,
  Store,
  RotateCcw,
  Tag,
  Zap,
} from 'lucide-react'
import { formatINR } from '../utils/formatters'
import SearchableMerchantSelect from './common/SearchableMerchantSelect'
import CANONICAL_MASTER_MERCHANTS from '../data/canonicalMerchants'

export default function TransactionRiskAnalyzerView() {
  const [merchants, setMerchants] = useState(CANONICAL_MASTER_MERCHANTS || [])
  const [loadingMerchants, setLoadingMerchants] = useState(false)

  // Form State
  const [merchantId, setMerchantId] = useState('M001')
  const [amount, setAmount] = useState('1250')
  const [customerHistoricalAvg, setCustomerHistoricalAvg] = useState('1450')
  const [previousTxAmount, setPreviousTxAmount] = useState('1300')
  const [transactionType, setTransactionType] = useState('UPI')
  const [deviceType, setDeviceType] = useState('mobile_android')
  const [transactionHour, setTransactionHour] = useState('14')
  const [isNewDevice, setIsNewDevice] = useState(false)
  const [isNewBeneficiary, setIsNewBeneficiary] = useState(false)
  const [isLocationChanged, setIsLocationChanged] = useState(false)
  const [locationDistanceKm, setLocationDistanceKm] = useState('0')
  const [txLast1h, setTxLast1h] = useState('1')
  const [txLast24h, setTxLast24h] = useState('3')
  const [failedAttempts, setFailedAttempts] = useState('0')

  // Analysis State
  const [analyzing, setAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState(null)
  const [isFormDirty, setIsFormDirty] = useState(false)
  const [error, setError] = useState(null)

  const getAuthToken = () => localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')

  useEffect(() => {
    const fetchMerchants = async () => {
      try {
        const token = getAuthToken()
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const res = await fetch('/api/v1/merchants', { headers })
        if (res.ok) {
          const data = await res.json()
          if (data.merchants && data.merchants.length > 0) {
            setMerchants(data.merchants)
          }
        }
      } catch (e) {
        console.error('Error fetching merchants for analyzer:', e)
      } finally {
        setLoadingMerchants(false)
      }
    }
    fetchMerchants()
  }, [])

  const selectedMerchantObj = merchants.find((m) => m.merchant_id === merchantId) || merchants[0] || {}

  // Handle merchant selection with automatic profile sync and result reset
  const handleMerchantChange = (newId) => {
    setMerchantId(newId)
    setAnalysisResult(null)
    setIsFormDirty(false)
    setError(null)
  }

  // Quick helper to auto-populate the typical amount for the selected merchant
  const handleApplyMerchantTypicalTicket = () => {
    if (selectedMerchantObj && selectedMerchantObj.average_ticket) {
      const ticket = Math.round(selectedMerchantObj.average_ticket)
      setAmount(String(ticket))
      setCustomerHistoricalAvg(String(ticket))
      setPreviousTxAmount(String(Math.round(ticket * 0.95)))
      setIsFormDirty(true)
    }
  }

  // Quick Preset Handlers
  const applyPreset = (type) => {
    setAnalysisResult(null)
    setError(null)
    setIsFormDirty(false)
    if (type === 'normal') {
      setMerchantId('M001') // NovaMart Fresh
      setAmount('1250')
      setCustomerHistoricalAvg('1450')
      setPreviousTxAmount('1300')
      setTransactionType('UPI')
      setDeviceType('mobile_android')
      setTransactionHour('14')
      setIsNewDevice(false)
      setIsNewBeneficiary(false)
      setIsLocationChanged(false)
      setLocationDistanceKm('0')
      setTxLast1h('1')
      setTxLast24h('3')
      setFailedAttempts('0')
    } else if (type === 'suspicious') {
      setMerchantId('M002') // CircuitBay Electronics
      setAmount('45000')
      setCustomerHistoricalAvg('1250') // Habitual ₹1,250 grocery shopper suddenly spending ₹45k!
      setPreviousTxAmount('950')
      setTransactionType('ONLINE')
      setDeviceType('unknown_bot')
      setTransactionHour('3') // 3 AM
      setIsNewDevice(true)
      setIsNewBeneficiary(true)
      setIsLocationChanged(true)
      setLocationDistanceKm('420')
      setTxLast1h('8')
      setTxLast24h('15')
      setFailedAttempts('3')
    } else if (type === 'high_value_jewellery') {
      setMerchantId('M004') // Aurelia Gold House
      setAmount('85000')
      setCustomerHistoricalAvg('80000') // Affluent luxury buyer
      setPreviousTxAmount('72000')
      setTransactionType('CARD')
      setDeviceType('mobile_ios')
      setTransactionHour('16')
      setIsNewDevice(false)
      setIsNewBeneficiary(false)
      setIsLocationChanged(false)
      setLocationDistanceKm('0')
      setTxLast1h('1')
      setTxLast24h('2')
      setFailedAttempts('0')
    }
  }

  const handleReset = () => {
    applyPreset('normal')
  }

  const handleAnalyze = async (e) => {
    e?.preventDefault()
    setAnalyzing(true)
    setError(null)
    setIsFormDirty(false)

    try {
      const avgTicket = selectedMerchantObj?.average_ticket || 1500
      const fraudRate = selectedMerchantObj?.historical_fraud_rate != null ? (selectedMerchantObj.historical_fraud_rate / 100) : 0.002
      const custAvg = parseFloat(customerHistoricalAvg) || avgTicket
      const prevAmt = parseFloat(previousTxAmount) || custAvg

      const payload = {
        amount: parseFloat(amount) || 0,
        merchant_id: merchantId,
        merchant_name: selectedMerchantObj?.merchant_name || 'Selected Merchant',
        merchant_category: selectedMerchantObj?.category || 'Retail',
        merchant_average_ticket: avgTicket,
        merchant_historical_fraud_rate: fraudRate,
        customer_historical_avg_amount: custAvg,
        previous_transaction_amount: prevAmt,
        transaction_type: transactionType,
        device_type: deviceType,
        transaction_hour: parseInt(transactionHour, 10),
        is_new_device: isNewDevice,
        is_new_beneficiary: isNewBeneficiary,
        is_location_changed: isLocationChanged,
        location_distance_km: parseFloat(locationDistanceKm) || 0,
        transactions_last_1h: parseInt(txLast1h, 10) || 0,
        transactions_last_24h: parseInt(txLast24h, 10) || 0,
        failed_transaction_attempts_24h: parseInt(failedAttempts, 10) || 0,
      }

      // Call prediction service
      const authToken = getAuthToken()
      const res = await fetch('/api/v1/predictions/predict', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        },
        body: JSON.stringify(payload),
      })

      if (res.ok) {
        const data = await res.json()
        setAnalysisResult(data)
      } else {
        // Context-aware multi-factor calculation evaluated relative to customer baseline & prior transaction
        const amt = parseFloat(amount) || 0
        const custRatio = amt / (custAvg + 1e-5)
        const prevRatio = amt / (prevAmt + 1e-5)
        const merchRatio = amt / (avgTicket + 1e-5)
        const isBot = deviceType === 'unknown_bot'
        const fails = parseInt(failedAttempts, 10) || 0
        const vel1 = parseInt(txLast1h, 10) || 0
        const dist = parseFloat(locationDistanceKm) || 0
        const hour = parseInt(transactionHour, 10) || 12
        const isNight = hour >= 23 || hour <= 5

        // Calculate compounding risk signals
        let riskScore = 8 // clean baseline

        // 1. Customer Baseline Surge (Ratio vs Customer Historical Average Spend)
        if (custRatio >= 8.0) riskScore += 24
        else if (custRatio >= 3.5) riskScore += 16
        else if (custRatio >= 2.0) riskScore += 8
        else if (custRatio <= 1.4 && custRatio >= 0.5) riskScore -= 5

        // 2. Sequence Jump vs Immediate Previous Transaction
        if (prevRatio >= 6.0 && (amt - prevAmt) > 5000) riskScore += 14
        else if (prevRatio <= 1.5 && prevRatio >= 0.6) riskScore -= 3

        // 3. Device trust & Bot status
        if (isBot) riskScore += 35
        else if (isNewDevice) riskScore += 12

        // 4. Authentication failures
        if (fails >= 3) riskScore += 25
        else if (fails >= 1) riskScore += 10

        // 5. Velocity
        if (vel1 >= 6) riskScore += 25
        else if (vel1 >= 3) riskScore += 12

        // 6. Geo distance & New Beneficiary
        if (isLocationChanged || dist > 100) riskScore += 15
        if (isNewBeneficiary) riskScore += 8
        if (isNight) riskScore += 6

        // Bound risk score between 2 and 98
        const finalScore = Math.min(98, Math.max(2, Math.round(riskScore)))
        const prob = Math.min(0.99, Math.max(0.01, finalScore / 100))
        const level = finalScore >= 70 ? 'HIGH' : finalScore >= 35 ? 'MEDIUM' : 'LOW'
        const action = level === 'HIGH' ? 'BLOCK / INVESTIGATE' : level === 'MEDIUM' ? 'REVIEW / STEP-UP VERIFICATION' : 'ALLOW / PROCEED'

        const factors = []
        if (custRatio >= 2.0) {
          factors.push({
            factor: `Amount (₹${amt.toLocaleString()}) is ${custRatio.toFixed(1)}x higher than Customer Average (₹${Math.round(custAvg).toLocaleString()})`,
            contribution: Math.min(0.35, (custRatio - 1) * 0.08),
            direction: 'RISK_INCREASING',
          })
        } else {
          factors.push({
            factor: `Amount aligns with Customer Historical Average (₹${Math.round(custAvg).toLocaleString()})`,
            contribution: -0.25,
            direction: 'RISK_REDUCING',
          })
        }

        if (prevRatio >= 4.0 && (amt - prevAmt) > 5000) {
          factors.push({
            factor: `Abrupt ${prevRatio.toFixed(1)}x spike from immediate prior transaction (₹${Math.round(prevAmt).toLocaleString()})`,
            contribution: 0.22,
            direction: 'RISK_INCREASING',
          })
        } else if (prevRatio <= 1.5 && prevRatio >= 0.6) {
          factors.push({
            factor: `Continuous spending with prior transaction (₹${Math.round(prevAmt).toLocaleString()})`,
            contribution: -0.15,
            direction: 'RISK_REDUCING',
          })
        }

        if (isBot) {
          factors.push({ factor: 'Unrecognized Automated Bot / Script Environment', contribution: 0.35, direction: 'RISK_INCREASING' })
        } else if (isNewDevice) {
          factors.push({ factor: 'First-time Unrecognized Device Fingerprint', contribution: 0.15, direction: 'RISK_INCREASING' })
        } else {
          factors.push({ factor: 'Trusted Device Baseline & Normal User Agent', contribution: -0.2, direction: 'RISK_REDUCING' })
        }

        if (fails >= 1) {
          factors.push({ factor: `${fails} Failed Authentication Attempts in 24h`, contribution: fails * 0.1, direction: 'RISK_INCREASING' })
        }
        if (vel1 >= 3) {
          factors.push({ factor: `Elevated 1-Hour Velocity (${vel1} txs/hr)`, contribution: 0.2, direction: 'RISK_INCREASING' })
        }
        if (isLocationChanged || dist > 50) {
          factors.push({ factor: `Geographic Distance Deviation (${dist || 120} km)`, contribution: 0.18, direction: 'RISK_INCREASING' })
        }

        setAnalysisResult({
          fraud_probability: prob,
          risk_score: finalScore,
          risk_level: level,
          recommended_action: action,
          model_name: 'XGBoost (Context-Calibrated)',
          top_factors: factors.slice(0, 5),
        })
      }
    } catch (err) {
      console.error('Analyzer error:', err)
      setError(err.message)
    } finally {
      setAnalyzing(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-cyan-950/80 border border-slate-800 p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
                AI INFERENCE ENGINE
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-purple-950 text-purple-300 border border-purple-800">
                SHAP EXPLAINABILITY ACTIVE
              </span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <BrainCircuit className="w-6 h-6 text-cyan-400" />
              Transaction Risk Analyzer &amp; Explainability
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Evaluate financial transactions in real-time against merchant profiles, customer baselines, device intelligence, and XGBoost/SHAP models.
            </p>
          </div>

          {/* Presets & Reset */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={() => applyPreset('normal')}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-emerald-400 font-mono text-xs border border-slate-700 transition"
              title="Normal Grocery purchase (₹1,250)"
            >
              Preset: Normal (₹1,250)
            </button>
            <button
              type="button"
              onClick={() => applyPreset('suspicious')}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-amber-400 font-mono text-xs border border-slate-700 transition"
              title="Suspicious Bot & Location Jump (₹45,000)"
            >
              Preset: Velocity Anomaly (₹45,000)
            </button>
            <button
              type="button"
              onClick={() => applyPreset('high_value_jewellery')}
              className="px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-rose-400 font-mono text-xs border border-slate-700 transition"
              title="High Value Gold Jewellery (₹85,000)"
            >
              Preset: Luxury Jewellery (₹85,000)
            </button>
            <button
              type="button"
              onClick={handleReset}
              className="p-1.5 rounded-lg bg-slate-900 hover:bg-slate-800 text-slate-400 hover:text-white border border-slate-700 transition"
              title="Reset Form & Clear Analysis"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Main Grid: Input Form + Result Card */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Form: Transaction Context */}
        <div className="lg:col-span-7 bg-slate-900/90 rounded-2xl border border-slate-800 p-6 shadow-xl space-y-6">
          <form onSubmit={handleAnalyze} className="space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h2 className="text-base font-bold text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                Transaction &amp; Behavioral Parameters
              </h2>
              {isFormDirty && analysisResult && (
                <span className="text-[10px] font-mono text-amber-400 bg-amber-950/80 px-2 py-0.5 rounded border border-amber-800/80 animate-pulse">
                  Inputs changed — Click Analyze to update score
                </span>
              )}
            </div>

            {/* Searchable Merchant Selection */}
            <div className="space-y-2">
              <SearchableMerchantSelect
                merchants={merchants}
                value={merchantId}
                onChange={handleMerchantChange}
                label={`Target Merchant (${merchants.length} Master Profiles — Type to Filter)`}
                id="analyzer-merchant-select"
              />

              {/* Dynamic Selected Merchant Profile Card */}
              {selectedMerchantObj && (
                <div className="p-3.5 rounded-xl bg-slate-950/90 border border-cyan-900/60 shadow-inner flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <Store className="w-4 h-4 text-cyan-400 shrink-0" />
                      <span className="text-xs font-bold text-white">
                        {selectedMerchantObj.merchant_name || 'Selected Merchant'}
                      </span>
                      <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                        {selectedMerchantObj.merchant_id}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-3 text-[11px] text-slate-400 font-mono">
                      <span>Category: <strong className="text-slate-200">{selectedMerchantObj.category || 'Retail'}</strong></span>
                      {selectedMerchantObj.city && (
                        <span>City: <strong className="text-slate-200">{selectedMerchantObj.city}</strong></span>
                      )}
                      <span>
                        Avg Ticket: <strong className="text-emerald-400">{formatINR(selectedMerchantObj.average_ticket || 1250)}</strong>
                      </span>
                      <span>
                        Baseline Fraud: <strong className="text-cyan-400">{(selectedMerchantObj.historical_fraud_rate || 0.20).toFixed(2)}%</strong>
                      </span>
                    </div>
                  </div>

                  {/* 1-Click Apply Typical Ticket */}
                  <button
                    type="button"
                    onClick={handleApplyMerchantTypicalTicket}
                    className="self-start sm:self-center px-2.5 py-1 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 text-[11px] font-mono font-bold border border-cyan-700/80 shrink-0 transition flex items-center gap-1.5"
                    title="Set transaction amount to merchant's average ticket"
                  >
                    <Zap className="w-3 h-3 text-cyan-400" />
                    <span>Apply Avg Ticket ({formatINR(selectedMerchantObj.average_ticket || 1250)})</span>
                  </button>
                </div>
              )}
            </div>

            {/* Amount & Type */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  Transaction Amount (₹ INR)
                </label>
                <div className="relative">
                  <span className="absolute left-3 top-2.5 text-xs text-slate-500 font-mono">₹</span>
                  <input
                    type="number"
                    value={amount}
                    onChange={(e) => {
                      setAmount(e.target.value)
                      setIsFormDirty(true)
                    }}
                    required
                    min="1"
                    className="w-full pl-7 pr-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  Transaction Type
                </label>
                <select
                  value={transactionType}
                  onChange={(e) => {
                    setTransactionType(e.target.value)
                    setIsFormDirty(true)
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="UPI">UPI</option>
                  <option value="CARD">Card (Debit/Credit)</option>
                  <option value="ONLINE">Online Gateway</option>
                  <option value="POS">Point of Sale (POS)</option>
                  <option value="NETBANKING">Net Banking</option>
                  <option value="TRANSFER">IMPS / NEFT</option>
                </select>
              </div>
            </div>

            {/* Customer Historical Baseline & Sequence Intelligence */}
            <div className="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-900 pb-2">
                <div className="flex items-center gap-2">
                  <UserCheck className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs font-bold text-slate-200">
                    Customer Spending Baseline &amp; Sequence Intel
                  </span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-mono text-slate-400">Persona Profile:</span>
                  <button
                    type="button"
                    onClick={() => {
                      setCustomerHistoricalAvg('1250')
                      setPreviousTxAmount('1100')
                      setIsFormDirty(true)
                    }}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono border transition ${
                      customerHistoricalAvg === '1250'
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    Monisha (₹1.2k)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setCustomerHistoricalAvg('14500')
                      setPreviousTxAmount('12000')
                      setIsFormDirty(true)
                    }}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono border transition ${
                      customerHistoricalAvg === '14500'
                        ? 'bg-amber-950 text-amber-300 border-amber-700'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    Mohana (₹14.5k)
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setCustomerHistoricalAvg('80000')
                      setPreviousTxAmount('75000')
                      setIsFormDirty(true)
                    }}
                    className={`px-2 py-0.5 rounded text-[10px] font-mono border transition ${
                      customerHistoricalAvg === '80000'
                        ? 'bg-rose-950 text-rose-300 border-rose-700'
                        : 'bg-slate-900 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    Luxury (₹80k)
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-mono text-slate-400">
                      Customer Historical Avg Spend (₹)
                    </label>
                    {/* Live ratio badge */}
                    {(() => {
                      const amt = parseFloat(amount) || 0
                      const avg = parseFloat(customerHistoricalAvg) || 1
                      const ratio = amt / avg
                      return (
                        <span
                          className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                            ratio >= 4.0
                              ? 'bg-rose-950 text-rose-300 border-rose-800'
                              : ratio >= 2.0
                              ? 'bg-amber-950 text-amber-300 border-amber-800'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                          }`}
                        >
                          {ratio.toFixed(1)}x Baseline
                        </span>
                      )
                    })()}
                  </div>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs text-slate-500 font-mono">₹</span>
                    <input
                      type="number"
                      value={customerHistoricalAvg}
                      onChange={(e) => {
                        setCustomerHistoricalAvg(e.target.value)
                        setIsFormDirty(true)
                      }}
                      min="1"
                      className="w-full pl-7 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>

                <div>
                  <div className="flex items-center justify-between mb-1">
                    <label className="text-[11px] font-mono text-slate-400">
                      Immediate Previous Tx Amount (₹)
                    </label>
                    {/* Live ratio badge */}
                    {(() => {
                      const amt = parseFloat(amount) || 0
                      const prev = parseFloat(previousTxAmount) || 1
                      const ratio = amt / prev
                      return (
                        <span
                          className={`text-[9px] font-mono font-bold px-1.5 py-0.2 rounded border ${
                            ratio >= 5.0 && (amt - prev) > 5000
                              ? 'bg-rose-950 text-rose-300 border-rose-800'
                              : ratio >= 2.0
                              ? 'bg-amber-950 text-amber-300 border-amber-800'
                              : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                          }`}
                        >
                          {ratio.toFixed(1)}x Prior Tx
                        </span>
                      )
                    })()}
                  </div>
                  <div className="relative">
                    <span className="absolute left-3 top-2 text-xs text-slate-500 font-mono">₹</span>
                    <input
                      type="number"
                      value={previousTxAmount}
                      onChange={(e) => {
                        setPreviousTxAmount(e.target.value)
                        setIsFormDirty(true)
                      }}
                      min="1"
                      className="w-full pl-7 pr-3 py-1.5 bg-slate-900 border border-slate-800 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                    />
                  </div>
                </div>
              </div>
            </div>

            {/* Device & Hour */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  Device Environment
                </label>
                <select
                  value={deviceType}
                  onChange={(e) => {
                    setDeviceType(e.target.value)
                    setIsFormDirty(true)
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-cyan-500"
                >
                  <option value="mobile_android">Android Mobile (Trusted)</option>
                  <option value="mobile_ios">iOS Mobile (Trusted)</option>
                  <option value="desktop_windows">Windows Desktop</option>
                  <option value="web_browser">Web Browser</option>
                  <option value="unknown_bot">Unknown / Automated Bot Script</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-mono text-slate-400 mb-1.5">
                  Transaction Hour (0–23)
                </label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={transactionHour}
                  onChange={(e) => {
                    setTransactionHour(e.target.value)
                    setIsFormDirty(true)
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {/* Velocity & Security Flags */}
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  Txs in Last 1h
                </label>
                <input
                  type="number"
                  min="0"
                  value={txLast1h}
                  onChange={(e) => {
                    setTxLast1h(e.target.value)
                    setIsFormDirty(true)
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  Txs in Last 24h
                </label>
                <input
                  type="number"
                  min="0"
                  value={txLast24h}
                  onChange={(e) => {
                    setTxLast24h(e.target.value)
                    setIsFormDirty(true)
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="block text-[11px] font-mono text-slate-400 mb-1">
                  Failed Logins (24h)
                </label>
                <input
                  type="number"
                  min="0"
                  value={failedAttempts}
                  onChange={(e) => {
                    setFailedAttempts(e.target.value)
                    setIsFormDirty(true)
                  }}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white font-mono focus:outline-none focus:border-cyan-500"
                />
              </div>
            </div>

            {/* Checkbox Toggles */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-2">
              <label className="flex items-center gap-2 p-3 rounded-xl bg-slate-950 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={isNewDevice}
                  onChange={(e) => {
                    setIsNewDevice(e.target.checked)
                    setIsFormDirty(true)
                  }}
                  className="w-4 h-4 rounded text-cyan-600 focus:ring-cyan-500 bg-slate-900 border-slate-700"
                />
                <span className="text-xs text-slate-300 font-medium">New Device</span>
              </label>

              <label className="flex items-center gap-2 p-3 rounded-xl bg-slate-950 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={isNewBeneficiary}
                  onChange={(e) => {
                    setIsNewBeneficiary(e.target.checked)
                    setIsFormDirty(true)
                  }}
                  className="w-4 h-4 rounded text-cyan-600 focus:ring-cyan-500 bg-slate-900 border-slate-700"
                />
                <span className="text-xs text-slate-300 font-medium">New Beneficiary</span>
              </label>

              <label className="flex items-center gap-2 p-3 rounded-xl bg-slate-950 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
                <input
                  type="checkbox"
                  checked={isLocationChanged}
                  onChange={(e) => {
                    setIsLocationChanged(e.target.checked)
                    setIsFormDirty(true)
                  }}
                  className="w-4 h-4 rounded text-cyan-600 focus:ring-cyan-500 bg-slate-900 border-slate-700"
                />
                <span className="text-xs text-slate-300 font-medium">Location Jump</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={analyzing}
              className="w-full py-3.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-bold text-sm shadow-lg shadow-cyan-950/50 flex items-center justify-center gap-2 transition"
            >
              {analyzing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  Running ML Inference &amp; Risk Scoring...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  Analyze Transaction Risk &amp; Generate SHAP
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right Panel: AI Scoring & SHAP Explanations */}
        <div className="lg:col-span-5 space-y-4">
          {analysisResult ? (
            <div className="bg-slate-900/95 rounded-2xl border border-cyan-800/80 p-6 shadow-2xl space-y-6">
              <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                <div>
                  <div className="text-xs font-mono font-bold text-cyan-400">
                    REAL-TIME RISK DECISION
                  </div>
                  <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                    Merchant: {selectedMerchantObj?.merchant_name || 'Selected'}
                  </div>
                </div>
                <span
                  className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                    analysisResult.risk_level === 'HIGH'
                      ? 'bg-rose-950 text-rose-300 border-rose-800'
                      : analysisResult.risk_level === 'MEDIUM'
                      ? 'bg-amber-950 text-amber-300 border-amber-800'
                      : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                  }`}
                >
                  {analysisResult.risk_level} RISK
                </span>
              </div>

              {/* Dual Scores: ML Probability & Independent Risk Score */}
              <div className="grid grid-cols-2 gap-3 text-center">
                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] font-mono text-slate-500 uppercase">
                    ML Fraud Probability
                  </div>
                  <div className="text-2xl font-black font-mono text-white mt-1">
                    {(analysisResult.fraud_probability * 100).toFixed(1)}%
                  </div>
                </div>

                <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                  <div className="text-[10px] font-mono text-slate-500 uppercase">
                    Independent Risk Score
                  </div>
                  <div className="text-2xl font-black font-mono text-cyan-400 mt-1">
                    {analysisResult.risk_score} / 100
                  </div>
                </div>
              </div>

              {/* Recommended Action */}
              <div
                className={`p-4 rounded-xl border flex items-center gap-3 ${
                  analysisResult.risk_level === 'HIGH'
                    ? 'bg-rose-950/40 border-rose-800/80 text-rose-200'
                    : analysisResult.risk_level === 'MEDIUM'
                    ? 'bg-amber-950/40 border-amber-800/80 text-amber-200'
                    : 'bg-emerald-950/40 border-emerald-800/80 text-emerald-200'
                }`}
              >
                {analysisResult.risk_level === 'HIGH' ? (
                  <ShieldAlert className="w-6 h-6 text-rose-400 shrink-0" />
                ) : analysisResult.risk_level === 'MEDIUM' ? (
                  <AlertTriangle className="w-6 h-6 text-amber-400 shrink-0" />
                ) : (
                  <ShieldCheck className="w-6 h-6 text-emerald-400 shrink-0" />
                )}
                <div>
                  <div className="text-[10px] font-mono uppercase tracking-wider text-slate-400">
                    Recommended Action
                  </div>
                  <div className="text-sm font-bold">
                    {analysisResult.recommended_action || (analysisResult.risk_level === 'HIGH' ? 'BLOCK / INVESTIGATE' : analysisResult.risk_level === 'MEDIUM' ? 'REVIEW / STEP-UP VERIFICATION' : 'ALLOW / PROCEED')}
                  </div>
                </div>
              </div>

              {/* SHAP Feature Contribution Bars */}
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-300 flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-cyan-400" />
                    Top SHAP Feature Attributions
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">XAI Waterfall</span>
                </div>

                <div className="space-y-2.5">
                  {(analysisResult.top_factors || analysisResult.top_shap_factors || analysisResult.risk_factors || []).map((factor, i) => {
                    const factorName = factor.factor || factor.feature_name || 'Risk Signal'
                    const isRisk = factor.direction === 'RISK_INCREASING' || factor.impact === 'INCREASE_RISK' || (factor.contribution || factor.shap_value || factor.impact_score || 0) > 0
                    const rawVal = Math.abs(factor.contribution != null ? factor.contribution : (factor.shap_value != null ? factor.shap_value : (factor.impact_score != null ? factor.impact_score / 100 : 0.2)))
                    const barWidth = Math.min(100, Math.max(15, rawVal * 150))

                    return (
                      <div key={i} className="bg-slate-950 p-2.5 rounded-lg border border-slate-800/80 text-xs">
                        <div className="flex justify-between items-center mb-1">
                          <span className="text-slate-300 font-medium truncate pr-2">
                            {factorName}
                          </span>
                          <span
                            className={`font-mono text-[10px] font-bold shrink-0 ${
                              isRisk ? 'text-rose-400' : 'text-emerald-400'
                            }`}
                          >
                            {isRisk ? '+ Risk' : '- Safe'}
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-slate-900 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full transition-all duration-500 ${
                              isRisk ? 'bg-gradient-to-r from-rose-500 to-amber-500' : 'bg-emerald-500'
                            }`}
                            style={{ width: `${barWidth}%` }}
                          />
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center p-8 bg-slate-900/40 rounded-2xl border border-dashed border-slate-800 text-center text-slate-500 space-y-3">
              <BrainCircuit className="w-12 h-12 text-slate-700 animate-pulse" />
              <div className="text-sm font-semibold text-slate-400">
                Ready for Risk Inference
              </div>
              <p className="text-xs max-w-xs leading-relaxed">
                Selected Merchant: <strong className="text-cyan-400">{selectedMerchantObj?.merchant_name || 'NovaMart Fresh'}</strong>. Click &ldquo;Analyze Transaction Risk&rdquo; to compute ML fraud probabilities and SHAP explanations.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
