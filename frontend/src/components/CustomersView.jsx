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
  ShieldCheck,
  ShieldAlert,
  UserCheck,
  DollarSign,
  MapPin,
  Calendar,
  ExternalLink,
} from 'lucide-react'
import { customersApi } from '../services/api'
import { formatINR } from '../utils/formatters'
import { getCustomerPersona } from '../utils/customerHelper'

export default function CustomersView({ onSelectTransaction, user, isAdmin }) {
  const customerPersona = getCustomerPersona(user)
  const isCustomer = customerPersona.isCustomer

  const [customers, setCustomers] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(15)
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
      // 1. Fetch detailed customer metrics & recent transactions
      const [detailData, txsData] = await Promise.allSettled([
        customersApi.get(cust.customer_id),
        customersApi.getTransactions(cust.customer_id, { page: 1, limit: 50 }),
      ])

      let loadedTxs = []
      if (txsData.status === 'fulfilled' && txsData.value) {
        loadedTxs = txsData.value.items || txsData.value.transactions || []
      }
      if (loadedTxs.length === 0 && detailData.status === 'fulfilled' && detailData.value) {
        loadedTxs = detailData.value.recent_transactions || []
      }

      setCustTxs(loadedTxs)

      if (detailData.status === 'fulfilled' && detailData.value) {
        setSelectedCust((prev) => ({
          ...prev,
          ...detailData.value,
          behavioral_stats: detailData.value.behavioral_stats || prev?.behavioral_stats,
        }))
      }
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
      {/* Top Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/70 border border-slate-800 p-6 shadow-xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold ${
                isCustomer ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' : 'bg-cyan-950 text-cyan-400 border border-cyan-800'
              }`}>
                {isCustomer ? `AUTHENTICATED CUSTOMER: ${customerPersona.customerName}` : '15 SYNTHETIC CUSTOMER PROFILES'}
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-indigo-950 text-indigo-300 border border-indigo-800">
                {isCustomer ? `ACCOUNT ID: ${customerPersona.customerId}` : '10 MALE • 5 FEMALE TAMIL IDENTITIES'}
              </span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <Users className="w-6 h-6 text-cyan-400" />
              {isCustomer ? 'My Customer Profile & Behavioral Baseline' : 'Customer Profiles & Behavioral Baseline Analysis'}
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              {isCustomer
                ? `Review your individual spending baseline, typical ticket sizes in ₹ INR, historical velocity, and registered device fingerprints.`
                : 'Monitor individual spending baselines, typical ticket sizes in ₹ INR, historical velocity, and detect account takeover anomalies.'}
            </p>
          </div>

          <button
            onClick={fetchCustomers}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs border border-slate-700 transition shadow self-start md:self-auto"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            Refresh Directory
          </button>
        </div>
      </div>

      {/* Search Bar / Customer Isolation Notice */}
      {isCustomer ? (
        <div className="p-3.5 rounded-xl bg-slate-900/80 border border-emerald-800/60 shadow-md flex items-center justify-between text-xs text-slate-300">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-400 shrink-0" />
            <span>Customer Privacy Enforcement Active: You are strictly scoped to your verified account profile (<strong>{customerPersona.customerId}</strong>). Cross-customer viewing is restricted to System Administrators.</span>
          </div>
        </div>
      ) : (
        <div className="p-4 rounded-xl bg-slate-900/80 border border-slate-800 shadow-md flex flex-col sm:flex-row items-center justify-between gap-3">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 w-full sm:max-w-md">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search customer by ID or Name (e.g. Murugan, CUST_001)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              type="submit"
              className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-xs font-bold text-white transition shadow"
            >
              Search
            </button>
          </form>
          <div className="text-xs text-slate-400 font-mono">
            Showing <strong className="text-white">{customers.length}</strong> of <strong className="text-white">{total}</strong> registered profiles
          </div>
        </div>
      )}

      {/* Customer Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2 bg-slate-900/40 rounded-2xl border border-slate-800">
          <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
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
            const hasFraudHistory = (c.fraud_transaction_count || 0) > 0
            const hasHighRisk = (c.high_risk_count || 0) > 0

            return (
              <div
                key={c.id || c.customer_id}
                onClick={() => handleOpenCustomer(c)}
                className="p-5 rounded-2xl bg-slate-900/80 border border-slate-800 hover:border-cyan-500 transition cursor-pointer shadow-lg flex flex-col justify-between group relative overflow-hidden"
              >
                <div>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <span className="font-mono text-[11px] font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800 block w-fit mb-1">
                        {c.customer_id}
                      </span>
                      <h3 className="text-base font-bold text-white group-hover:text-cyan-300 transition">
                        {c.name || `Customer ${c.customer_id}`}
                      </h3>
                    </div>
                    <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-950 border border-slate-800 text-slate-400 shrink-0">
                      {c.account_age_days || 0}d tenure
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                    <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 uppercase font-mono block">Total Txs</span>
                      <span className="font-mono font-bold text-white text-sm">{c.transaction_count || 0}</span>
                    </div>
                    <div className="p-2.5 bg-slate-950/80 rounded-xl border border-slate-800/80">
                      <span className="text-[10px] text-slate-400 uppercase font-mono block">Hist. Avg Ticket</span>
                      <span className="font-mono font-bold text-cyan-300 text-sm">
                        {formatINR(c.historical_avg_amount || 0)}
                      </span>
                    </div>
                  </div>

                  {/* Available Cash Liquidity (includes ₹15 Lakhs Feature Cash) */}
                  <div className="p-2.5 bg-gradient-to-r from-emerald-950/70 via-slate-950/80 to-cyan-950/70 rounded-xl border border-emerald-700/60 mb-3 flex items-center justify-between">
                    <div>
                      <span className="text-[9px] text-emerald-400 uppercase font-mono font-bold block">Available Cash</span>
                      <span className="font-mono font-black text-emerald-300 text-sm">
                        {formatINR(c.simulated_balance || 1500000.0)}
                      </span>
                    </div>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 font-bold border border-emerald-600">
                      +₹15L Feature
                    </span>
                  </div>

                  {/* Status Flags */}
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {hasFraudHistory ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-950 text-rose-300 border border-rose-800">
                        ⚠ {c.fraud_transaction_count} Fraud Flagged
                      </span>
                    ) : hasHighRisk ? (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-950 text-amber-300 border border-amber-800">
                        {c.high_risk_count} High Risk Flags
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                        ✓ Clean History
                      </span>
                    )}
                  </div>
                </div>

                <div className="mt-4 pt-3 border-t border-slate-800/80 text-[11px] text-cyan-400 font-medium font-mono flex items-center justify-between group-hover:translate-x-0.5 transition-transform">
                  <span>Inspect Customer Ledger</span>
                  <span className="text-xs">&rarr;</span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Customer Profile & Dedicated Transactions Modal */}
      {selectedCust && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="max-w-3xl w-full rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl p-6 space-y-5 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div className="flex items-center gap-2.5">
                <div className="p-2 rounded-xl bg-cyan-950 text-cyan-400 border border-cyan-800">
                  <UserCheck className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-white flex items-center gap-2">
                    {selectedCust.name || selectedCust.customer_id}
                    <span className="font-mono text-xs text-cyan-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
                      {selectedCust.customer_id}
                    </span>
                  </h3>
                  <div className="text-xs text-slate-400">{selectedCust.email || `${selectedCust.customer_id.toLowerCase()}@customer.fraudlens.ai`}</div>
                </div>
              </div>
              <button
                onClick={() => setSelectedCust(null)}
                className="p-1.5 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition text-xs"
              >
                ✕ Close
              </button>
            </div>
            {/* Available Cash Liquidity & Wallet Reserve */}
            <div className="p-3.5 rounded-xl bg-gradient-to-r from-emerald-950/70 via-slate-900 to-cyan-950/70 border border-emerald-600/70 flex items-center justify-between font-mono">
              <div>
                <span className="text-[10px] text-emerald-400 uppercase tracking-wider block font-bold">
                  Available Cash Liquidity / Wallet
                </span>
                <span className="text-xl font-black text-emerald-300">
                  {formatINR(selectedCust.simulated_balance || 1500000.0)}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-900/90 text-emerald-200 border border-emerald-600 font-bold">
                  +₹15 Lakhs Extra Cash Added
                </span>
                <div className="text-[10px] text-slate-400 mt-0.5">Real-Time Instant Pre-Auth Liquidity</div>
              </div>
            </div>

            {/* Baseline Profile Stats */}
            <div className="grid grid-cols-3 gap-3 font-mono text-center">
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Tenure</div>
                <div className="text-base font-bold text-white mt-0.5">{selectedCust.account_age_days} Days</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Average Amount</div>
                <div className="text-base font-bold text-cyan-300 mt-0.5">{formatINR(selectedCust.historical_avg_amount || 0)}</div>
              </div>
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
                <div className="text-[10px] text-slate-500 uppercase">Recorded Txs</div>
                <div className="text-base font-bold text-slate-200 mt-0.5">{selectedCust.transaction_count}</div>
              </div>
            </div>

            {/* Customer's Individual Transactions Ledger */}
            <div>
              <div className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2.5 flex items-center justify-between">
                <span>Recent Transactions for this Customer</span>
                <span className="text-[10px] font-mono text-slate-500">Filtered by {selectedCust.customer_id}</span>
              </div>

              {detailLoading ? (
                <div className="p-8 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
                  <RefreshCw className="w-5 h-5 animate-spin text-cyan-400" />
                  <span>Loading customer transaction history...</span>
                </div>
              ) : custTxs.length === 0 ? (
                <div className="p-6 text-center text-xs text-slate-500 bg-slate-950 rounded-xl border border-slate-800">
                  No transaction records found for this specific customer.
                </div>
              ) : (
                <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                  {custTxs.map((tx) => {
                    const isHigh = tx.risk_level === 'HIGH' || tx.is_fraud === 1
                    const isMedium = tx.risk_level === 'MEDIUM'

                    return (
                      <div
                        key={tx.transaction_id || tx.id}
                        className="flex items-center justify-between p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs hover:border-slate-700 transition"
                      >
                        <div>
                          <div className="font-bold text-white flex items-center gap-2">
                            <span>{tx.merchant_name || tx.merchant_category || 'Merchant'}</span>
                            <span className="font-mono text-[10px] text-slate-500">({tx.transaction_type})</span>
                          </div>
                          <div className="text-[10px] font-mono text-slate-400 mt-0.5">
                            {tx.transaction_id} • {tx.created_at ? new Date(tx.created_at).toLocaleString() : 'Recent'}
                          </div>
                        </div>

                        <div className="text-right font-mono">
                          <div className="font-bold text-slate-200">{formatINR(tx.amount)}</div>
                          <span
                            className={`px-1.5 py-0.2 rounded text-[9px] font-bold ${
                              isHigh
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : isMedium
                                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            }`}
                          >
                            Score: {tx.risk_score || 0}
                          </span>
                        </div>
                      </div>
                    )
                  })}
                </div>
              )}
            </div>

            <div className="pt-2 border-t border-slate-800 flex justify-end">
              <button
                onClick={() => setSelectedCust(null)}
                className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-white transition"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
