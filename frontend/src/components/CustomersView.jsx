import React, { useState, useEffect } from 'react'
import {
  Users,
  Search,
  ChevronLeft,
  ChevronRight,
  TrendingUp,
  AlertTriangle,
  Clock,
  CreditCard,
  X,
  RefreshCw,
  Activity,
} from 'lucide-react'
import { customersApi } from '../services/api'

export default function CustomersView({ onSelectTransaction }) {
  const [customers, setCustomers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(12)
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Customer detail modal
  const [selectedCust, setSelectedCust] = useState(null)
  const [custTxs, setCustTxs] = useState([])
  const [detailLoading, setDetailLoading] = useState(false)

  const fetchCustomers = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await customersApi.list({
        page,
        limit,
        search: searchQuery,
      })
      setCustomers(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load customers')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCustomers()
  }, [page])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    setPage(1)
    fetchCustomers()
  }

  const handleOpenCustomer = async (cust) => {
    setSelectedCust(cust)
    setDetailLoading(true)
    try {
      const txData = await customersApi.getTransactions(cust.customer_id, { page: 1, limit: 10 })
      setCustTxs(txData.items || [])
    } catch (err) {
      console.error('Error fetching customer transactions:', err)
      setCustTxs([])
    } finally {
      setDetailLoading(false)
    }
  }

  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div>
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Users className="w-5 h-5 text-cyan-400" />
          Customer Profiles &amp; Behavioral Baseline Analysis
        </h2>
        <p className="text-xs text-slate-400 mt-0.5">
          Inspect customer spending baselines, account tenure, historical averages, and behavioral anomalies.
        </p>
      </div>

      {/* Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex items-center justify-between gap-3">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by Customer ID (e.g., CUST-1001)..."
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

        <button
          onClick={fetchCustomers}
          className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition"
          title="Refresh"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
        </button>
      </div>

      {/* Customer Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
          <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
          <span>Synchronizing customer profile baselines...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs text-center">
          {error}
        </div>
      ) : customers.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-400 space-y-2 bg-slate-900/60 rounded-2xl border border-slate-800">
          <Users className="w-8 h-8 mx-auto text-slate-600" />
          <div className="font-semibold text-slate-300">No customer records found</div>
          <p>No customers match the active query.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {customers.map((c) => {
            const hasChargebacks = (c.previous_chargebacks || 0) > 0
            const hasFraudHistory = (c.fraud_transaction_count || 0) > 0

            return (
              <div
                key={c.id || c.customer_id}
                onClick={() => handleOpenCustomer(c)}
                className="p-4 rounded-2xl bg-slate-900/70 border border-slate-800 hover:border-cyan-700/60 transition cursor-pointer shadow-lg backdrop-blur-md flex flex-col justify-between group"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-mono font-bold text-sm text-cyan-400 group-hover:text-cyan-300 transition">
                      {c.customer_id}
                    </span>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400">
                      {c.account_age_days || 0} days tenure
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs mb-3">
                    <div className="p-2 bg-slate-950/60 rounded-lg">
                      <span className="text-[10px] text-slate-400 uppercase font-mono block">Total Tx</span>
                      <span className="font-mono font-bold text-white">{c.total_transactions || 0}</span>
                    </div>
                    <div className="p-2 bg-slate-950/60 rounded-lg">
                      <span className="text-[10px] text-slate-400 uppercase font-mono block">Hist. Avg Amount</span>
                      <span className="font-mono font-bold text-slate-200">
                        ${Number(c.historical_avg_amount || c.average_amount || 0).toFixed(2)}
                      </span>
                    </div>
                  </div>

                  {/* Status Flags */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {hasChargebacks && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-amber-950/80 text-amber-300 border border-amber-800/80">
                        {c.previous_chargebacks} Chargebacks
                      </span>
                    )}
                    {hasFraudHistory && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-950/80 text-rose-300 border border-rose-800/80">
                        {c.fraud_transaction_count} Prior Fraud
                      </span>
                    )}
                    {!hasChargebacks && !hasFraudHistory && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-950/60 text-emerald-300 border border-emerald-900/60">
                        Clean History
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-cyan-400/80 font-mono flex items-center justify-between">
                  <span>Inspect Timeline</span>
                  <span className="text-xs">&rarr;</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Pagination Footer */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 flex items-center justify-between text-xs text-slate-400">
        <div>
          Showing Page <span className="text-white font-mono">{page}</span> of{' '}
          <span className="text-white font-mono">{totalPages}</span> ({total} customers)
        </div>
        <div className="flex items-center gap-2">
          <button
            disabled={page <= 1}
            onClick={() => setPage(page - 1)}
            className="p-1.5 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white"
          >
            <ChevronLeft className="w-4 h-4" />
          </button>
          <button
            disabled={page >= totalPages}
            onClick={() => setPage(page + 1)}
            className="p-1.5 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white"
          >
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Customer Profile & Behavioral Baseline Modal */}
      {selectedCust && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="max-w-2xl w-full rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2">
                <Users className="w-5 h-5 text-cyan-400" />
                <h3 className="text-base font-bold text-white">
                  Customer Baseline: <span className="font-mono text-cyan-400">{selectedCust.customer_id}</span>
                </h3>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setSelectedCust(null)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition"
                >
                  <svg xmlns="http://www.w3.org/2000/svg" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M10 19l-7-7m0 0l7-7m-7 7h18" /></svg>
                  Back to Customers
                </button>
                <button
                  onClick={() => setSelectedCust(null)}
                  className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition"
                  title="Close"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Behavioral Anomaly Comparison Banner */}
            <div className="p-4 rounded-xl bg-slate-950 border border-cyan-900/60 space-y-2">
              <div className="flex items-center justify-between text-xs font-semibold text-slate-200">
                <span className="flex items-center gap-1.5">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  Behavioral Spending Envelope
                </span>
                <span className="text-[11px] font-mono text-cyan-400">
                  Tenure: {selectedCust.account_age_days || 0} days
                </span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed">
                Transactions significantly exceeding historical baseline trigger{' '}
                <span className="text-amber-300 font-medium">Behavioral anomaly detected</span> alerts without
                assuming absolute fraudulent intent.
              </p>
              <div className="grid grid-cols-3 gap-2 pt-1 font-mono text-xs text-center">
                <div className="p-2 bg-slate-900 rounded-lg">
                  <span className="text-[10px] text-slate-400 uppercase block">Min Amount</span>
                  <span className="font-bold text-slate-200">
                    ${Number(selectedCust.historical_min_amount || selectedCust.min_amount || 0).toFixed(2)}
                  </span>
                </div>
                <div className="p-2 bg-slate-900 rounded-lg">
                  <span className="text-[10px] text-cyan-400 uppercase block">Historical Avg</span>
                  <span className="font-bold text-cyan-300">
                    ${Number(selectedCust.historical_avg_amount || selectedCust.average_amount || 0).toFixed(2)}
                  </span>
                </div>
                <div className="p-2 bg-slate-900 rounded-lg">
                  <span className="text-[10px] text-slate-400 uppercase block">Max Amount</span>
                  <span className="font-bold text-slate-200">
                    ${Number(selectedCust.historical_max_amount || selectedCust.max_amount || 0).toFixed(2)}
                  </span>
                </div>
              </div>
            </div>

            {/* Recent Customer Transactions */}
            <div>
              <h4 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center justify-between">
                <span>Recent Customer Activity</span>
                <span className="text-[10px] font-mono text-slate-400">PostgreSQL Stream</span>
              </h4>

              {detailLoading ? (
                <div className="p-6 text-center text-xs text-slate-400">Loading customer history...</div>
              ) : custTxs.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500 bg-slate-950/60 rounded-xl border border-slate-800">
                  No individual transactions recorded for this customer.
                </div>
              ) : (
                <div className="overflow-x-auto rounded-xl border border-slate-800">
                  <table className="w-full text-left text-xs">
                    <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Transaction</th>
                        <th className="py-2.5 px-3">Amount</th>
                        <th className="py-2.5 px-3">Category</th>
                        <th className="py-2.5 px-3">Risk Level</th>
                        <th className="py-2.5 px-3">Probability</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 bg-slate-950/40">
                      {custTxs.map((tx) => (
                        <tr key={tx.id || tx.transaction_id} className="hover:bg-slate-800/40">
                          <td className="py-2 px-3 font-mono text-cyan-400 font-semibold">{tx.transaction_id}</td>
                          <td className="py-2 px-3 font-mono font-bold text-white">${Number(tx.amount).toFixed(2)}</td>
                          <td className="py-2 px-3 capitalize text-slate-300">{tx.merchant_category || 'N/A'}</td>
                          <td className="py-2 px-3">
                            <span
                              className={`px-1.5 py-0.5 rounded text-[10px] font-mono font-bold ${
                                tx.risk_level === 'HIGH'
                                  ? 'bg-rose-950 text-rose-300'
                                  : tx.risk_level === 'MEDIUM'
                                  ? 'bg-amber-950 text-amber-300'
                                  : 'bg-emerald-950 text-emerald-300'
                              }`}
                            >
                              {tx.risk_level || 'LOW'} ({tx.risk_score || 0})
                            </span>
                          </td>
                          <td className="py-2 px-3 font-mono text-slate-300">
                            {tx.fraud_probability !== null ? `${(tx.fraud_probability * 100).toFixed(1)}%` : 'N/A'}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedCust(null)}
                className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
