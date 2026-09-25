import React, { useState, useEffect } from 'react'
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
} from 'lucide-react'
import { transactionsApi } from '../services/api'

const AVAILABLE_AI_MODELS = [
  { id: 'xgboost', name: 'XGBoost Classifier', badge: 'Active Champion', tag: 'TreeSHAP', icon: Cpu, desc: 'Gradient Boosted Decision Trees (99.1% ROC-AUC)' },
  { id: 'random_forest', name: 'Random Forest', badge: 'Ensemble Bagging', tag: 'TreeSHAP', icon: Layers, desc: '100-Tree Forest with Out-of-Bag voting' },
  { id: 'logistic_regression', name: 'Logistic Regression', badge: 'Calibrated Linear', tag: 'LinearSHAP', icon: Binary, desc: 'Cost-sensitive L2 regularized odds classifier' },
  { id: 'ensemble_stacking', name: 'Ensemble Stacking', badge: 'Meta-Learner', tag: 'EnsembleSHAP', icon: Compass, desc: 'Fused Meta-Classifier stacking XGBoost, RF & LR' },
]

export default function ExplainableAiView({ initialTransactionId }) {
  const [transactionId, setTransactionId] = useState(initialTransactionId || '')
  const [selectedModel, setSelectedModel] = useState('xgboost')
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recentTransactions, setRecentTransactions] = useState([])

  const fetchRecent = async () => {
    try {
      const data = await transactionsApi.list({ page: 1, limit: 30 })
      const items = data.items || []
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
  }, [])

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
    setExplanation(null)
    setError(null)
    setTransactionId('')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            Explainable AI (XAI) &amp; Local SHAP Attributions
          </h2>
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
            <span>Select Transaction to Explain</span>
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
            <option value="">▼ Dropdown: Select from recent transactions ({recentTransactions.length} available)...</option>
            {recentTransactions.map((tx) => (
              <option key={tx.transaction_id} value={tx.transaction_id}>
                {tx.transaction_id} • {tx.customer_id} • ₹{Number(tx.amount || 0).toLocaleString('en-IN')} • {tx.prediction} ({tx.risk_level})
              </option>
            ))}
          </select>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center gap-3 pt-1">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Or type Transaction ID (e.g., TXN-CUST_MOHANA_002-11492, PAY-A6BC4E67BA45)..."
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

        {/* Quick select chips */}
        {recentTransactions.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5 pt-1 text-[11px]">
            <span className="text-slate-500 font-mono">Quick select:</span>
            {recentTransactions.slice(0, 10).map((tx) => (
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
          <span>Synthesizing multi-model TreeSHAP attributions...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs text-center space-y-2">
          <AlertTriangle className="w-5 h-5 mx-auto text-rose-400" />
          <div>{error}</div>
          <p className="text-slate-400 text-[11px]">
            Please select another transaction or run a real-time evaluation to generate an explanation.
          </p>
        </div>
      ) : explanation ? (
        <div className="space-y-6">
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
                        <span>Tier: {mVal.risk_level || 'LOW'}</span>
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          {/* AI Forensic Investigator Narrative */}
          {composedExp && (
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-purple-800/40 shadow-xl backdrop-blur-md">
              <div className="flex items-center gap-2 mb-2">
                <Sparkles className="w-4 h-4 text-purple-400" />
                <h3 className="text-xs font-bold text-purple-300 uppercase tracking-wider font-mono">
                  AI Forensic Investigator Narrative
                </h3>
              </div>
              <p className="text-xs text-slate-200 leading-relaxed font-sans">
                {composedExp.investigator_summary || 'Pre-authorization analysis concluded for this transaction.'}
              </p>
              {composedExp.technical_summary && (
                <div className="mt-2.5 p-2.5 rounded-xl bg-slate-950/70 border border-slate-800 text-[11px] text-slate-400 font-mono">
                  {composedExp.technical_summary}
                </div>
              )}
            </div>
          )}

          {/* Counterfactual What-If AI Explainer */}
          {counterfactual && (
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Compass className="w-4 h-4 text-amber-400" />
                  <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                    Counterfactual "What-If" AI Explainer
                  </h3>
                </div>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  counterfactual.status === 'SUCCESS' ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-slate-950 text-slate-400 border border-slate-800'
                }`}>
                  {counterfactual.status}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                {counterfactual.actionable_summary || 'Evaluated feature perturbations to identify counterfactual reversal conditions.'}
              </p>
              {counterfactual.modified_features && counterfactual.modified_features.length > 0 && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 mt-3 pt-3 border-t border-slate-800 font-mono text-xs">
                  {counterfactual.modified_features.map((mf, i) => (
                    <div key={i} className="p-2 rounded-lg bg-slate-950/80 border border-slate-800 flex items-center justify-between">
                      <span className="text-slate-400">{mf.feature_name}:</span>
                      <span className="text-slate-300 line-through mr-2">{String(mf.original_value)}</span>
                      <span className="text-emerald-400 font-bold">→ {String(mf.counterfactual_value)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Feature Attributions Waterfall / Bar Table */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider font-mono">
                TreeSHAP Feature Influence Attribution Ranking
              </h3>
              <div className="flex items-center gap-4 text-[10px] font-mono">
                <span className="flex items-center gap-1 text-rose-400">
                  <span className="w-2 h-2 rounded-full bg-rose-500" /> Increases Fraud Risk (+)
                </span>
                <span className="flex items-center gap-1 text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" /> Decreases Fraud Risk (-)
                </span>
              </div>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-950/60 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Feature Name</th>
                    <th className="py-2.5 px-3">Feature Value</th>
                    <th className="py-2.5 px-3">Direction</th>
                    <th className="py-2.5 px-3">SHAP Impact</th>
                    <th className="py-2.5 px-3 w-48">Attribution Magnitude</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 font-mono">
                  {allFeatures.map((item, idx) => {
                    const isPositive = (item.shap_value || 0) > 0
                    const absVal = Math.abs(item.shap_value || 0)
                    const barPct = Math.min(absVal * 200, 100)

                    return (
                      <tr key={idx} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-semibold text-slate-200">
                          {item.display_name || item.feature_name}
                        </td>
                        <td className="py-2.5 px-3 text-cyan-300">
                          {item.feature_value !== undefined ? String(item.feature_value) : 'N/A'}
                        </td>
                        <td className="py-2.5 px-3">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold inline-flex items-center gap-1 ${
                              isPositive
                                ? 'bg-rose-950/80 text-rose-400 border border-rose-800/80'
                                : 'bg-emerald-950/80 text-emerald-400 border border-emerald-800/80'
                            }`}
                          >
                            {isPositive ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                            {isPositive ? 'Increases Risk' : 'Decreases Risk'}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 font-bold">
                          <span className={isPositive ? 'text-rose-400' : 'text-emerald-400'}>
                            {isPositive ? '+' : ''}
                            {Number(item.shap_value || 0).toFixed(4)}
                          </span>
                        </td>
                        <td className="py-2.5 px-3">
                          <div className="w-full h-2 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${isPositive ? 'bg-rose-500' : 'bg-emerald-500'}`}
                              style={{ width: `${Math.max(barPct, 4)}%` }}
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
      ) : (
        <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/40 rounded-2xl border border-slate-800">
          Select a transaction from the dropdown or type an ID to generate TreeSHAP explainability across all 4 AI models.
        </div>
      )}
    </div>
  )
}
