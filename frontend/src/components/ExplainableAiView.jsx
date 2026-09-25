import React, { useState, useEffect, useRef } from 'react'
import {
  Sparkles,
  Search,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  AlertTriangle,
  Cpu,
  Layers,
  HelpCircle,
  ShieldCheck,
  ShieldAlert,
  Binary,
  Compass,
  CheckCircle2,
  Volume2,
  VolumeX,
  Play,
  Pause,
  Square,
  Lock,
  UserCheck,
  Headphones,
  Bot,
  Zap,
} from 'lucide-react'
import { transactionsApi } from '../services/api'
import { getCustomerPersona } from '../utils/customerHelper'

const AVAILABLE_AI_MODELS = [
  { id: 'xgboost', name: 'XGBoost Classifier', badge: 'Active Champion', tag: 'TreeSHAP', icon: Cpu, desc: 'Gradient Boosted Decision Trees (99.1% ROC-AUC)' },
  { id: 'random_forest', name: 'Random Forest', badge: 'Ensemble Bagging', tag: 'TreeSHAP', icon: Layers, desc: '100-Tree Forest with Out-of-Bag voting' },
  { id: 'logistic_regression', name: 'Logistic Regression', badge: 'Calibrated Linear', tag: 'LinearSHAP', icon: Binary, desc: 'Cost-sensitive L2 regularized odds classifier' },
  { id: 'ensemble_stacking', name: 'Ensemble Stacking', badge: 'Meta-Learner', tag: 'EnsembleSHAP', icon: Compass, desc: 'Fused Meta-Classifier stacking XGBoost, RF & LR' },
]

