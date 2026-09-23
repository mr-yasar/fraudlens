import React, { useState, useEffect, useCallback } from 'react'
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
  DollarSign,
  Smartphone,
  Globe,
  HelpCircle,
  ChevronRight,
  UserCheck,
} from 'lucide-react'
import { paymentApi, customersApi } from '../services/api'

export default function PaymentView({
  onViewExplanation,
  onNavigateToInvestigations,
  onSelectTransaction,
}) {
  // Evaluation progress step state
  const [evalStep, setEvalStep] = useState(0)
  const evalSteps = [
    'Validating transaction payload...',
    'Running ML inference & threshold calculation...',
    'Computing multi-factor risk score...',
    'Generating local SHAP game-theoretic attributions...',
  ]
  // Preset scenarios
  const presets = [
    {
      id: 'low_risk',
      title: 'Scenario A: Low Risk (Routine)',
      badge: 'ALLOW EXPECTED',
      badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
      description: 'Known customer, routine $45 transaction, recognized browser, domestic CA region.',
      data: {
        customer_id: 'CUST-1001',
        amount: 45.0,
        currency: 'USD',
        merchant_name: 'Whole Foods Market',
        merchant_category: 'grocery',
        payment_method: 'credit_card',
        device_type: 'web',
        location: 'CA',
        transaction_country: 'US',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },
    {
      id: 'medium_risk',
      title: 'Scenario B: Medium Risk (Moderate Surge)',
      badge: 'REVIEW EXPECTED',
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
      description: 'Known customer, $450 electronics purchase (4x avg), new mobile device, 1 prior failure.',
      data: {
        customer_id: 'CUST-1002',
        amount: 450.0,
        currency: 'USD',
        merchant_name: 'Best Buy Electronics',
        merchant_category: 'electronics',
        payment_method: 'credit_card',
        device_type: 'mobile_android',
        location: 'CA',
        transaction_country: 'US',
        transaction_type: 'online_payment',
        failed_attempts: 1,
      },
    },
    {
      id: 'high_risk',
      title: 'Scenario C: High Risk (Account Takeover)',
      badge: 'BLOCK EXPECTED',
      badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
      description: '50x amount surge ($6,800), luxury crypto vendor, novel Tor/Linux client, cross-border origin, 4 failed attempts.',
      data: {
        customer_id: 'CUST-1001',
        amount: 6800.0,
        currency: 'USD',
        merchant_name: 'Apex Luxury Bullion',
        merchant_category: 'luxury_goods',
        payment_method: 'credit_card',
        device_type: 'unknown_bot',
        location: 'Lagos',
        transaction_country: 'NG',
        transaction_type: 'online_payment',
        failed_attempts: 4,
      },
    },
    {
      id: 'cold_start',
      title: 'Scenario D: Cold-Start (New Customer)',
      badge: 'SAFE ALLOW',
      badgeColor: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60',
      description: 'Brand new customer profile with 0 prior transactions, normal $60 coffee purchase. Should NOT false-alarm.',
      data: {
        customer_id: 'CUST-NEW-' + Math.floor(1000 + Math.random() * 9000),
        amount: 60.0,
        currency: 'USD',
        merchant_name: 'Blue Bottle Coffee',
        merchant_category: 'dining',
        payment_method: 'credit_card',
        device_type: 'mobile_ios',
        location: 'NY',
        transaction_country: 'US',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },
  ]

  const [activePreset, setActivePreset] = useState('low_risk')
  const [formData, setFormData] = useState(presets[0].data)
  const [customerProfile, setCustomerProfile] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)

  // Pre-auth decision state
  const [evaluating, setEvaluating] = useState(false)
  const [decisionResult, setDecisionResult] = useState(null)
  const [error, setError] = useState(null)

  // Fetch customer profile when customer_id changes
  const loadCustomerProfile = useCallback(async (customerId) => {
    if (!customerId) return
    setProfileLoading(true)
    try {
      const profile = await paymentApi.getCustomerProfile(customerId)
      setCustomerProfile(profile)
    } catch (err) {
      setCustomerProfile(null)
    } finally {
      setProfileLoading(false)
    }
  }, [])

  useEffect(() => {
    loadCustomerProfile(formData.customer_id)
  }, [formData.customer_id, loadCustomerProfile])

  const handleSelectPreset = (preset) => {
    setActivePreset(preset.id)
    setFormData(preset.data)
    setDecisionResult(null)
    setError(null)
  }

  const handleInputChange = (field, value) => {
    setFormData((prev) => ({
      ...prev,
      [field]: field === 'amount' || field === 'failed_attempts' ? (value === '' ? '' : Number(value)) : value,
    }))
    setActivePreset('custom')
  }

  const handleInitiatePayment = async (e) => {
    e.preventDefault()
    setEvaluating(true)
    setError(null)
    setDecisionResult(null)

    try {
      const result = await paymentApi.initiate(formData)
      setDecisionResult(result)
      // Refresh customer profile to reflect updated transaction counts
      loadCustomerProfile(formData.customer_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Pre-authorization evaluation failed')
    } finally {
      setEvaluating(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900/90 to-cyan-950/40 p-6 rounded-2xl border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-full bg-cyan-500/5 blur-3xl pointer-events-none" />
        <div className="flex items-center gap-4 relative z-10">
          <div className="p-3.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-2xl shadow-lg shadow-cyan-500/20 text-white">
            <CreditCard className="w-7 h-7" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-wide">Transaction Risk Simulator</h1>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800">
                REAL-TIME RISK CHECK
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl">
              Evaluates application signals, customer behavioral deviations, and ML risk scores for newly submitted transactions.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono bg-slate-950/80 px-4 py-2 rounded-xl border border-slate-800 text-slate-400">
          <Lock className="w-3.5 h-3.5 text-cyan-400" />
          <span>Evaluation Mode: <strong className="text-emerald-400">REAL-TIME RISK INTERCEPTOR</strong></span>
        </div>
      </div>

      {/* Preset Scenario Selector */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {presets.map((preset) => {
          const isSelected = activePreset === preset.id
          return (
            <button
              key={preset.id}
              type="button"
              onClick={() => handleSelectPreset(preset)}
              className={`text-left p-3.5 rounded-xl border transition-all duration-200 relative ${
                isSelected
                  ? 'bg-slate-900/90 border-cyan-500/80 shadow-lg shadow-cyan-950/50'
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

      {/* Main Grid: Form + Live Customer Profile */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Payment Initiation Form */}
        <div className="lg:col-span-7 bg-slate-900/60 border border-slate-800/80 backdrop-blur-md rounded-2xl p-6 shadow-xl space-y-5">
          <div className="flex items-center justify-between border-b border-slate-800/80 pb-4">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-cyan-400" />
              <h2 className="text-sm font-bold text-white uppercase tracking-wider">Submitted Transaction Details</h2>
            </div>
            <span className="text-[11px] font-mono text-slate-400">Zero Sensitive Credentials Stored</span>
          </div>

          <form onSubmit={handleInitiatePayment} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Customer ID */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Customer Identifier</label>
                <div className="relative">
                  <input
                    type="text"
                    required
                    value={formData.customer_id}
                    onChange={(e) => handleInputChange('customer_id', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono"
                    placeholder="e.g. CUST-1001"
                  />
                </div>
              </div>

              {/* Amount & Currency */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Payment Amount ($ USD)</label>
                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500 text-xs">
                    $
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
              </div>

              {/* Merchant Name */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Merchant / Recipient</label>
                <input
                  type="text"
                  required
                  value={formData.merchant_name}
                  onChange={(e) => handleInputChange('merchant_name', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition"
                  placeholder="Merchant name"
                />
              </div>

              {/* Merchant Category */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Merchant Sector</label>
                <select
                  value={formData.merchant_category}
                  onChange={(e) => handleInputChange('merchant_category', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="retail">Retail Shopping</option>
                  <option value="grocery">Grocery & Supermarket</option>
                  <option value="dining">Dining & Restaurants</option>
                  <option value="electronics">Consumer Electronics</option>
                  <option value="travel">Airlines & Travel</option>
                  <option value="luxury_goods">Luxury Goods & Jewelry (High Risk)</option>
                  <option value="crypto">Cryptocurrency Exchange (High Risk)</option>
                </select>
              </div>

              {/* Device Type */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Hardware / Client Device</label>
                <select
                  value={formData.device_type}
                  onChange={(e) => handleInputChange('device_type', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="web">Web Browser (Desktop Chrome/Safari)</option>
                  <option value="mobile_ios">iOS Mobile App (iPhone)</option>
                  <option value="mobile_android">Android Mobile App</option>
                  <option value="pos">In-Person Point of Sale</option>
                  <option value="unknown_bot">Unrecognized Automated Client (Tor/Linux)</option>
                </select>
              </div>

              {/* Geo Location / Country */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Origin Region &amp; Country</label>
                <div className="grid grid-cols-2 gap-2">
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => handleInputChange('location', e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono"
                    placeholder="Region (CA/NY)"
                  />
                  <input
                    type="text"
                    maxLength={2}
                    value={formData.transaction_country}
                    onChange={(e) => handleInputChange('transaction_country', e.target.value.toUpperCase())}
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono uppercase"
                    placeholder="Country (US)"
                  />
                </div>
              </div>

              {/* Failed Authentication Attempts */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Prior Failed Password Attempts</label>
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

              {/* Payment Method */}
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Payment Instrument</label>
                <select
                  value={formData.payment_method}
                  onChange={(e) => handleInputChange('payment_method', e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition"
                >
                  <option value="credit_card">Credit Card (Visa/Mastercard/Amex)</option>
                  <option value="debit_card">Debit Card</option>
                  <option value="upi">Instant UPI / Fast Bank Transfer</option>
                </select>
              </div>
            </div>

            {/* Error banner */}
            {error && (
              <div className="p-3 bg-rose-950/80 border border-rose-800/80 rounded-xl text-rose-300 text-xs flex items-center gap-2">
                <XCircle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{error}</span>
              </div>
            )}

            {/* Submit Action */}
            <div className="pt-2">
              <button
                type="submit"
                disabled={evaluating}
                className="w-full py-3 px-6 bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-cyan-900/30 flex items-center justify-center gap-2 transition duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
              >
                {evaluating ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Evaluating Signals &amp; Risk Score...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-4 h-4" />
                    <span>EVALUATE TRANSACTION RISK</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        {/* Live Customer Behavioral Baseline Card */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/60 border border-slate-800/80 backdrop-blur-md rounded-2xl p-5 shadow-xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center gap-2">
                <UserCheck className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">Customer Baseline Profile</h3>
              </div>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">
                {customerProfile?.is_cold_start ? 'COLD START' : 'ESTABLISHED'}
              </span>
            </div>

            {profileLoading ? (
              <div className="py-8 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                <span>Loading customer ledger history...</span>
              </div>
            ) : customerProfile ? (
              <div className="space-y-3 text-xs">
                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Historical Avg Amount</div>
                    <div className="text-sm font-bold text-white font-mono mt-0.5">
                      ${customerProfile.historical_avg_amount.toFixed(2)}
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Historical Max Amount</div>
                    <div className="text-sm font-bold text-white font-mono mt-0.5">
                      ${customerProfile.historical_max_amount.toFixed(2)}
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Total Past Transactions</div>
                    <div className="text-sm font-bold text-cyan-400 font-mono mt-0.5">
                      {customerProfile.total_transactions} records
                    </div>
                  </div>

                  <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">Account Tenure</div>
                    <div className="text-sm font-bold text-slate-300 font-mono mt-0.5">
                      {Math.round(customerProfile.account_age_days)} days
                    </div>
                  </div>
                </div>

                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 space-y-2">
                  <div className="text-[10px] text-slate-500 uppercase font-mono">Recognized Hardware Signatures</div>
                  <div className="flex flex-wrap gap-1.5">
                    {customerProfile.known_devices && customerProfile.known_devices.length > 0 ? (
                      customerProfile.known_devices.map((dev, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700 text-[10px] font-mono">
                          {dev}
                        </span>
                      ))
                    ) : (
                      <span className="text-slate-500 text-[11px] italic">None yet (Cold-start new account)</span>
                    )}
                  </div>
                </div>

                <div className="p-3 bg-slate-950/80 rounded-xl border border-slate-800/80 space-y-2">
                  <div className="text-[10px] text-slate-500 uppercase font-mono">Historical Modal Locations</div>
                  <div className="flex flex-wrap gap-1.5">
                    {customerProfile.usual_locations && customerProfile.usual_locations.length > 0 ? (
                      customerProfile.usual_locations.map((loc, i) => (
                        <span key={i} className="px-2 py-0.5 rounded bg-slate-900 text-cyan-300 border border-cyan-800/60 text-[10px] font-mono">
                          {loc}
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
                Customer record will be initialized on authorization check.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Authoritative Pre-Authorization Decision Outcome Card */}
      {decisionResult && (
        <div className={`p-6 rounded-2xl border transition-all duration-500 shadow-2xl space-y-6 ${
          decisionResult.decision === 'ALLOW'
            ? 'bg-gradient-to-b from-slate-900 via-slate-900 to-emerald-950/30 border-emerald-700/60 shadow-emerald-950/20'
            : decisionResult.decision === 'REVIEW'
            ? 'bg-gradient-to-b from-slate-900 via-slate-900 to-amber-950/30 border-amber-700/60 shadow-amber-950/20'
            : 'bg-gradient-to-b from-slate-900 via-slate-900 to-rose-950/30 border-rose-700/60 shadow-rose-950/20'
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
                    {decisionResult.decision === 'ALLOW' && 'PRE-AUTHORIZATION APPROVED'}
                    {decisionResult.decision === 'REVIEW' && 'PRE-AUTHORIZATION FLAGGED FOR REVIEW'}
                    {decisionResult.decision === 'BLOCK' && 'PRE-AUTHORIZATION PROHIBITED (BLOCKED)'}
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
                <div className="text-[10px] text-slate-400 font-mono uppercase">Decision Latency</div>
                <div className="text-xs font-mono font-bold text-white">{decisionResult.processing_time_ms} ms</div>
              </div>
            </div>
          </div>

          {/* Metric Telemetry Row */}
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
              <div className="text-[10px] text-slate-400 font-mono uppercase">Multi-Factor Risk Score</div>
              <div className="text-xl font-extrabold font-mono text-white mt-1">
                {decisionResult.risk_score} <span className="text-xs text-slate-500">/ 100</span>
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Synthetic Decision Score
              </div>
            </div>

            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Behavioural Deviation</div>
              <div className="text-xl font-extrabold font-mono text-purple-300 mt-1">
                {(decisionResult.behavioural_deviation_score * 100).toFixed(0)}%
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                vs Historical Customer Profile
              </div>
            </div>

            <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
              <div className="text-[10px] text-slate-400 font-mono uppercase">Provider Ready State</div>
              <div className={`text-base font-bold font-mono mt-1 ${
                decisionResult.ready_for_provider ? 'text-emerald-400' : 'text-slate-500'
              }`}>
                {decisionResult.ready_for_provider ? 'READY FOR SANDBOX' : 'HOLD / PROHIBITED'}
              </div>
              <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                Phase 8 Local Pre-Auth Complete
              </div>
            </div>
          </div>

          {/* Triggered Rules Breakdown */}
          {decisionResult.triggered_rules && decisionResult.triggered_rules.length > 0 && (
            <div className="space-y-2">
              <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                <span>Triggered Gateway Security Rules</span>
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
                      {/* Visual Contribution Bar */}
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

          {/* Provider Execution / Sandbox Receipt or Case Alert */}
          <div className="p-4 bg-slate-950/90 rounded-xl border border-slate-800 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
            <div>
              <div className="text-[10px] text-slate-500 uppercase font-mono">Payment Lifecycle Status</div>
              <div className="flex items-center gap-2 mt-0.5">
                <span className="font-mono font-bold text-white">{decisionResult.lifecycle_status || 'CREATED'}</span>
                {decisionResult.case_id && (
                  <span className="px-2 py-0.5 rounded bg-amber-950 text-amber-300 border border-amber-800 text-[10px] font-mono">
                    Case Opened: {decisionResult.case_id}
                  </span>
                )}
                {decisionResult.external_payment_id && (
                  <span className="px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800 text-[10px] font-mono">
                    Sandbox ID: {decisionResult.external_payment_id}
                  </span>
                )}
              </div>
            </div>

            {decisionResult.decision === 'REVIEW' && decisionResult.case_id && (
              <div className="text-amber-400 font-medium text-[11px] flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5" />
                <span>Held in Review Queue for Investigator Sign-Off</span>
              </div>
            )}
            {decisionResult.decision === 'ALLOW' && (
              <div className="text-emerald-400 font-medium text-[11px] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Submitted to Payment Provider Sandbox</span>
              </div>
            )}
            {decisionResult.decision === 'BLOCK' && (
              <div className="text-rose-400 font-medium text-[11px] flex items-center gap-1.5">
                <XCircle className="w-3.5 h-3.5" />
                <span>Gateway Rejected: Submission Terminated</span>
              </div>
            )}
          </div>

          {/* Fast Navigation & Action Routing Bar */}
          <div className="p-3 bg-slate-950/60 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="text-slate-400 text-[11px] font-mono">
              Investigation &amp; Audit Trail Active for Token <strong className="text-cyan-400">{decisionResult.transaction_id}</strong>
            </div>
            <div className="flex items-center gap-2">
              {onViewExplanation && (
                <button
                  type="button"
                  onClick={() => onViewExplanation(decisionResult.transaction_id)}
                  className="px-3 py-1.5 rounded-xl bg-purple-900/60 hover:bg-purple-900 text-purple-200 border border-purple-700 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  Full SHAP Breakdown
                </button>
              )}
              {onNavigateToInvestigations && (decisionResult.case_id || decisionResult.risk_level === 'HIGH' || decisionResult.decision === 'REVIEW') && (
                <button
                  type="button"
                  onClick={onNavigateToInvestigations}
                  className="px-3 py-1.5 rounded-xl bg-amber-900/60 hover:bg-amber-900 text-amber-200 border border-amber-700 text-xs font-semibold transition flex items-center gap-1.5"
                >
                  <ShieldAlert className="w-3.5 h-3.5" />
                  Go to Investigation Cases &rarr;
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
