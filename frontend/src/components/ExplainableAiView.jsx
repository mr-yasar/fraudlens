import React, { useState, useEffect } from 'react'
import {
  Sparkles,
  Search,
  ArrowUpRight,
  ArrowDownRight,
  RefreshCw,
  AlertTriangle,
} from 'lucide-react'
import { transactionsApi } from '../services/api'


export default function ExplainableAiView({ initialTransactionId }) {
  const [transactionId, setTransactionId] = useState(initialTransactionId || '')
  const [explanation, setExplanation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [recentTransactions, setRecentTransactions] = useState([])

  const fetchRecent = async () => {
    try {
      const data = await transactionsApi.list({ page: 1, limit: 6 })
      setRecentTransactions(data.items || [])
      if (!transactionId && data.items && data.items.length > 0) {
        handleLookup(data.items[0].transaction_id)
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
      handleLookup(initialTransactionId)
    }
  }, [initialTransactionId])

  const handleLookup = async (idToLook) => {
    const target = idToLook || transactionId
    if (!target) return

    setLoading(true)
    setError(null)
    try {
      const res = await transactionsApi.getExplanation(target)
      setExplanation(res)
      setTransactionId(target)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'No SHAP explanation found for this transaction.')
      setExplanation(null)
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleLookup()
  }

  // BUG 3 FIX: Backend returns top_risk_increasing_factors / top_risk_decreasing_factors
  // (not top_positive_features / top_negative_features)
  const topPos = explanation?.top_risk_increasing_factors ||
                 explanation?.top_positive_features || []
  const topNeg = explanation?.top_risk_decreasing_factors ||
                 explanation?.top_negative_features || []
  // Fall back to all_attributions if both are empty
  const allAttributions = explanation?.all_attributions || []
  const allFeatures = (topPos.length === 0 && topNeg.length === 0 && allAttributions.length > 0)
    ? allAttributions.sort((a, b) => Math.abs(b.shap_value || 0) - Math.abs(a.shap_value || 0))
    : [...topPos, ...topNeg].sort((a, b) => Math.abs(b.shap_value || 0) - Math.abs(a.shap_value || 0))

  // Determine prediction label — backend returns string 'FRAUD'/'GENUINE' or integer 1/0
  const isFraud = explanation?.prediction === 'FRAUD' || explanation?.prediction === 1

  const handleClear = () => {
    setExplanation(null)
    setError(null)
    setTransactionId('')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-400" />
            Explainable AI (XAI) &amp; Local SHAP Attributions
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Mathematical transparency explaining individual model inferences using TreeSHAP game-theoretic Shapley values.
          </p>
        </div>

        {/* Clear result / back to search */}
        {explanation && (
          <button
            onClick={handleClear}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition shrink-0"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
            New Search
          </button>
        )}
      </div>

      {/* Conceptual Clarity Banner */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] uppercase font-mono text-cyan-400 font-bold mb-1">1. AI Prediction</div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Raw ML classifier output (0 to 1 fraud probability) optimized against cost-sensitive thresholds.
          </p>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-purple-800/50">
          <div className="text-[10px] uppercase font-mono text-purple-400 font-bold mb-1">2. SHAP Explanation</div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Game-theoretic feature attributions quantifying how each signal drove probability up or down from base value.
          </p>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800">
          <div className="text-[10px] uppercase font-mono text-emerald-400 font-bold mb-1">3. Risk Score (0-100)</div>
          <p className="text-slate-300 text-[11px] leading-relaxed">
            Business composite risk combining behavioral velocity, chargebacks, geography, and ML probability.
          </p>
        </div>
      </div>

      {/* Search / Lookup Bar & Recent Selector */}
      <div className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-md space-y-3">
        <form onSubmit={handleSubmit} className="flex flex-col sm:flex-row items-center gap-3">
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Enter Transaction ID (e.g., TX-INV-001)..."
              value={transactionId}
              onChange={(e) => setTransactionId(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-100 font-mono placeholder-slate-400 focus:outline-none focus:border-purple-500"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full sm:w-auto px-4 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold shadow-md shadow-purple-950 transition flex items-center justify-center gap-1.5 disabled:opacity-50"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            {loading ? 'Computing SHAP...' : 'Generate Explanation'}
          </button>
        </form>

        {/* Quick select chips */}
        {recentTransactions.length > 0 && (
          <div className="flex flex-wrap items-center gap-2 pt-1 text-[11px]">
            <span className="text-slate-500 font-mono">Quick select:</span>
            {recentTransactions.map((tx) => (
              <button
                key={tx.transaction_id}
                onClick={() => handleLookup(tx.transaction_id)}
                className={`px-2 py-0.5 rounded-lg font-mono border transition ${
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
          <span>Synthesizing SHAP waterfall attributions...</span>
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
          {/* Metadata Card */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-white font-mono">{explanation.transaction_id}</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      isFraud
                        ? 'bg-rose-950 text-rose-300 border border-rose-800'
                        : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                    }`}
                  >
                    {isFraud ? 'FRAUD' : 'GENUINE'}
                  </span>
                </div>
                <div className="text-xs text-slate-400 mt-1 font-mono">
                  Base Expected Value (E[f(x)]):{' '}
                  <strong className="text-slate-200">{Number(explanation.base_value || 0).toFixed(4)}</strong>
                </div>
              </div>

              <div className="flex items-center gap-4 text-xs font-mono">
                <div className="text-right">
                  <div className="text-[10px] text-slate-400 uppercase">Fraud Probability</div>
                  <div className="text-lg font-bold text-white">
                    {(Number(explanation.fraud_probability || 0) * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-[10px] text-slate-400 uppercase">Risk Level</div>
                  <div className="text-lg font-bold text-cyan-400">
                    {explanation.risk_level || 'LOW'} ({explanation.risk_score || 0})
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Feature Attributions Waterfall / Bar Table */}
          <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Feature Influence Attribution Ranking
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
                    const barPct = Math.min(absVal * 200, 100) // normalized visual bar

                    return (
                      <tr key={idx} className="hover:bg-slate-800/40 transition">
                        <td className="py-2.5 px-3 font-semibold text-slate-200">
                          {item.feature_name}
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
          Enter a transaction ID or select from recent activity to compute SHAP attributions.
        </div>
      )}
    </div>
  )
}
