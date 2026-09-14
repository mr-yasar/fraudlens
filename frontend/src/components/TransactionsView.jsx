import React, { useState, useEffect } from 'react'
import {
  Search,
  CreditCard,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Plus,
  RefreshCw,
  Eye,
  ShieldAlert,
  Sparkles,
  X,
} from 'lucide-react'
import { transactionsApi, investigationsApi } from '../services/api'

export default function TransactionsView({ onViewExplanation }) {
  const [transactions, setTransactions] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(15)
  const [riskFilter, setRiskFilter] = useState('')
  const [predictionFilter, setPredictionFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Details Modal state
  const [selectedTx, setSelectedTx] = useState(null)

  // Live Evaluation Form modal state
  const [showEvaluateModal, setShowEvaluateModal] = useState(false)
  const [evalLoading, setEvalLoading] = useState(false)
  const [evalError, setEvalError] = useState(null)
  const [evalResult, setEvalResult] = useState(null)

  // Case creation notification
  const [caseMsg, setCaseMsg] = useState(null)

  // Evaluation Form inputs
  const [evalForm, setEvalForm] = useState({
    transaction_id: 'TX-LIVE-001',
    customer_id: 'CUST-1001',

    amount: 1250.0,
    transaction_hour: 14,
    merchant_category: 'electronics',
    transaction_country: 'US',
    device_type: 'mobile_ios',
    transaction_type: 'ONLINE',
  })

  const fetchTransactions = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await transactionsApi.list({
        page,
        limit,
        risk_level: riskFilter,
        prediction: predictionFilter,
        search: searchQuery,
      })
      setTransactions(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load transactions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTransactions()
  }, [page, riskFilter, predictionFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    setPage(1)
    fetchTransactions()
  }

  const handleOpenDetail = async (txId) => {
    try {
      const data = await transactionsApi.get(txId)
      setSelectedTx(data)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Error fetching transaction details')
    }
  }


  const handleCreateCase = async (txId) => {
    try {
      const res = await investigationsApi.create({
        transaction_id: txId,
        notes: 'Case initiated from Transactions Command Panel',
      })
      setCaseMsg(`Case opened successfully: ${res.case_id}`)
      setTimeout(() => setCaseMsg(null), 4000)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to open case')
    }
  }

  const handleEvaluateSubmit = async (e) => {
    e.preventDefault()
    setEvalLoading(true)
    setEvalError(null)
    try {
      const payload = {
        transaction_id: evalForm.transaction_id,
        customer_id: evalForm.customer_id,
        amount: parseFloat(evalForm.amount),
        transaction_hour: parseInt(evalForm.transaction_hour, 10),
        merchant_category: evalForm.merchant_category,
        transaction_country: evalForm.transaction_country,
        device_type: evalForm.device_type,
        transaction_type: evalForm.transaction_type,
      }
      const res = await transactionsApi.evaluate(payload)
      setEvalResult(res)
      fetchTransactions()
    } catch (err) {
      setEvalError(err instanceof Error ? err.message : 'Evaluation failed')
    } finally {
      setEvalLoading(false)
    }
  }

  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className="space-y-6">
      {/* Top Header & Simulation Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-cyan-400" />
            Transaction Management &amp; Real-Time Evaluation
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Query real PostgreSQL financial transactions, inspect multi-factor risk scores, and evaluate live requests.
          </p>
        </div>

        <button
          onClick={() => {
            setEvalResult(null)
            setEvalError(null)
            setEvalForm({
              ...evalForm,
              transaction_id: `TX-LIVE-${Date.now().toString().slice(-6)}`,
            })
            setShowEvaluateModal(true)
          }}
          className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-cyan-950 transition flex items-center gap-2"
        >
          <Plus className="w-4 h-4" />
          Evaluate New Transaction
        </button>
      </div>

      {caseMsg && (
        <div className="p-3 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{caseMsg}</span>
        </div>
      )}

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex flex-wrap items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 min-w-[240px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Transaction ID or Customer ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-medium text-slate-200 border border-slate-700 transition"
          >
            Search
          </button>
        </form>

        <div className="flex items-center gap-2">
          {/* Risk Level Filter */}
          <select
            value={riskFilter}
            onChange={(e) => {
              setRiskFilter(e.target.value)
              setPage(1)
            }}
            className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Risk Levels</option>
            <option value="LOW">LOW</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="HIGH">HIGH</option>
          </select>

          {/* Prediction Filter */}
          <select
            value={predictionFilter}
            onChange={(e) => {
              setPredictionFilter(e.target.value)
              setPage(1)
            }}
            className="bg-slate-950/80 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            <option value="">All Predictions</option>
            <option value="0">Genuine (0)</option>
            <option value="1">Fraud (1)</option>
          </select>

          <button
            onClick={fetchTransactions}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
            title="Refresh"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Transaction Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
            <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
            <span>Retrieving transaction stream from database...</span>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-xs text-rose-400">{error}</div>
        ) : transactions.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 space-y-2">
            <CreditCard className="w-8 h-8 mx-auto text-slate-600" />
            <div className="font-semibold text-slate-300">No transactions found</div>
            <p>Try adjusting your search criteria or risk filter.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Transaction ID</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Category</th>
                  <th className="py-3 px-4">Country</th>
                  <th className="py-3 px-4">Probability</th>
                  <th className="py-3 px-4">Prediction</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {transactions.map((t) => {
                  const isHigh = t.risk_level === 'HIGH'
                  const isMed = t.risk_level === 'MEDIUM'
                  const isFraud = t.prediction === 1

                  return (
                    <tr key={t.id || t.transaction_id} className="hover:bg-slate-800/40 transition">
                      <td className="py-3 px-4 font-mono font-bold text-cyan-400">
                        {t.transaction_id}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">{t.customer_id}</td>
                      <td className="py-3 px-4 font-mono font-bold text-white">
                        ${Number(t.amount).toFixed(2)}
                      </td>
                      <td className="py-3 px-4 capitalize text-slate-300">{t.merchant_category || 'N/A'}</td>
                      <td className="py-3 px-4 font-mono text-slate-400">{t.transaction_country || 'US'}</td>
                      <td className="py-3 px-4 font-mono">
                        {t.fraud_probability !== null ? `${(t.fraud_probability * 100).toFixed(1)}%` : 'N/A'}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            isFraud
                              ? 'bg-rose-950/80 text-rose-300 border border-rose-800/60'
                              : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800/60'
                          }`}
                        >
                          {isFraud ? 'FRAUD' : 'GENUINE'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase flex items-center gap-1 w-fit ${
                            isHigh
                              ? 'bg-rose-950 text-rose-400 border border-rose-800'
                              : isMed
                              ? 'bg-amber-950 text-amber-400 border border-amber-800'
                              : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full ${
                              isHigh ? 'bg-rose-400' : isMed ? 'bg-amber-400' : 'bg-emerald-400'
                            }`}
                          />
                          {t.risk_level || 'LOW'} ({t.risk_score || 0})
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right space-x-1">
                        <button
                          onClick={() => handleOpenDetail(t.transaction_id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-cyan-300 hover:bg-slate-800 transition"
                          title="Inspect Attributes"
                        >
                          <Eye className="w-4 h-4" />
                        </button>
                        {onViewExplanation && (
                          <button
                            onClick={() => onViewExplanation(t.transaction_id)}
                            className="p-1.5 rounded-lg text-slate-400 hover:text-purple-300 hover:bg-slate-800 transition"
                            title="SHAP Explainability"
                          >
                            <Sparkles className="w-4 h-4" />
                          </button>
                        )}
                        <button
                          onClick={() => handleCreateCase(t.transaction_id)}
                          className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition"
                          title="Open Investigation Case"
                        >
                          <ShieldAlert className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-3 bg-slate-950/40 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <span className="text-white font-mono">{page}</span> of{' '}
            <span className="text-white font-mono">{totalPages}</span> ({total} total transactions)
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* Transaction Details Slide-over / Modal */}
      {selectedTx && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="max-w-xl w-full rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <CreditCard className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white">Transaction Profile</h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedTx(null)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                  Back to List
                </button>
                <button
                  onClick={() => setSelectedTx(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Transaction ID</span>
                <span className="font-mono font-bold text-cyan-400">{selectedTx.transaction_id}</span>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Customer Profile</span>
                <span className="font-mono font-bold text-slate-200">{selectedTx.customer_id}</span>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Amount</span>
                <span className="font-mono font-bold text-white text-sm">${Number(selectedTx.amount).toFixed(2)}</span>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Merchant Category</span>
                <span className="capitalize text-slate-200">{selectedTx.merchant_category || 'N/A'}</span>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Country &amp; Device</span>
                <span className="text-slate-200">{selectedTx.transaction_country || 'US'} • {selectedTx.device_type || 'Unknown'}</span>
              </div>
              <div className="p-3 bg-slate-950/70 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">ML Probability</span>
                <span className="font-mono text-purple-300 font-bold">
                  {(Number(selectedTx.fraud_probability || 0) * 100).toFixed(1)}%
                </span>
              </div>
            </div>

            {/* Risk Assessment Block */}
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-slate-300">Composite Risk Evaluation</span>
                <span className="text-xs font-mono font-bold text-cyan-400">{selectedTx.risk_score} / 100</span>
              </div>
              <div className="text-[11px] text-slate-400">
                Evaluation Category: <strong className="text-white">{selectedTx.risk_level}</strong>
              </div>
            </div>

            <div className="flex justify-end gap-2 pt-2">
              {onViewExplanation && (
                <button
                  onClick={() => {
                    const txId = selectedTx.transaction_id
                    setSelectedTx(null)
                    onViewExplanation(txId)
                  }}
                  className="px-3 py-1.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-1.5"
                >
                  <Sparkles className="w-3.5 h-3.5" /> View SHAP Breakdown
                </button>
              )}
              <button
                onClick={() => setSelectedTx(null)}
                className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Real-time Evaluation Modal */}
      {showEvaluateModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
          <div className="max-w-xl w-full rounded-2xl bg-slate-900 border border-cyan-800/60 shadow-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="text-base font-bold text-white flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-cyan-400" />
                  Real-Time Transaction Evaluation
                </h3>
                <p className="text-xs text-slate-400">
                  Runs full ML inference, multi-factor risk scoring, and commits transaction to database.
                </p>
              </div>
              <button
                onClick={() => setShowEvaluateModal(false)}
                className="p-1 text-slate-400 hover:text-white rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {evalError && (
              <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs">
                {evalError}
              </div>
            )}

            <form onSubmit={handleEvaluateSubmit} className="space-y-3 text-xs">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Transaction ID</label>
                  <input
                    type="text"
                    required
                    value={evalForm.transaction_id}
                    onChange={(e) => setEvalForm({ ...evalForm, transaction_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Customer ID</label>
                  <input
                    type="text"
                    required
                    value={evalForm.customer_id}
                    onChange={(e) => setEvalForm({ ...evalForm, customer_id: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Amount ($)</label>
                  <input
                    type="number"
                    step="0.01"
                    min="0.01"
                    required
                    value={evalForm.amount}
                    onChange={(e) => setEvalForm({ ...evalForm, amount: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Merchant Category</label>
                  <select
                    value={evalForm.merchant_category}
                    onChange={(e) => setEvalForm({ ...evalForm, merchant_category: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="electronics">Electronics</option>
                    <option value="luxury_goods">Luxury Goods</option>
                    <option value="grocery">Grocery</option>
                    <option value="clothing">Clothing</option>
                    <option value="travel">Travel</option>
                  </select>
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Country</label>
                  <input
                    type="text"
                    required
                    value={evalForm.transaction_country}
                    onChange={(e) => setEvalForm({ ...evalForm, transaction_country: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="block text-[11px] font-medium text-slate-400 mb-1">Device Type</label>
                  <select
                    value={evalForm.device_type}
                    onChange={(e) => setEvalForm({ ...evalForm, device_type: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
                  >
                    <option value="mobile_ios">Mobile iOS</option>
                    <option value="desktop_windows">Desktop Windows</option>
                    <option value="mobile_android">Mobile Android</option>
                    <option value="unknown">Unknown</option>
                  </select>
                </div>
              </div>

              <div className="flex justify-end gap-2 pt-3">
                <button
                  type="button"
                  onClick={() => setShowEvaluateModal(false)}
                  className="px-3 py-1.5 rounded-xl bg-slate-800 text-slate-300 text-xs hover:bg-slate-700"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={evalLoading}
                  className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-1.5"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${evalLoading ? 'animate-spin' : ''}`} />
                  {evalLoading ? 'Evaluating...' : 'Run Pipeline Inference'}
                </button>
              </div>
            </form>

            {/* Evaluation Result Display */}
            {evalResult && (
              <div className="p-4 rounded-xl bg-slate-950 border border-cyan-800/80 space-y-3 mt-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold text-white">Inference Engine Result</span>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                      evalResult.prediction === 1
                        ? 'bg-rose-950 text-rose-400 border border-rose-800'
                        : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                    }`}
                  >
                    {evalResult.prediction === 1 ? 'FRAUD (1)' : 'GENUINE (0)'}
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                  <div className="p-2 bg-slate-900 rounded-lg">
                    <span className="text-slate-400 block text-[10px]">Probability</span>
                    <span className="text-cyan-300 font-bold">
                      {(Number(evalResult.fraud_probability || 0) * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="p-2 bg-slate-900 rounded-lg">
                    <span className="text-slate-400 block text-[10px]">Risk Score</span>
                    <span className="text-white font-bold">{evalResult.risk_score} ({evalResult.risk_level})</span>
                  </div>
                </div>

                {evalResult.risk_factors && (
                  <div className="text-[11px] text-slate-300">
                    <span className="text-[10px] font-mono uppercase text-slate-400 block mb-1">Key Factors</span>
                    <ul className="list-disc pl-4 space-y-0.5 text-slate-400">
                      {evalResult.risk_factors.map((f, i) => (
                        <li key={i}>{typeof f === 'string' ? f : JSON.stringify(f)}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
