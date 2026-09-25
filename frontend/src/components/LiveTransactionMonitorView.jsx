import React, { useState, useEffect } from 'react'
import {
  Activity,
  ShieldAlert,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Search,
  Filter,
  Eye,
  Sliders,
  Radio,
  ArrowUpRight,
  TrendingDown,
  TrendingUp,
} from 'lucide-react'
import { formatINR } from '../utils/formatters'

import { getCustomerPersona } from '../utils/customerHelper'

export default function LiveTransactionMonitorView({ onInvestigate, user, isAdmin }) {
  const customerPersona = getCustomerPersona(user)
  const isCustomer = customerPersona.isCustomer

  const [transactions, setTransactions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filterRisk, setFilterRisk] = useState('ALL')
  const [customerFilter, setCustomerFilter] = useState(isCustomer ? customerPersona.customerId : 'ALL')
  const [search, setSearch] = useState('')
  const [isLiveStreaming, setIsLiveStreaming] = useState(true)

  const getToken = () => localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')

  const fetchTransactions = async () => {
    try {
      const token = getToken()
      const res = await fetch('/api/v1/transactions?limit=50', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (res.ok) {
        const data = await res.json()
        setTransactions(data.transactions || data.items || [])
      }
    } catch (err) {
      console.error('Error fetching live transactions:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTransactions()
    let interval = null
    if (isLiveStreaming) {
      interval = setInterval(() => {
        fetchTransactions()
      }, 4000)
    }
    return () => {
      if (interval) clearInterval(interval)
    }
  }, [isLiveStreaming])

  const filtered = transactions.filter((tx) => {
    const matchRisk = filterRisk === 'ALL' || tx.risk_level === filterRisk
    const matchCustomer =
      customerFilter === 'ALL' ||
      tx.customer_id === customerFilter ||
      (customerFilter === 'CUST_MONISHA_001' && tx.customer_id?.includes('MONISHA')) ||
      (customerFilter === 'CUST_MOHANA_002' && tx.customer_id?.includes('MOHANA')) ||
      (customerFilter === 'CUST_SOWMIYA_003' && tx.customer_id?.includes('SOWMIYA'))
    const matchSearch =
      tx.transaction_id?.toLowerCase().includes(search.toLowerCase()) ||
      tx.merchant_name?.toLowerCase().includes(search.toLowerCase()) ||
      tx.customer_id?.toLowerCase().includes(search.toLowerCase())
    return matchRisk && matchCustomer && matchSearch
  })

  const highRiskCount = transactions.filter((t) => t.risk_level === 'HIGH' || t.is_fraud === 1).length
  const mediumRiskCount = transactions.filter((t) => t.risk_level === 'MEDIUM').length
  const lowRiskCount = transactions.filter((t) => t.risk_level === 'LOW').length

  return (
    <div className="space-y-6">
      {/* Live Stream Banner */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/80 border border-slate-800 p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
                STREAM ACTIVE • REAL-TIME RADAR
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-slate-800 text-slate-300">
                20,000 SYNTHETIC CANONICAL REPOSITORY
              </span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <Radio className="w-6 h-6 text-cyan-400" />
              Live Transaction Radar &amp; Fraud Monitor
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              Real-time monitoring feed of incoming transactions with instant ML scoring, risk classification, and step-up flags.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setIsLiveStreaming(!isLiveStreaming)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition ${
                isLiveStreaming
                  ? 'bg-emerald-950/80 border-emerald-700 text-emerald-300'
                  : 'bg-slate-800 border-slate-700 text-slate-400'
              }`}
            >
              <Activity className="w-4 h-4" />
              {isLiveStreaming ? 'Live Polling: ON (4s)' : 'Live Polling: PAUSED'}
            </button>
            <button
              onClick={fetchTransactions}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-xl border border-slate-700 transition"
              title="Manual Refresh"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Live Counters */}
        <div className="grid grid-cols-3 gap-3 mt-6">
          <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">High Risk &amp; Blocked</div>
              <div className="text-xl font-black font-mono text-rose-400 mt-0.5">{highRiskCount}</div>
            </div>
            <ShieldAlert className="w-6 h-6 text-rose-500/80" />
          </div>

          <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Step-Up Verifications</div>
              <div className="text-xl font-black font-mono text-amber-400 mt-0.5">{mediumRiskCount}</div>
            </div>
            <AlertTriangle className="w-6 h-6 text-amber-500/80" />
          </div>

          <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800/80 flex items-center justify-between">
            <div>
              <div className="text-[10px] font-mono uppercase text-slate-500">Legitimate Volume</div>
              <div className="text-xl font-black font-mono text-emerald-400 mt-0.5">{lowRiskCount}</div>
            </div>
            <CheckCircle2 className="w-6 h-6 text-emerald-500/80" />
          </div>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="flex flex-col md:flex-row gap-3 bg-slate-900/80 p-4 rounded-xl border border-slate-800">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search by Transaction ID, Merchant, or Customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          />
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Risk Level Pills */}
          <div className="flex gap-1.5">
            {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((risk) => (
              <button
                key={risk}
                onClick={() => setFilterRisk(risk)}
                className={`px-2.5 py-1.5 rounded-lg text-xs font-mono font-bold border transition ${
                  filterRisk === risk
                    ? 'bg-cyan-950 border-cyan-700 text-cyan-300 shadow'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                {risk}
              </button>
            ))}
          </div>

          <div className="h-6 w-px bg-slate-800 hidden sm:block" />

          {/* Real-Time Personas Filter */}
          {isCustomer ? (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs font-mono font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              <span>Monitoring Account: {customerPersona.customerName} ({customerPersona.customerId})</span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5">
              <span className="text-[10px] font-mono uppercase text-slate-400 font-bold hidden sm:inline">Persona:</span>
              <button
                onClick={() => setCustomerFilter('ALL')}
                className={`px-2 py-1.5 rounded-lg text-xs font-mono font-bold border transition ${
                  customerFilter === 'ALL'
                    ? 'bg-slate-800 border-slate-600 text-white'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-white'
                }`}
              >
                All
              </button>
              <button
                onClick={() => setCustomerFilter('CUST_MONISHA_001')}
                className={`px-2 py-1.5 rounded-lg text-xs font-mono font-bold border transition ${
                  customerFilter === 'CUST_MONISHA_001'
                    ? 'bg-emerald-950 border-emerald-600 text-emerald-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-emerald-400'
                }`}
              >
                Monisha (3%)
              </button>
              <button
                onClick={() => setCustomerFilter('CUST_MOHANA_002')}
                className={`px-2 py-1.5 rounded-lg text-xs font-mono font-bold border transition ${
                  customerFilter === 'CUST_MOHANA_002'
                    ? 'bg-amber-950 border-amber-600 text-amber-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-amber-400'
                }`}
              >
                Mohana (12%)
              </button>
              <button
                onClick={() => setCustomerFilter('CUST_SOWMIYA_003')}
                className={`px-2 py-1.5 rounded-lg text-xs font-mono font-bold border transition ${
                  customerFilter === 'CUST_SOWMIYA_003'
                    ? 'bg-rose-950 border-rose-600 text-rose-300'
                    : 'bg-slate-950 border-slate-800 text-slate-400 hover:text-rose-400'
                }`}
              >
                Sowmiya (26%)
              </button>
            </div>
          )}
        </div>
      </div>

      {/* Transactions Table */}
      <div className="bg-slate-900/90 rounded-2xl border border-slate-800 overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950 text-slate-400 font-mono text-[10px] uppercase border-b border-slate-800">
              <tr>
                <th className="p-3.5">Transaction ID</th>
                <th className="p-3.5">Merchant</th>
                <th className="p-3.5">Amount</th>
                <th className="p-3.5">Type &amp; Device</th>
                <th className="p-3.5">Fraud Prob</th>
                <th className="p-3.5">Risk Score</th>
                <th className="p-3.5">Decision</th>
                <th className="p-3.5 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-sans">
              {filtered.map((tx) => {
                const isHigh = tx.risk_level === 'HIGH' || tx.is_fraud === 1
                const isMedium = tx.risk_level === 'MEDIUM'

                return (
                  <tr
                    key={tx.transaction_id || tx.id}
                    className="hover:bg-slate-850/60 transition group"
                  >
                    <td className="p-3.5 font-mono text-slate-300 font-bold">
                      {tx.transaction_id}
                      <div className="text-[10px] text-slate-500 font-normal font-sans">
                        Cust: {tx.customer_id}
                      </div>
                    </td>

                    <td className="p-3.5">
                      <div className="font-bold text-white group-hover:text-cyan-300 transition">
                        {tx.merchant_name || tx.merchant_category || 'Merchant'}
                      </div>
                      <div className="text-[10px] text-slate-400 font-mono">
                        {tx.merchant_id || tx.merchant_category}
                      </div>
                    </td>

                    <td className="p-3.5 font-mono font-bold text-slate-200">
                      {formatINR(tx.amount)}
                    </td>

                    <td className="p-3.5 text-slate-300">
                      <div className="font-medium">{tx.transaction_type || 'UPI'}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{tx.device_type || 'mobile'}</div>
                    </td>

                    <td className="p-3.5 font-mono text-slate-300 font-bold">
                      {tx.fraud_probability !== undefined && tx.fraud_probability !== null
                        ? `${(tx.fraud_probability * 100).toFixed(1)}%`
                        : '—'}
                    </td>

                    <td className="p-3.5 font-mono">
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
                    </td>

                    <td className="p-3.5">
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full ${
                          isHigh
                            ? 'bg-rose-950 text-rose-400 border border-rose-800'
                            : isMedium
                            ? 'bg-amber-950 text-amber-400 border border-amber-800'
                            : 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        }`}
                      >
                        {tx.decision || (isHigh ? 'BLOCK' : isMedium ? 'VERIFY' : 'ALLOW')}
                      </span>
                    </td>

                    <td className="p-3.5 text-right">
                      {onInvestigate && (
                        <button
                          onClick={() => onInvestigate(tx.transaction_id)}
                          className="px-2.5 py-1 rounded bg-slate-800 hover:bg-cyan-950 text-slate-300 hover:text-cyan-300 border border-slate-700 hover:border-cyan-700 font-medium text-[11px] transition inline-flex items-center gap-1"
                        >
                          <Eye className="w-3 h-3" />
                          Investigate
                        </button>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