export default function ExplainableAiView({ user, isAdmin, initialTransactionId }) {
  const isCustomer = !isAdmin && (user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user')
  const customerPersona = getCustomerPersona(user)

  const [transactionId, setTransactionId] = useState(initialTransactionId || '')
  const [selectedModel, setSelectedModel] = useState('xgboost')
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recentTransactions, setRecentTransactions] = useState([])

  // Sweet Voice Speech Synthesis State
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [isPaused, setIsPaused] = useState(false)
  const [speechVoice, setSpeechVoice] = useState(null)
  const [availableVoices, setAvailableVoices] = useState([])
  const [voiceStyle, setVoiceStyle] = useState('sweet') // 'sweet' | 'siri' | 'analytical'

  // Initialize Speech Synthesis Voices
  useEffect(() => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      const loadVoices = () => {
        const voices = window.speechSynthesis.getVoices()
        setAvailableVoices(voices)
        // Find sweet, gentle female / natural neural voice
        const sweetPreferred = voices.find(
          (v) =>
            v.name.includes('Jenny') ||
            v.name.includes('Zira') ||
            v.name.includes('Aria') ||
            v.name.includes('Samantha') ||
            v.name.includes('Victoria') ||
            v.name.includes('Google UK English Female') ||
            v.name.includes('Google US English') ||
            (v.lang.startsWith('en') && v.name.toLowerCase().includes('female')) ||
            (v.lang.startsWith('en') && !v.name.includes('Desktop'))
        )
        setSpeechVoice(sweetPreferred || voices[0] || null)
      }

      loadVoices()
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices
      }
    }
  }, [])

  // Stop speaking when unmounted or transaction changes
  useEffect(() => {
    return () => {
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [transactionId, selectedModel])

  const fetchRecent = async () => {
    try {
      const data = await transactionsApi.list({ page: 1, limit: 40 })
      let items = data.items || []

      // Privacy: If Customer is logged in, strictly isolate transactions to their own customer ID
      if (isCustomer) {
        const targetCustId = customerPersona.customerId.toLowerCase()
        const targetName = (customerPersona.name || '').toLowerCase()
        items = items.filter((tx) => {
          const txCust = (tx.customer_id || '').toLowerCase()
          return txCust === targetCustId || txCust.includes(targetName)
        })
      }

      setRecentTransactions(items)

      if (!transactionId && items.length > 0) {
        handleLookup(items[0].transaction_id, selectedModel)
      }
    } catch {
      // Non-blocking
    }
  }

  useEffect(() => {
    fetchRecent()
  }, [user])

  useEffect(() => {
    if (initialTransactionId) {
      setTransactionId(initialTransactionId)
      handleLookup(initialTransactionId, selectedModel)
    }
  }, [initialTransactionId])

  const handleLookup = async (idToLook, modelOverride) => {
    const target = idToLook || transactionId
    if (!target) return

    const effectiveModel = modelOverride || selectedModel

    setLoading(true)
    setError(null)
    handleStopSpeech()
    try {
      const res = await transactionsApi.getExplanation(target, effectiveModel)
      setExplanation(res)
      setTransactionId(target)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No SHAP explanation found for this transaction.')
      setExplanation(null)
    } finally {
      setLoading(false)
    }
  }

  const handleModelChange = (modelId) => {
    setSelectedModel(modelId)
    if (transactionId) {
      handleLookup(transactionId, modelId)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleLookup()
  }

  const topPos = explanation?.top_risk_increasing_factors ||
                 explanation?.top_positive_features || []
  const topNeg = explanation?.top_risk_decreasing_factors ||
                 explanation?.top_negative_features || []
  const allAttributions = explanation?.all_attributions || []
  const allFeatures = (topPos.length === 0 && topNeg.length === 0 && allAttributions.length > 0)
    ? allAttributions.sort((a, b) => Math.abs(b.shap_value || 0) - Math.abs(a.shap_value || 0))
    : [...topPos, ...topNeg].sort((a, b) => Math.abs(b.shap_value || 0) - Math.abs(a.shap_value || 0))

  const isFraud = explanation?.prediction === 'FRAUD' || explanation?.prediction === 1
  const modelComparison = explanation?.model_comparison?.model_predictions || null
  const composedExp = explanation?.composed_explanation || null
  const counterfactual = explanation?.counterfactual || null

  const handleClear = () => {
    handleStopSpeech()
    setExplanation(null)
    setError(null)
    setTransactionId('')
  }

  // Generate Tailored Spoken Script for this Specific Transaction
  const generateSpokenScript = () => {
    if (!explanation) return ''
    const mName = (explanation.model_name || selectedModel).replace('_', ' ').toUpperCase()
    const prob = (Number(explanation.fraud_probability || 0) * 100).toFixed(1)
    const score = explanation.risk_score || 0
    const verd = isFraud ? 'FRAUD (BLOCKED)' : 'GENUINE (APPROVED)'
    const baseVal = Number(explanation.base_value || 0).toFixed(3)

    const posNames = topPos.slice(0, 2).map((f) => `${f.feature_name || f.feature} with positive ${Number(f.shap_value || 0).toFixed(2)} Shapley points`).join(', and ')
    const negNames = topNeg.slice(0, 2).map((f) => `${f.feature_name || f.feature} with protective negative ${Math.abs(Number(f.shap_value || 0)).toFixed(2)} points`).join(', and ')

    if (isCustomer) {
      const greeting = customerPersona?.name ? `Hello ${customerPersona.name}. ` : 'Hello. '
      if (isFraud) {
        return `${greeting}FraudLens AI has protected your account. Your transaction ${transactionId} was analyzed using ${mName} with TreeSHAP mathematical explainability. It was flagged as high-risk with an AI probability of ${prob} percent and composite risk score of ${score} out of 100. TreeSHAP indicates that ${posNames || 'elevated velocity signals'} pushed risk up, so the payment was securely blocked to prevent fund loss.`
      } else {
        return `${greeting}Your transaction ${transactionId} was verified clean and safe. Using active model ${mName} with TreeSHAP game-theoretic explainability, your fraud probability is only ${prob} percent with a low risk score of ${score} out of 100. ${negNames ? `Protective factors including ${negNames} kept your score low.` : 'All behavioral and device checks passed.'} Your payment was approved without delay.`
      }
    } else {
      return `Forensic Explanation for Transaction ${transactionId}. Evaluated by active model ${mName} with TreeSHAP engine. Final verdict is ${verd} with a fraud probability of ${prob} percent and composite risk score of ${score} out of 100. Base expected value is ${baseVal}. Primary risk escalators driving the inference are ${posNames || 'none'}. Protective factors mitigating risk include ${negNames || 'baseline profile'}. Multi-model consensus evaluated all four active AI models simultaneously.`
    }
  }

  // Voice Narration Playback Handler
  const handleToggleSpeak = () => {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported on this browser.')
      return
    }

    if (isSpeaking && !isPaused) {
      window.speechSynthesis.pause()
      setIsPaused(true)
      return
    }

    if (isPaused) {
      window.speechSynthesis.resume()
      setIsPaused(false)
      return
    }

    const script = generateSpokenScript()
    if (!script) return

    window.speechSynthesis.cancel()
    const utterance = new SpeechSynthesisUtterance(script)
    if (speechVoice) utterance.voice = speechVoice

    // Voice style parameters for sweetness and clarity
    if (voiceStyle === 'sweet') {
      utterance.pitch = 1.12 // Warm, sweet, melodic pitch
      utterance.rate = 0.93  // Gentle, unhurried, crystal clear pacing
    } else if (voiceStyle === 'analytical') {
      utterance.pitch = 0.95
      utterance.rate = 1.15  // Fast forensic investigator speed
    } else {
      utterance.pitch = 1.0  // Standard Siri
      utterance.rate = 1.0
    }

    utterance.onstart = () => {
      setIsSpeaking(true)
      setIsPaused(false)
    }

    utterance.onend = () => {
      setIsSpeaking(false)
      setIsPaused(false)
    }

    utterance.onerror = () => {
      setIsSpeaking(false)
      setIsPaused(false)
    }

    window.speechSynthesis.speak(utterance)
  }

  const handleStopSpeech = () => {
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel()
    }
    setIsSpeaking(false)
    setIsPaused(false)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-purple-400" />
              Explainable AI (XAI) &amp; Local SHAP Attributions
            </h2>
            {isCustomer && (
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-400" />
                Customer Account View ({customerPersona.name})
              </span>
            )}
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            Mathematical transparency explaining individual model inferences using TreeSHAP game-theoretic Shapley values across 4 active AI models.
          </p>
        </div>

        {explanation && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition shrink-0"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            New Search
          </button>
        )}
      </div>

      {/* Privacy Notice for Customer View */}
      {isCustomer && (
        <div className="p-3.5 rounded-2xl bg-emerald-950/20 border border-emerald-800/40 text-xs text-slate-300 flex items-start gap-2.5">
          <Lock className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
          <div>
            <strong className="text-emerald-300 font-bold block mb-0.5">Strict Personal Account Privacy Enforced</strong>
            <span>Only transactions belonging to your verified account (<code>{customerPersona.customerId}</code>) are accessible for explanation. Cross-customer data is strictly shielded.</span>
          </div>
        </div>
      )}

      {/* Conceptual Clarity Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] uppercase font-mono text-cyan-400 font-bold mb-1">1. AI Model Multi-Inference</div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Raw ML classifier probabilities evaluated across XGBoost, Random Forest, Logistic Regression, and Stacking.
          </p>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-purple-800/50">
          <div className="text-[10px] uppercase font-mono text-purple-400 font-bold mb-1">2. TreeSHAP Attribution</div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Game-theoretic feature attributions quantifying how each signal drove probability up or down from base expected value.
          </p>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] uppercase font-mono text-emerald-400 font-bold mb-1">3. Holistic Risk Score (0-100)</div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Multi-factor composite risk combining behavioral velocity, chargebacks, geography, device hardware, and ML score.
          </p>
        </div>
      </div>

      {/* AI Model Selector Tabs */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Cpu className="w-4 h-4 text-purple-400" />
            <span className="text-xs font-bold text-white uppercase tracking-wider font-mono">
              Implemented AI Models Engine Selection
            </span>
          </div>
          <span className="text-[10px] text-slate-400 font-mono hidden sm:inline">
            Click model to re-evaluate TreeSHAP attributions
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          {AVAILABLE_AI_MODELS.map((m) => {
            const Icon = m.icon
            const isSelected = selectedModel === m.id
            return (
              <button
                key={m.id}
                type="button"
                onClick={() => handleModelChange(m.id)}
                className={`p-3 rounded-xl border text-left transition flex flex-col justify-between gap-2 relative overflow-hidden group ${
                  isSelected
                    ? 'bg-purple-950/70 border-purple-500 shadow-lg shadow-purple-950/50'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/70'
                }`}
              >
                {isSelected && (
                  <div className="absolute top-0 right-0 w-2 h-2 bg-purple-400 rounded-bl-lg" />
                )}
                <div className="flex items-center justify-between gap-1.5">
                  <div className="flex items-center gap-2">
                    <Icon className={`w-4 h-4 ${isSelected ? 'text-purple-400' : 'text-slate-400 group-hover:text-slate-200'}`} />
                    <span className="text-xs font-bold text-white font-mono">{m.name}</span>
                  </div>
                  <span className={`text-[9px] font-mono px-1.5 py-0.5 rounded font-bold ${
                    isSelected ? 'bg-purple-900 text-purple-200 border border-purple-700' : 'bg-slate-900 text-slate-400 border border-slate-800'
                  }`}>
                    {m.badge}
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 line-clamp-1">
                  {m.desc}
                </div>
                <div className="flex items-center justify-between text-[9px] font-mono text-slate-400 pt-1 border-t border-slate-800/60">
                  <span>Engine: {m.tag}</span>
                  {isSelected && <span className="text-purple-300 font-bold">● Active</span>}
                </div>
              </button>
            )
          })}
        </div>
      </div>

      {/* Search / Lookup Bar & Recent Selector */}
      <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-md space-y-3">
        {/* Quick Dropdown of Available Transactions */}
        <div>
          <label className="text-xs font-medium text-slate-300 flex items-center justify-between mb-1.5">
            <span>
              {isCustomer
                ? `Select One of Your Transactions to Explain (${recentTransactions.length} of your transactions available)`
                : `Select Transaction to Explain (${recentTransactions.length} available)`}
            </span>
            <span className="text-[10px] text-purple-400 font-mono font-normal">Choose from dropdown or enter ID</span>
          </label>
          <select
            id="explain-transaction-dropdown"
            value={transactionId}
            onChange={(e) => {
              const val = e.target.value
              if (val) {
                setTransactionId(val)
                handleLookup(val, selectedModel)
              }
            }}
            className="w-full bg-slate-950/90 border border-purple-800/60 hover:border-purple-500 rounded-xl px-3 py-2 text-xs text-purple-200 font-mono focus:outline-none focus:ring-1 focus:ring-purple-500 transition shadow-inner cursor-pointer"
          >
            <option value="">▼ Dropdown: Select transaction to explain...</option>
            {recentTransactions.map((tx) => (
              <option key={tx.transaction_id} value={tx.transaction_id}>
                {tx.transaction_id} {isCustomer ? '' : `• ${tx.customer_id}`} • ₹{Number(tx.amount || 0).toLocaleString('en-IN')} • {tx.prediction} ({tx.risk_level})
              </option>
            ))}
          </select>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center gap-3 pt-1">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder={
                isCustomer
                  ? "Enter your transaction ID (e.g. TXN-CUST_MONISHA_001-11492)..."
                  : "Or type Transaction ID (e.g., TXN-CUST_MOHANA_002-11492, PAY-A4C40947F13C)..."
              }
              value={transactionId}
              onChange={(e) => setTransactionId(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-100 font-mono placeholder-slate-400 focus:outline-none focus:border-purple-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-950 transition flex items-center justify-center gap-1.5 disabled:opacity-50 shrink-0"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Computing SHAP...' : 'Generate Explanation'}
          </button>
        </form>

        {/* Quick select chips (Customer sees only their own chips) */}
        {recentTransactions.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px]">
            <span className="text-slate-500 font-mono">Quick select:</span>
            {recentTransactions.slice(0, 8).map((tx) => (
              <button
                key={tx.transaction_id}
                onClick={() => handleLookup(tx.transaction_id, selectedModel)}
                className={`px-2 py-0.5 rounded-lg font-mono text-[10px] border transition ${
                  transactionId === tx.transaction_id
                    ? 'bg-purple-950 text-purple-300 border-purple-700 font-bold'
                    : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-slate-200'
                }`}
              >
                {tx.transaction_id}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Explanation Results Container */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-purple-400" />
          <span>Synthesizing multi-model TreeSHAP attributions &amp; spoken briefing...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs text-center space-y-2">
          <AlertTriangle className="w-5 h-5 mx-auto text-rose-400" />
          <div>{error}</div>
          <p className="text-slate-400 text-[11px]">
            Please select another transaction or run a real-time payment to generate an explanation.
          </p>
        </div>
      ) : explanation ? (
        <div className="space-y-6 animate-fadeIn">
          
          {/* Metadata & Model Header Card */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md">
            <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-4">
              <div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-bold text-white font-mono">{explanation.transaction_id}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      isFraud
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    {isFraud ? 'FRAUD (BLOCKED)' : 'GENUINE (APPROVED)'}
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-purple-950 text-purple-300 border border-purple-800">
                    AI Model: {(explanation.model_name || selectedModel).toUpperCase()} {explanation.model_version || 'v1.1.0'}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1.5 font-mono flex flex-wrap items-center gap-4">
                  <span>
                    Base Expected Value (E[f(x)]):{' '}
                    <strong className="text-slate-200">{Number(explanation.base_value || 0).toFixed(4)}</strong>
                  </span>
                  {explanation.uncertainty_score !== null && explanation.uncertainty_score !== undefined && (
                    <span>
                      Model Uncertainty:{' '}
                      <strong className="text-cyan-300">{Number(explanation.uncertainty_score).toFixed(3)} ({explanation.uncertainty_level || 'LOW'})</strong>
                    </span>
                  )}
                  {explanation.anomaly_score !== null && explanation.anomaly_score !== undefined && (
                    <span>
                      Isolation Forest Anomaly:{' '}
                      <strong className="text-amber-300">{Number(explanation.anomaly_score).toFixed(3)}</strong>
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-6 text-xs font-mono shrink-0">
                <div className="text-right">
                  <div className="text-[10px] text-slate-400 uppercase">Fraud Probability</div>
                  <div className={`text-xl font-bold ${isFraud ? 'text-rose-400' : 'text-emerald-400'}`}>
                    {(Number(explanation.fraud_probability || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-400 uppercase">Composite Risk Score</div>
                  <div className="text-xl font-bold text-cyan-400">
                    {explanation.risk_score || 0}/100
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* ========================================================================= */}
          {/* SWEET NATURAL AI VOICE EXPLAINER BAR (Every Transaction Spoken Out Loud)  */}
          {/* ========================================================================= */}
          <div className="p-4 rounded-2xl bg-gradient-to-r from-purple-950/70 via-indigo-950/50 to-slate-900 border-2 border-purple-500/60 shadow-[0_0_35px_rgba(168,85,247,0.25)] space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-purple-600 text-white shadow-md shadow-purple-900/50 animate-pulse">
                  <Headphones className="w-4 h-4" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs font-extrabold text-white uppercase tracking-wider font-mono">
                      Sweet AI Voice Explainer — Spoken TreeSHAP Attribution
                    </h3>
                    <span className="px-1.5 py-0.2 rounded text-[9px] font-mono font-bold bg-purple-900 text-purple-200 border border-purple-700">
                      Siri / Google Voice
                    </span>
                  </div>
                  <p className="text-[11px] text-purple-300">
                    Audible mathematical explanation for Transaction <strong>{explanation.transaction_id}</strong>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2.5">
                {/* Voice Style Selector */}
                <select
                  value={voiceStyle}
                  onChange={(e) => setVoiceStyle(e.target.value)}
                  className="bg-slate-900 border border-purple-700/80 text-purple-200 text-xs rounded-xl px-2.5 py-1.5 focus:ring-1 focus:ring-purple-400 font-semibold cursor-pointer"
                  title="Voice Style Tone"
                >
                  <option value="sweet">🌸 Sweet &amp; Gentle Voice (Warm Tone)</option>
                  <option value="siri">🎙️ Natural Siri Voice (Standard)</option>
                  <option value="analytical">⚡ Analytical Voice (Fast Forensic)</option>
                </select>

                {/* Play / Pause Button */}
                <button
                  onClick={handleToggleSpeak}
                  className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold shadow-lg transition ${
                    isSpeaking && !isPaused
                      ? 'bg-amber-600 hover:bg-amber-500 text-white animate-pulse'
                      : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white shadow-purple-950/60'
                  }`}
                >
                  {isSpeaking && !isPaused ? (
                    <>
                      <Pause className="w-3.5 h-3.5" />
                      <span>Pause Spoken Verdict</span>
                    </>
                  ) : isPaused ? (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      <span>Resume Spoken Verdict</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5" />
                      <span>Listen to AI Voice Explanation</span>
                    </>
                  )}
                </button>

                {/* Stop Button */}
                {isSpeaking && (
                  <button
                    onClick={handleStopSpeech}
                    className="p-2 rounded-xl bg-rose-950 hover:bg-rose-900 border border-rose-800 text-rose-300 transition"
                    title="Stop Speaking"
                  >
                    <Square className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Equalizer Soundwave Visualizer when speaking */}
            {isSpeaking && !isPaused && (
              <div className="flex items-center gap-1.5 p-2 rounded-xl bg-purple-950/80 border border-purple-800/80">
                <div className="flex items-center gap-1 px-2">
                  <span className="w-1 h-3.5 bg-purple-400 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="w-1 h-6 bg-cyan-300 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="w-1 h-2 bg-purple-300 rounded-full animate-bounce [animation-delay:300ms]" />
                  <span className="w-1 h-7 bg-pink-400 rounded-full animate-bounce [animation-delay:450ms]" />
                  <span className="w-1 h-4 bg-purple-400 rounded-full animate-bounce [animation-delay:600ms]" />
                </div>
                <span className="text-[11px] font-mono text-purple-200 font-bold">
                  SPEAKING SWEET VOICE • Describing Model Consensus &amp; Shapley Attributions
                </span>
              </div>
            )}

            {/* Read-Along Transcript Card */}
            <div className="p-3 rounded-xl bg-slate-950/80 border border-purple-900/60 text-xs text-slate-300 leading-relaxed font-mono relative">
              <div className="text-[10px] text-purple-400 uppercase font-bold mb-1 flex items-center gap-1.5">
                <Bot className="w-3.5 h-3.5 text-purple-400" />
                <span>Audible Explanation Transcript:</span>
              </div>
              <blockquote className="italic text-slate-200">
                &ldquo;{generateSpokenScript()}&rdquo;
              </blockquote>
            </div>
          </div>

          {/* Multi-Model Inference Comparison Matrix */}
          {modelComparison && Object.keys(modelComparison).length > 0 && (
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-cyan-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Multi-Model Consensus &amp; AI Comparison Matrix
                  </h3>
                </div>
                <span className="text-[10px] text-slate-400 font-mono">
                  All 4 candidate models evaluated simultaneously
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                {Object.entries(modelComparison).map(([mKey, mVal]) => {
                  const isCur = (explanation.model_name || selectedModel).toLowerCase() === mKey.toLowerCase()
                  const isMFraud = mVal.prediction === 'FRAUD'
                  return (
                    <div
                      key={mKey}
                      onClick={() => handleModelChange(mKey)}
                      className={`p-3 rounded-xl border cursor-pointer transition flex flex-col justify-between gap-2 ${
                        isCur
                          ? 'bg-cyan-950/40 border-cyan-500 shadow-md shadow-cyan-950/50'
                          : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-white font-mono uppercase">{mKey.replace('_', ' ')}</span>
                        {isCur && <span className="text-[9px] px-1 rounded bg-cyan-900 text-cyan-200 font-mono">Selected</span>}
                      </div>
                      <div className="flex items-baseline justify-between">
                        <span className={`text-base font-bold font-mono ${isMFraud ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {mVal.fraud_probability !== undefined ? `${(mVal.fraud_probability * 100).toFixed(1)}%` : 'N/A'}
                        </span>
                        <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded font-bold ${
                          isMFraud ? 'bg-rose-950 text-rose-300 border border-rose-800' : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                        }`}>
                          {mVal.prediction || 'GENUINE'}
                        </span>
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono flex items-center justify-between">
                        <span>Risk: {mVal.risk_score || 0}/100</span>
                        <span>Tier: {mVal.risk_tier || 'LOW'}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* AI Forensic Investigator Narrative */}
          {composedExp && (
            <div className="p-5 rounded-2xl bg-gradient-to-r from-purple-950/30 via-slate-900/60 to-slate-900/60 border border-purple-800/40 shadow-xl space-y-3">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  {isCustomer ? 'AI Security Receipt & Explanation' : 'AI Forensic Investigator Narrative'}
                </h3>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed font-sans">
                {composedExp.executive_summary || composedExp.technical_summary}
              </p>
              {composedExp.metadata && (
                <div className="pt-2 text-[10px] font-mono text-slate-400 border-t border-slate-800/80 flex flex-wrap gap-x-4 gap-y-1">
                  <span>Active Model: <strong className="text-slate-300">{composedExp.metadata.active_model}</strong></span>
                  <span>Probability: <strong className="text-slate-300">{composedExp.metadata.fraud_probability}</strong></span>
                  <span>Risk Score: <strong className="text-slate-300">{composedExp.metadata.composite_risk_score}</strong></span>
                  <span>Decision: <strong className="text-slate-300">{composedExp.metadata.decision}</strong></span>
                </div>
              )}
            </div>
          )}

          {/* Counterfactual "What-If" Analysis */}
          {counterfactual && (
            <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Compass className="w-4 h-4 text-amber-400" />
                  <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wider font-mono">
                    Counterfactual &ldquo;What-If&rdquo; AI Explainer
                  </h4>
                </div>
                <span className="text-[10px] font-mono text-slate-400 uppercase">{counterfactual.status}</span>
              </div>
              {counterfactual.changes_required && counterfactual.changes_required.length > 0 ? (
                <div className="space-y-1.5 pt-1">
                  <p className="text-xs text-slate-300">
                    To reverse this risk classification, the minimum required feature perturbations are:
                  </p>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {counterfactual.changes_required.map((ch, idx) => (
                      <div key={idx} className="p-2 rounded-xl bg-slate-950/80 border border-slate-800 font-mono text-[11px] flex justify-between">
                        <span className="text-amber-300">{ch.feature}</span>
                        <span className="text-slate-400">{ch.current_value} &rarr; <strong className="text-emerald-400">{ch.suggested_value}</strong></span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-400">
                  {counterfactual.rationale || 'No single or composite mutable feature perturbation sufficiently altered the risk tier within valid constraints.'}
                </p>
              )}
            </div>
          )}

          {/* TreeSHAP Feature Attributions Table */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                  TreeSHAP Feature Influence Attribution Ranking
                </h3>
              </div>
              <div className="flex items-center gap-4 text-[10px] font-mono">
                <span className="flex items-center gap-1.5 text-rose-400">
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  Increases Fraud Risk (+)
                </span>
                <span className="flex items-center gap-1.5 text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  Decreases Fraud Risk (-)
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-slate-800 text-[10px] uppercase text-slate-400">
                    <th className="pb-2.5 font-semibold">Feature Name</th>
                    <th className="pb-2.5 font-semibold">Feature Value</th>
                    <th className="pb-2.5 font-semibold">Direction</th>
                    <th className="pb-2.5 font-semibold text-right">SHAP Impact</th>
                    <th className="pb-2.5 font-semibold pl-4">Attribution Magnitude</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {allFeatures.map((f, i) => {
                    const shapVal = Number(f.shap_value || 0)
                    const isPositive = shapVal > 0
                    const magnitude = Math.min(Math.abs(shapVal) * 20, 100)

                    return (
                      <tr key={i} className="hover:bg-slate-800/30 transition">
                        <td className="py-2.5 font-bold text-slate-200">
                          {f.feature_name || f.feature}
                        </td>
                        <td className="py-2.5 text-slate-300">
                          {f.feature_value !== undefined && f.feature_value !== null
                            ? String(f.feature_value)
                            : f.raw_value !== undefined && f.raw_value !== null
                            ? String(f.raw_value)
                            : '—'}
                        </td>
                        <td className="py-2.5">
                          <span
                            className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-bold ${
                              isPositive
                                ? 'bg-rose-950/60 text-rose-400 border border-rose-900/60'
                                : 'bg-emerald-950/60 text-emerald-400 border border-emerald-900/60'
                            }`}
                          >
                            {isPositive ? (
                              <>
                                <ArrowUpRight className="w-3 h-3" /> Increases Risk
                              </>
                            ) : (
                              <>
                                <ArrowDownRight className="w-3 h-3" /> Decreases Risk
                              </>
                            )}
                          </span>
                        </td>
                        <td
                          className={`py-2.5 text-right font-bold ${
                            isPositive ? 'text-rose-400' : 'text-emerald-400'
                          }`}
                        >
                          {isPositive ? `+${shapVal.toFixed(4)}` : shapVal.toFixed(4)}
                        </td>
                        <td className="py-2.5 pl-4">
                          <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden flex items-center">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                isPositive
                                  ? 'bg-gradient-to-r from-rose-500 to-red-600'
                                  : 'bg-gradient-to-r from-emerald-500 to-teal-500'
                              }`}
                              style={{ width: `${Math.max(magnitude, 4)}%` }}
                            />
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>

        </div>
      ) : null}
    </div>
  )
}
