import React, { useState, useEffect, useCallback } from 'react'
import {
  CreditCard,
  Zap,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowRight,
  Sparkles,
  Laptop,
  Smartphone,
  Globe,
  RefreshCw,
  Search,
  Filter,
  Eye,
  KeyRound,
  ShieldX,
} from 'lucide-react'
import { premiumApi } from '../../services/api'
import PremiumVerificationModal from './PremiumVerificationModal'

export default function PremiumTransactionCenter({ user }) {
  // Scenario and Form State
  const [scenarios, setScenarios] = useState([])
  const [activeScenario, setActiveScenario] = useState(null)
  const [amount, setAmount] = useState('14500')
  const [recipient, setRecipient] = useState('Cloudflare Global Services')
  const [deviceId, setDeviceId] = useState('dev-mbp-m3')
  const [deviceName, setDeviceName] = useState('MacBook Pro M3 Max')
  const [location, setLocation] = useState('Mumbai / Cyber City')
  const [transactionType, setTransactionType] = useState('WIRE_TRANSFER')
  const [transactionHour, setTransactionHour] = useState(14)

  // Execution & Evaluation Result State
  const [evaluating, setEvaluating] = useState(false)
  const [evalResult, setEvalResult] = useState(null)
  const [error, setError] = useState(null)

  // Verification Modal State
  const [activeChallengeTx, setActiveChallengeTx] = useState(null)
  const [isVerificationOpen, setIsVerificationOpen] = useState(false)

  // Transaction Ledger Table State
  const [transactions, setTransactions] = useState([])
  const [loadingLedger, setLoadingLedger] = useState(true)
  const [selectedTxDetail, setSelectedTxDetail] = useState(null)

  // Load scenarios & transactions
  const loadInitialData = useCallback(async () => {
    try {
      setLoadingLedger(true)
      const [scenariosRes, txRes] = await Promise.all([
        premiumApi.getScenarios(),
        premiumApi.getTransactions({ limit: 50 }),
      ])
      setScenarios(scenariosRes)
      setTransactions(txRes.transactions || [])
      setError(null)
    } catch (err) {
      setError(err.message || 'Failed to load scenarios or transaction ledger.')
    } finally {
      setLoadingLedger(false)
    }
  }, [])

  useEffect(() => {
    loadInitialData()
  }, [loadInitialData])

  // Select a preset demo scenario
  const applyScenario = (sc) => {
    setActiveScenario(sc.id)
    setAmount(String(sc.amount))
    setRecipient(sc.recipient)
    setDeviceId(sc.device_id)
    setDeviceName(sc.device_name)
    setLocation(sc.location)
    setTransactionType(sc.transaction_type || 'WIRE_TRANSFER')
    setTransactionHour(sc.transaction_hour ?? 14)
    setEvalResult(null)
  }

  // Execute or stage transaction
  const handleExecute = async (e) => {
    e?.preventDefault()
    if (!amount || !recipient || evaluating) return
    setEvaluating(true)
    setError(null)
    setEvalResult(null)

    try {
      const payload = {
        amount: parseFloat(amount),
        recipient: recipient.trim(),
        device_id: deviceId,
        device_name: deviceName,
        location: location.trim(),
        transaction_type: transactionType,
        transaction_hour: parseInt(transactionHour, 10),
      }

      const res = await premiumApi.evaluateTransaction(payload)
      setEvalResult(res)

      // If Step-Up verification or temporary hold with challenge was returned, open challenge modal
      if (res.verification_challenge) {
        setActiveChallengeTx(res)
        setIsVerificationOpen(true)
      }

      // Refresh Ledger
      const updatedTxs = await premiumApi.getTransactions({ limit: 50 })
      setTransactions(updatedTxs.transactions || [])
    } catch (err) {
      setError(err.message || 'Transaction evaluation failed.')
    } finally {
      setEvaluating(false)
    }
  }

  // Quick 1-click Run Scenario Endpoint
  const handleRunScenarioDirectly = async (scenarioId) => {
    setEvaluating(true)
    setError(null)
    setEvalResult(null)
    try {
      const res = await premiumApi.runScenario(scenarioId)
      setEvalResult(res)
      setActiveScenario(scenarioId)

      if (res.verification_challenge) {
        setActiveChallengeTx(res)
        setIsVerificationOpen(true)
      }

      const updatedTxs = await premiumApi.getTransactions({ limit: 50 })
      setTransactions(updatedTxs.transactions || [])
    } catch (err) {
      setError(err.message || 'Failed to execute scenario.')
    } finally {
      setEvaluating(false)
    }
  }

  const handleVerificationComplete = async (res) => {
    setEvalResult((prev) => (prev ? { ...prev, status: 'SUCCESS', decision: 'ALLOW' } : prev))
    const updatedTxs = await premiumApi.getTransactions({ limit: 50 })
    setTransactions(updatedTxs.transactions || [])
  }

  const getRiskColor = (level) => {
    switch (level) {
      case 'LOW':
        return 'text-emerald-400 bg-emerald-950/80 border-emerald-600/70'
      case 'MEDIUM':
        return 'text-amber-400 bg-amber-950/80 border-amber-600/70'
      case 'HIGH':
        return 'text-rose-400 bg-rose-950/80 border-rose-600/70'
      case 'CRITICAL':
        return 'text-purple-300 bg-purple-950/90 border-purple-500/80 shadow-[0_0_15px_rgba(168,85,247,0.4)]'
      default:
        return 'text-slate-300 bg-slate-900 border-slate-700'
    }
  }

  return (
    <div className="space-y-8 animate-fade-in text-slate-100">
      {/* Header Banner */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-black text-white font-mono tracking-tight flex items-center gap-2">
              <Zap className="w-5 h-5 text-indigo-400" />
              EXECUTIVE TRANSACTION &amp; RISK ENGINE CENTER
            </h2>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-700 font-bold">
              ENTERPRISE SPEC
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Test and evaluate multi-signal risk decisions across Scenarios A, B, C, D with real ML &amp; cryptographic step-up challenges.
          </p>
        </div>

        <button
          onClick={loadInitialData}
          className="self-start md:self-auto px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-xs font-mono text-slate-300 hover:text-white flex items-center gap-2 transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loadingLedger ? 'animate-spin text-indigo-400' : ''}`} />
          <span>Refresh Ledger</span>
        </button>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-2xl bg-rose-950/80 border border-rose-600 text-rose-200 text-xs flex items-center gap-2.5 animate-shake">
          <AlertTriangle className="w-4 h-4 shrink-0 text-rose-400" />
          <span className="font-semibold">{error}</span>
        </div>
      )}

      {/* 1-Click Standard Pre-Configured Scenarios A, B, C, D (Section 38) */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-mono uppercase tracking-wider font-extrabold text-indigo-300 flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-indigo-400" />
            STANDARDIZED TEST SCENARIOS (SECTION 38 SPECIFICATION)
          </h3>
          <span className="text-[10px] font-mono text-slate-400">Click scenario card to stage or run</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {scenarios.map((sc) => {
            const isSelected = activeScenario === sc.id
            const isA = sc.id.includes('scenario_a')
            const isB = sc.id.includes('scenario_b')
            const isC = sc.id.includes('scenario_c')
            const isD = sc.id.includes('scenario_d')

            const accentColor = isA
              ? 'border-emerald-700/60 hover:border-emerald-500 from-emerald-950/30'
              : isB
              ? 'border-amber-700/60 hover:border-amber-500 from-amber-950/30'
              : isC
              ? 'border-rose-700/60 hover:border-rose-500 from-rose-950/30'
              : 'border-purple-600/70 hover:border-purple-400 from-purple-950/40 shadow-[0_0_20px_rgba(168,85,247,0.25)]'

            return (
              <div
                key={sc.id}
                className={`p-4 rounded-2xl bg-gradient-to-b ${accentColor} to-slate-950/90 border-2 transition-all duration-200 flex flex-col justify-between gap-3 relative ${
                  isSelected ? 'ring-2 ring-indigo-400 scale-[1.02]' : ''
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-extrabold text-xs text-white uppercase truncate">
                      {sc.name.split('—')[0]}
                    </span>
                    <span
                      className={`text-[9px] font-mono font-bold px-1.5 py-0.5 rounded border ${
                        isA
                          ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                          : isB
                          ? 'bg-amber-950 text-amber-300 border-amber-700'
                          : isC
                          ? 'bg-rose-950 text-rose-300 border-rose-700'
                          : 'bg-purple-950 text-purple-200 border-purple-600'
                      }`}
                    >
                      {isA ? 'LOW RISK' : isB ? 'MEDIUM RISK' : isC ? 'HIGH RISK' : 'CRITICAL'}
                    </span>
                  </div>

                  <div className="font-mono text-base font-black text-white">
                    ₹{Number(sc.amount).toLocaleString('en-IN')}
                  </div>

                  <p className="text-[11px] text-slate-300 line-clamp-2 leading-tight">
                    {sc.description}
                  </p>

                  <div className="space-y-1 pt-1 border-t border-slate-800/80">
                    {sc.signals?.map((sig, sIdx) => (
                      <div key={sIdx} className="text-[10px] font-mono text-slate-400 flex items-center gap-1.5 truncate">
                        <span className="w-1 h-1 rounded-full bg-slate-500" />
                        <span className="truncate">{sig}</span>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="flex items-center gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => applyScenario(sc)}
                    className="flex-1 py-1.5 px-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 text-[11px] font-mono text-slate-200 font-semibold transition"
                  >
                    Stage Form
                  </button>
                  <button
                    type="button"
                    onClick={() => handleRunScenarioDirectly(sc.id)}
                    disabled={evaluating}
                    className="py-1.5 px-3 rounded-xl bg-indigo-900/90 hover:bg-indigo-800 border border-indigo-500/70 text-[11px] font-mono text-white font-bold transition flex items-center gap-1 shadow-md"
                  >
                    <span>Run</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {/* Main Form & Real-Time Adaptive Evaluation Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left 6 Cols: Transaction Dispatch Form */}
        <div className="lg:col-span-6 p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-mono uppercase tracking-wider font-extrabold text-white flex items-center gap-2">
              <CreditCard className="w-4 h-4 text-indigo-400" />
              TRANSACTION DISPATCH ENGINE
            </h3>
            <span className="text-[10px] font-mono text-slate-400">Adaptive AI Pipeline</span>
          </div>

          <form onSubmit={handleExecute} className="space-y-4">
            {/* Amount */}
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-300 font-mono">
                TRANSFER AMOUNT (INR)
              </label>
              <div className="relative">
                <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 font-mono font-bold text-sm">
                  ₹
                </span>
                <input
                  type="number"
                  required
                  min="1"
                  step="any"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="14500"
                  className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 rounded-xl pl-8 pr-4 py-2.5 text-white font-mono text-sm outline-none transition"
                />
              </div>
            </div>

            {/* Recipient / Beneficiary */}
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-300 font-mono">
                BENEFICIARY RECIPIENT
              </label>
              <input
                type="text"
                required
                value={recipient}
                onChange={(e) => setRecipient(e.target.value)}
                placeholder="Cloudflare Global Services"
                className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400 rounded-xl px-4 py-2.5 text-white font-mono text-xs outline-none transition"
              />
            </div>

            {/* Device Profile */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="block text-[11px] font-semibold text-slate-300 font-mono">
                  HARDWARE IDENTIFIER
                </label>
                <select
                  value={deviceId}
                  onChange={(e) => {
                    setDeviceId(e.target.value)
                    if (e.target.value === 'dev-mbp-m3') setDeviceName('MacBook Pro M3 Max')
                    else if (e.target.value === 'dev-iphone-15pm') setDeviceName('iPhone 15 Pro Max')
                    else setDeviceName('Unregistered Hardware Node')
                  }}
                  className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-400 rounded-xl px-3 py-2 text-white font-mono text-xs outline-none"
                >
                  <option value="dev-mbp-m3">MacBook Pro M3 (Trusted Enclave)</option>
                  <option value="dev-iphone-15pm">iPhone 15 Pro (Biometric)</option>
                  <option value="dev-unregistered-mac-lon">Unregistered Mac (Roaming)</option>
                  <option value="dev-unknown-linux-node">Unknown Rooted Linux Node</option>
                </select>
              </div>

              <div className="space-y-1">
                <label className="block text-[11px] font-semibold text-slate-300 font-mono">
                  ORIGINATING GEOGRAPHY
                </label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="Mumbai / Cyber City"
                  className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-400 rounded-xl px-3 py-2 text-white font-mono text-xs outline-none"
                />
              </div>
            </div>

            {/* Hour of Day & Channel */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <label className="block text-[11px] font-semibold text-slate-300 font-mono">
                  INITIATION TIME (00-23 HRS)
                </label>
                <input
                  type="number"
                  min="0"
                  max="23"
                  value={transactionHour}
                  onChange={(e) => setTransactionHour(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-400 rounded-xl px-3 py-2 text-white font-mono text-xs outline-none"
                />
              </div>

              <div className="space-y-1">
                <label className="block text-[11px] font-semibold text-slate-300 font-mono">
                  PAYMENT CHANNEL
                </label>
                <select
                  value={transactionType}
                  onChange={(e) => setTransactionType(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 focus:border-indigo-400 rounded-xl px-3 py-2 text-white font-mono text-xs outline-none"
                >
                  <option value="WIRE_TRANSFER">Wire Transfer (RTGS)</option>
                  <option value="INSTANT_SETTLEMENT">Instant Enterprise Settlement</option>
                  <option value="CROSS_BORDER_ESCROW">Cross-Border Escrow</option>
                </select>
              </div>
            </div>

            {/* Execute Button */}
            <button
              type="submit"
              disabled={evaluating}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-purple-600 to-indigo-600 hover:from-indigo-500 hover:to-purple-500 disabled:opacity-50 text-white font-mono text-xs font-bold uppercase tracking-wider shadow-[0_0_25px_rgba(99,102,241,0.5)] flex items-center justify-center gap-2 transition"
            >
              {evaluating ? (
                <>
                  <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  <span>Evaluating Risk Signals &amp; Enclave Shield...</span>
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4" />
                  <span>Evaluate &amp; Execute Transaction</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Right 6 Cols: Explainable Risk Breakdown & Decision Card */}
        <div className="lg:col-span-6 space-y-4">
          {evalResult ? (
            <div className="p-6 rounded-3xl bg-slate-900/90 border-2 border-indigo-500/60 shadow-[0_0_35px_rgba(99,102,241,0.3)] space-y-4 animate-fade-in">
              <div className="flex items-center justify-between pb-3 border-b border-slate-800">
                <div>
                  <div className="text-[10px] font-mono text-slate-400 uppercase">Adaptive Evaluation Result</div>
                  <h3 className="text-base font-black text-white font-mono">{evalResult.transaction_id}</h3>
                </div>
                <div className={`px-3 py-1 rounded-xl border text-xs font-mono font-bold ${getRiskColor(evalResult.risk_level)}`}>
                  {evalResult.risk_level} • {evalResult.risk_score}/100
                </div>
              </div>

              {/* Decision Alert Banner */}
              <div
                className={`p-4 rounded-2xl border flex items-start gap-3 ${
                  evalResult.risk_level === 'LOW'
                    ? 'bg-emerald-950/80 border-emerald-600/70 text-emerald-200'
                    : evalResult.risk_level === 'MEDIUM'
                    ? 'bg-amber-950/80 border-amber-600/70 text-amber-200'
                    : 'bg-rose-950/80 border-rose-600/70 text-rose-200'
                }`}
              >
                {evalResult.risk_level === 'LOW' ? (
                  <ShieldCheck className="w-5 h-5 text-emerald-400 shrink-0 mt-0.5" />
                ) : (
                  <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
                )}
                <div>
                  <div className="font-mono font-bold text-xs uppercase tracking-wide">
                    DECISION: {evalResult.decision} ({evalResult.status})
                  </div>
                  <div className="text-xs mt-0.5 opacity-90">{evalResult.next_step}</div>
                </div>
              </div>

              {/* Explainable Contributing Factors (Section 18) */}
              <div className="space-y-2">
                <div className="text-xs font-mono font-bold text-slate-300 uppercase tracking-wide">
                  EXPLAINABLE RISK FACTORS:
                </div>
                <div className="space-y-1.5">
                  {evalResult.contributing_factors?.map((factor, fIdx) => (
                    <div
                      key={fIdx}
                      className="p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-300 flex items-start gap-2"
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-indigo-400 shrink-0 mt-1.5" />
                      <span>{factor}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Action Button if Challenge Required */}
              {evalResult.verification_challenge && evalResult.status !== 'SUCCESS' && (
                <button
                  type="button"
                  onClick={() => {
                    setActiveChallengeTx(evalResult)
                    setIsVerificationOpen(true)
                  }}
                  className="w-full py-2.5 px-4 rounded-xl bg-amber-600 hover:bg-amber-500 text-slate-950 font-mono text-xs font-bold uppercase tracking-wider flex items-center justify-center gap-2 transition"
                >
                  <KeyRound className="w-4 h-4" />
                  <span>Complete Step-Up Challenge (Passcode OTP)</span>
                </button>
              )}
            </div>
          ) : (
            <div className="p-8 rounded-3xl bg-slate-900/60 border border-slate-800/80 text-center flex flex-col items-center justify-center min-h-[340px] space-y-3">
              <div className="p-4 rounded-2xl bg-indigo-950/60 border border-indigo-800/60 text-indigo-400">
                <Zap className="w-8 h-8 opacity-60" />
              </div>
              <h4 className="font-mono font-bold text-sm text-slate-300">Awaiting Transaction Execution</h4>
              <p className="text-xs text-slate-500 max-w-sm leading-relaxed">
                Click a scenario above or dispatch a transaction to view real-time multi-signal score breakdown and explainable risk factors.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Complete Historical Transaction Ledger (Section 21) */}
      <div className="p-6 rounded-3xl bg-slate-900/80 border border-slate-800 shadow-xl space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-base font-bold text-white font-mono flex items-center gap-2">
              <Clock className="w-4 h-4 text-cyan-400" />
              TRANSACTION AUDIT LEDGER (SECTION 21 SPEC)
            </h3>
            <p className="text-xs text-slate-400">
              Complete tamper-resistant transaction log with risk scores, decisions, and verification states.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse font-mono text-xs">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 bg-slate-950/60">
                <th className="p-3">TRANSACTION ID</th>
                <th className="p-3">TIMESTAMP</th>
                <th className="p-3">RECIPIENT</th>
                <th className="p-3">AMOUNT</th>
                <th className="p-3">RISK SCORE</th>
                <th className="p-3">DECISION</th>
                <th className="p-3">STATUS</th>
                <th className="p-3 text-right">ACTION</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {transactions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="p-6 text-center text-slate-500">
                    No transactions registered in this enterprise tenant partition yet.
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => (
                  <tr key={tx.id || tx.transaction_id} className="hover:bg-slate-800/40 transition">
                    <td className="p-3 font-bold text-cyan-400">{tx.transaction_id}</td>
                    <td className="p-3 text-slate-400">
                      {tx.created_at ? new Date(tx.created_at).toLocaleString() : 'Recent'}
                    </td>
                    <td className="p-3 text-white font-semibold">{tx.recipient || 'Verified Merchant'}</td>
                    <td className="p-3 font-bold text-white">
                      ₹{Number(tx.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                    </td>
                    <td className="p-3">
                      <span className={`px-2 py-0.5 rounded border text-[10px] font-bold ${getRiskColor(tx.risk_level)}`}>
                        {tx.risk_score}/100 • {tx.risk_level}
                      </span>
                    </td>
                    <td className="p-3 text-slate-300 font-semibold">{tx.decision || 'ALLOW'}</td>
                    <td className="p-3">
                      <span className={`text-[10px] font-bold uppercase ${tx.status === 'SUCCESS' ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {tx.status}
                      </span>
                    </td>
                    <td className="p-3 text-right">
                      <button
                        type="button"
                        onClick={() => setSelectedTxDetail(tx)}
                        className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                        title="View Full Risk Breakdown"
                      >
                        <Eye className="w-3.5 h-3.5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Transaction Detail Modal */}
      {selectedTxDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md">
          <div className="relative w-full max-w-xl rounded-3xl bg-slate-900 border-2 border-indigo-500/60 p-6 space-y-4 shadow-2xl text-slate-100">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <h3 className="font-mono font-bold text-base text-white">
                TRANSACTION AUDIT INSPECTOR • {selectedTxDetail.transaction_id}
              </h3>
              <button
                onClick={() => setSelectedTxDetail(null)}
                className="text-slate-400 hover:text-white text-sm font-bold"
              >
                ✕
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400 block">Amount</span>
                <span className="text-base font-bold text-white">
                  ₹{Number(selectedTxDetail.amount || 0).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400 block">Recipient</span>
                <span className="text-sm font-bold text-indigo-300">{selectedTxDetail.recipient}</span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400 block">Risk Score &amp; Level</span>
                <span className="text-sm font-bold text-amber-400">
                  {selectedTxDetail.risk_score} / 100 ({selectedTxDetail.risk_level})
                </span>
              </div>
              <div className="p-3 rounded-xl bg-slate-950 border border-slate-800">
                <span className="text-slate-400 block">Decision / Status</span>
                <span className="text-sm font-bold text-emerald-400">
                  {selectedTxDetail.decision} ({selectedTxDetail.status})
                </span>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono space-y-1">
              <span className="text-slate-400 block uppercase font-bold">Metadata &amp; Enclave Fingerprint</span>
              <div className="text-slate-300">Device ID: {selectedTxDetail.device_id || 'dev-mbp-m3'}</div>
              <div className="text-slate-300">Geo Location: {selectedTxDetail.location || 'Mumbai / Cyber City'}</div>
              <div className="text-slate-300">Created: {new Date(selectedTxDetail.created_at).toISOString()}</div>
            </div>

            <button
              onClick={() => setSelectedTxDetail(null)}
              className="w-full py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-mono font-bold text-white transition"
            >
              Close Inspector
            </button>
          </div>
        </div>
      )}

      {/* Verification OTP Modal */}
      <PremiumVerificationModal
        isOpen={isVerificationOpen}
        onClose={() => setIsVerificationOpen(false)}
        transaction={activeChallengeTx}
        onVerificationSuccess={handleVerificationComplete}
      />
    </div>
  )
}
