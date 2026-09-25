import React, { useState, useEffect } from 'react'
import {
  BrainCircuit,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  RefreshCw,
  TrendingUp,
  ShieldAlert,
  ArrowRight,
} from 'lucide-react'
import { transactionsApi, dashboardApi } from '../services/api'
import { formatINR } from '../utils/formatters'

export default function PredictionsView({ onOpenExplanation }) {
  const [predictions, setPredictions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modelInfo, setModelInfo] = useState(null)

  // Interactive Live Tester state using actual dataset fields
  const [form, setForm] = useState({
    transaction_id: `TXN${Math.floor(100000 + Math.random() * 900000)}`,
    customer_id: 'CUST001',
    Amount: 7663.76,
    Transaction_Type: 'Purchase',
    Transaction_Hour: 16,
    Location: 'Pune',
    Usual_Location: 'Pune',
    Device_Type: 'Mac',
    New_Device: 0,
    Failed_Attempts: 0,
    International_Transaction: 0,
    Unusual_Location: 0,
  })
  const [predictLoading, setPredictLoading] = useState(false)
  const [activeResult, setActiveResult] = useState(null)

  const fetchData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [txRes, statsRes] = await Promise.all([
        transactionsApi.list({ page: 1, limit: 12 }),
        dashboardApi.getStats(),
      ])
      setPredictions(txRes.items || [])
      setModelInfo(statsRes.active_model_info || {})
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch predictions')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  const handlePredict = async (e) => {
    e.preventDefault()
    setPredictLoading(true)
    try {
      const res = await transactionsApi.evaluate({
        ...form,
        Amount: parseFloat(form.Amount),
        transaction_amount: parseFloat(form.Amount),
        Transaction_Hour: parseInt(form.Transaction_Hour, 10),
        transaction_hour: parseInt(form.Transaction_Hour, 10),
        Failed_Attempts: parseInt(form.Failed_Attempts, 10),
        New_Device: parseInt(form.New_Device, 10),
        International_Transaction: parseInt(form.International_Transaction, 10),
        Unusual_Location: form.Location !== form.Usual_Location ? 1 : parseInt(form.Unusual_Location, 10),
      })
      setActiveResult(res)
      fetchData()
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Prediction inference failed')
    } finally {
      setPredictLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <BrainCircuit className="w-5 h-5 text-cyan-400" />
            AI Fraud Predictions Engine
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Production ML inference with calibrated thresholds, multi-factor risk scoring, and real-time classification.
          </p>
        </div>

        {/* Model Spec Badge */}
        <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 px-3 py-1.5 rounded-xl text-xs font-mono">
          <Cpu className="w-4 h-4 text-purple-400" />
          <span className="text-slate-300">Active Model:</span>
          <span className="text-white font-bold">{modelInfo?.name || 'XGBoost_Champion'}</span>
          <span className="text-cyan-400">({modelInfo?.version || 'v1.0'})</span>
        </div>
      </div>

      {/* Interactive Inference Simulator */}
      <div className="p-5 rounded-2xl bg-gradient-to-br from-slate-900/90 to-slate-950 border border-cyan-800/50 shadow-xl backdrop-blur-md">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-white uppercase tracking-wider">
              Interactive Model Inference Testing
            </h3>
          </div>
          <span className="text-[10px] font-mono text-cyan-400">Live Scoring Pipeline</span>
        </div>

        <form onSubmit={handlePredict} className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Customer ID</label>
            <input
              type="text"
              required
              value={form.customer_id}
              onChange={(e) => setForm({ ...form, customer_id: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Amount (₹ INR)</label>
            <input
              type="number"
              step="0.01"
              required
              value={form.Amount}
              onChange={(e) => setForm({ ...form, Amount: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Transaction Type</label>
            <select
              value={form.Transaction_Type}
              onChange={(e) => setForm({ ...form, Transaction_Type: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="Transfer">Transfer</option>
              <option value="Purchase">Purchase</option>
              <option value="ATM Withdrawal">ATM Withdrawal</option>
              <option value="Online Payment">Online Payment</option>
              <option value="Bill Payment">Bill Payment</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Hour (0–23)</label>
            <input
              type="number"
              min="0"
              max="23"
              required
              value={form.Transaction_Hour}
              onChange={(e) => setForm({ ...form, Transaction_Hour: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Location</label>
            <select
              value={form.Location}
              onChange={(e) => setForm({ ...form, Location: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              {['Pune', 'Hassan', 'Chennai', 'Mangalore', 'Bangalore', 'Hyderabad', 'Mumbai', 'Mysore', 'Delhi'].map((loc) => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Usual Location</label>
            <select
              value={form.Usual_Location}
              onChange={(e) => setForm({ ...form, Usual_Location: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              {['Pune', 'Mangalore', 'Delhi', 'Hassan', 'Hyderabad', 'Mumbai', 'Bangalore', 'Chennai', 'Mysore'].map((loc) => (
                <option key={loc} value={loc}>{loc}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Device Type</label>
            <select
              value={form.Device_Type}
              onChange={(e) => setForm({ ...form, Device_Type: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-cyan-500"
            >
              <option value="Mac">Mac</option>
              <option value="iPhone">iPhone</option>
              <option value="Android">Android</option>
              <option value="Windows">Windows</option>
            </select>
          </div>

          <div>
            <label className="block text-[10px] font-mono uppercase text-slate-400 mb-1">Failed Attempts</label>
            <input
              type="number"
              min="0"
              max="10"
              value={form.Failed_Attempts}
              onChange={(e) => setForm({ ...form, Failed_Attempts: e.target.value })}
              className="w-full bg-slate-950 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-cyan-500"
            />
          </div>

          <div className="col-span-2 md:col-span-4 flex items-center justify-between pt-2">
            <div className="flex items-center gap-4 text-slate-300 text-xs">
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.New_Device === 1}
                  onChange={(e) => setForm({ ...form, New_Device: e.target.checked ? 1 : 0 })}
                  className="rounded border-slate-700 text-cyan-500 focus:ring-0"
                />
                <span>New Device Flag</span>
              </label>
              <label className="flex items-center gap-1.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={form.International_Transaction === 1}
                  onChange={(e) => setForm({ ...form, International_Transaction: e.target.checked ? 1 : 0 })}
                  className="rounded border-slate-700 text-cyan-500 focus:ring-0"
                />
                <span>International Tx</span>
              </label>
            </div>

            <button
              type="submit"
              disabled={predictLoading}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-cyan-950 transition flex items-center gap-1.5 disabled:opacity-50"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${predictLoading ? 'animate-spin' : ''}`} />
              {predictLoading ? 'Scoring...' : 'Execute AI Prediction'}
            </button>
          </div>
        </form>

        {/* Live Result Callout */}
        {activeResult && (
          <div className="mt-4 p-4 rounded-xl bg-slate-950 border border-cyan-700/60 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 relative">
            {/* Dismiss button */}
            <button
              onClick={() => setActiveResult(null)}
              title="Clear result"
              className="absolute top-2 right-2 p-1 rounded-lg text-slate-500 hover:text-white hover:bg-slate-800 transition"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" /></svg>
            </button>

            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase ${
                    activeResult.prediction === 1 || activeResult.prediction === 'FRAUD'
                      ? 'bg-rose-950 text-rose-400 border border-rose-800'
                      : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                  }`}
                >
                  {activeResult.prediction === 1 || activeResult.prediction === 'FRAUD' ? 'FRAUD DETECTED' : 'GENUINE TRANSACTION'}
                </span>
                <span className="text-xs text-slate-300 font-mono">
                  Tx: {activeResult.transaction_id}
                </span>
              </div>
              <p className="text-xs text-slate-400">
                Probability: <strong className="text-white font-mono">{(Number(activeResult.fraud_probability || 0) * 100).toFixed(1)}%</strong>{' '}
                • Threshold: <strong className="text-cyan-400 font-mono">{activeResult.threshold_used ?? 0.8045}</strong>{' '}
                • Composite Risk: <strong className="text-purple-300 font-mono">{activeResult.risk_score} / 100 ({activeResult.risk_level})</strong>
              </p>
            </div>

            {onOpenExplanation && (
              <button
                onClick={() => onOpenExplanation(activeResult.transaction_id)}
                className="px-3 py-1.5 rounded-xl bg-purple-900/60 hover:bg-purple-900 text-purple-200 border border-purple-700 text-xs font-semibold transition flex items-center gap-1.5 shrink-0"
              >
                Inspect SHAP <ArrowRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        )}
      </div>

      {/* Production Predictions Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <h3 className="text-xs font-bold text-white uppercase tracking-wider">
            Recent System Model Predictions
          </h3>
          <span className="text-[10px] font-mono text-slate-400">Database Record Stream</span>
        </div>

        {loading ? (
          <div className="p-8 text-center text-xs text-slate-400">Loading predictions...</div>
        ) : error ? (
          <div className="p-6 text-center text-xs text-rose-400">{error}</div>
        ) : predictions.length === 0 ? (
          <div className="p-8 text-center text-xs text-slate-400">No predictions found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/60 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Transaction ID</th>
                  <th className="py-3 px-4">Customer</th>
                  <th className="py-3 px-4">Amount</th>
                  <th className="py-3 px-4">Probability</th>
                  <th className="py-3 px-4">Threshold</th>
                  <th className="py-3 px-4">Prediction</th>
                  <th className="py-3 px-4">Risk Level</th>
                  <th className="py-3 px-4">Model &amp; Version</th>
                  <th className="py-3 px-4 text-right">SHAP Explain</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {predictions.map((p) => {
                  const isFraud = p.prediction === 1
                  const prob = Number(p.fraud_probability || 0)

                  return (
                    <tr key={p.id || p.transaction_id} className="hover:bg-slate-800/40">
                      <td className="py-3 px-4 font-mono font-bold text-cyan-400">
                        {p.transaction_id}
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-300">{p.customer_id}</td>
                      <td className="py-3 px-4 font-mono font-bold text-white">
                        {formatINR(p.amount)}
                      </td>
                      <td className="py-3 px-4 font-mono">
                        <div className="flex items-center gap-2">
                          <span className={isFraud ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                            {(prob * 100).toFixed(1)}%
                          </span>
                          <div className="w-16 h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${isFraud ? 'bg-rose-500' : 'bg-cyan-500'}`}
                              style={{ width: `${Math.min(prob * 100, 100)}%` }}
                            />
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4 font-mono text-slate-400">{p.threshold_used ?? 0.50}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold uppercase ${
                            isFraud
                              ? 'bg-rose-950/80 text-rose-300 border border-rose-800'
                              : 'bg-emerald-950/80 text-emerald-300 border border-emerald-800'
                          }`}
                        >
                          {isFraud ? 'FRAUD' : 'GENUINE'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className="font-mono text-slate-300">
                          {p.risk_level || 'LOW'} ({p.risk_score || 0})
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-[11px] text-slate-400">
                        {p.model_name || 'XGBoost_Champion'}
                      </td>
                      <td className="py-3 px-4 text-right">
                        {onOpenExplanation && (
                          <button
                            onClick={() => onOpenExplanation(p.transaction_id)}
                            className="text-purple-400 hover:text-purple-300 font-medium text-xs flex items-center gap-1 ml-auto"
                          >
                            Explain &rarr;
                          </button>
                        )}
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
