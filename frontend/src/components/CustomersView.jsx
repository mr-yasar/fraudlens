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
  Zap,
  Sparkles,
} from 'lucide-react'
import { customersApi, paymentApi } from '../services/api'
import { formatINR } from '../utils/formatters'
import { getCustomerPersona } from '../utils/customerHelper'
import GlobalCenterModal from './common/GlobalCenterModal'

function getCustomerBalance(c) {
  if (c?.simulated_balance !== null && c?.simulated_balance !== undefined) {
    return c.simulated_balance
  }
  const cid = String(c?.customer_id || c?.id || '').toUpperCase()
  if (cid.includes('MONISHA')) return 45000.0
  if (cid.includes('MOHANA')) return 60000.0
  if (cid.includes('SOWMIYA')) return 80000.0
  if (cid.includes('AJAY')) return 300000.0
  return 50000.0
}

export default function CustomersView({ onSelectTransaction, user, isAdmin }) {
  const customerPersona = getCustomerPersona(user) || {}
  const isCustomer = !isAdmin && Boolean(customerPersona.isCustomer)

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

  // Demo Liquidity Simulator Handlers (5L, 10L, 20L)
  const [injectingId, setInjectingId] = useState(null)
  const [liquiditySuccess, setLiquiditySuccess] = useState(null)

  const handleInjectLiquidity = async (customerId, amountInRupees) => {
    if (!customerId) return
    setInjectingId(customerId)
    try {
      const res = await paymentApi.injectDemoLiquidity(customerId, {
        amount: amountInRupees,
        action: 'SET',
      })
      setCustomers((prev) =>
        prev.map((c) =>
          c.customer_id === customerId
            ? { ...c, simulated_balance: res.simulated_balance }
            : c
        )
      )
      if (selectedCust?.customer_id === customerId) {
        setSelectedCust((prev) => ({ ...prev, simulated_balance: res.simulated_balance }))
      }
      setLiquiditySuccess(`✓ Injected ₹${(amountInRupees / 100000).toFixed(0)} Lakhs for ${customerId}!`)
      setTimeout(() => setLiquiditySuccess(null), 3500)
    } catch (e) {
      console.error(e)
    } finally {
      setInjectingId(null)
    }
  }

  const handleResetLiquidity = async (customerId) => {
    if (!customerId) return
    setInjectingId(customerId)
    try {
      const res = await paymentApi.injectDemoLiquidity(customerId, {
        amount: 0,
        action: 'RESET',
      })
      setCustomers((prev) =>
        prev.map((c) =>
          c.customer_id === customerId
            ? { ...c, simulated_balance: res.simulated_balance }
            : c
        )
      )
      if (selectedCust?.customer_id === customerId) {
        setSelectedCust((prev) => ({ ...prev, simulated_balance: res.simulated_balance }))
      }
      setLiquiditySuccess(`✓ Reset balance for ${customerId} to ₹${res.simulated_balance.toLocaleString('en-IN')}`)
      setTimeout(() => setLiquiditySuccess(null), 3500)
    } catch (e) {
      console.error(e)
    } finally {
      setInjectingId(null)
    }
  }

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
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
              isCustomer ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
            }`}>
              {isCustomer ? `MY CUSTOMER PROFILE: ${customerPersona.customerName}` : 'ADMIN CUSTOMER DIRECTORY'}
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {isCustomer ? 'Zero Data Leakage (Self Only)' : 'Global Directory of Consumer Profiles'}
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Users className="w-5 h-5 text-cyan-400" />
            Customer Behavioral Profiles &amp; Liquidity
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            View profiles, active liquidity, historical ticket metrics, risk flags, and full transaction history.
          </p>
        </div>

        <button
          onClick={fetchCustomers}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 hover:text-white text-xs font-semibold transition"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          Refresh Customers
        </button>
      </div>

      {/* Filter & Search Bar */}
      <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-md flex items-center justify-between gap-4">
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search customers by ID (e.g. CUST_MONISHA_001) or Name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full bg-slate-950/80 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-400 focus:outline-none focus:border-cyan-500 font-mono"
            />
          </div>
          <button
            type="submit"
            className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold border border-slate-700 transition"
          >
            Search
          </button>
        </form>

        <div className="text-xs text-slate-400 font-mono">
          Total Customers: <strong className="text-white">{total.toLocaleString()}</strong>
        </div>
      </div>

      {/* Customers Cards Grid */}
      {loading ? (
        <div className="p-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
          <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
          <span>Loading customer behavioral profiles...</span>
        </div>
      ) : error ? (
        <div className="p-6 rounded-2xl bg-rose-950/40 border border-rose-800 text-rose-300 text-xs text-center">
          {error}
        </div>
      ) : customers.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-400">
          No customer profiles found matching your search.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
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

                  {/* Available Cash Liquidity */}
                  <div className="p-2.5 bg-gradient-to-r from-emerald-950/70 via-slate-950/80 to-cyan-950/70 rounded-xl border border-emerald-700/60 mb-2 flex items-center justify-between">
                    <div>
                      <span className="text-[9px] text-emerald-400 uppercase font-mono font-bold block">Available Cash</span>
                      <span className="font-mono font-black text-emerald-300 text-sm">
                        {formatINR(getCustomerBalance(c))}
                      </span>
                    </div>
                    <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-emerald-950 text-emerald-300 font-bold border border-emerald-600">
                      Active Cash
                    </span>
                  </div>

                  {/* Demo Liquidity Box (5L, 10L, 20L) for Fraud Testing */}
                  <div className="p-2 bg-slate-950/90 rounded-xl border border-amber-500/30 mb-3" onClick={(e) => e.stopPropagation()}>
                    <div className="flex items-center justify-between text-[9px] font-mono text-amber-300 font-bold mb-1.5">
                      <span className="flex items-center gap-1">
                        <Zap className="w-2.5 h-2.5 text-amber-400" />
                        Demo Liquidity:
                      </span>
                      <span className="text-[8px] text-slate-400 font-normal">Fraud Testing</span>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        type="button"
                        disabled={injectingId === c.customer_id}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleInjectLiquidity(c.customer_id, 500000)
                        }}
                        className={`flex-1 py-1 rounded text-[10px] font-mono font-bold transition cursor-pointer text-center ${
                          getCustomerBalance(c) === 500000
                            ? 'bg-amber-500 text-slate-950 font-black'
                            : 'bg-slate-900 hover:bg-amber-950/60 text-amber-300 border border-amber-500/30'
                        }`}
                        title="Set ₹5 Lakhs for testing high-ticket fraud"
                      >
                        5L
                      </button>
                      <button
                        type="button"
                        disabled={injectingId === c.customer_id}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleInjectLiquidity(c.customer_id, 1000000)
                        }}
                        className={`flex-1 py-1 rounded text-[10px] font-mono font-bold transition cursor-pointer text-center ${
                          getCustomerBalance(c) === 1000000
                            ? 'bg-amber-500 text-slate-950 font-black'
                            : 'bg-slate-900 hover:bg-amber-950/60 text-amber-300 border border-amber-500/30'
                        }`}
                        title="Set ₹10 Lakhs for testing high-ticket fraud"
                      >
                        10L
                      </button>
                      <button
                        type="button"
                        disabled={injectingId === c.customer_id}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleInjectLiquidity(c.customer_id, 2000000)
                        }}
                        className={`flex-1 py-1 rounded text-[10px] font-mono font-bold transition cursor-pointer text-center ${
                          getCustomerBalance(c) === 2000000
                            ? 'bg-amber-500 text-slate-950 font-black'
                            : 'bg-slate-900 hover:bg-amber-950/60 text-amber-300 border border-amber-500/30'
                        }`}
                        title="Set ₹20 Lakhs for testing high-ticket fraud"
                      >
                        20L
                      </button>
                      <button
                        type="button"
                        disabled={injectingId === c.customer_id}
                        onClick={(e) => {
                          e.stopPropagation()
                          handleResetLiquidity(c.customer_id)
                        }}
                        className="px-1.5 py-1 rounded text-[10px] font-mono text-slate-400 hover:text-white bg-slate-900 border border-slate-700 transition cursor-pointer"
                        title="Reset balance to baseline"
                      >
                        ↺
                      </button>
                    </div>
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

      {/* Customer Profile & Dedicated Transactions Global Center Modal */}
      {selectedCust && (
        <GlobalCenterModal
          isOpen={Boolean(selectedCust)}
          onClose={() => setSelectedCust(null)}
          title={selectedCust.name || selectedCust.customer_id}
          subtitle={`Customer ID: ${selectedCust.customer_id} • Email: ${selectedCust.email || `${selectedCust.customer_id.toLowerCase()}@customer.fraudlens.ai`}`}
          badge={
            (selectedCust.fraud_transaction_count || 0) > 0
              ? 'FRAUD FLAGGED'
              : (selectedCust.high_risk_count || 0) > 0
              ? 'ELEVATED RISK'
              : 'VERIFIED CUSTOMER'
          }
          badgeType={
            (selectedCust.fraud_transaction_count || 0) > 0
              ? 'danger'
              : (selectedCust.high_risk_count || 0) > 0
              ? 'warning'
              : 'success'
          }
          icon={UserCheck}
          maxWidth="max-w-3xl"
        >
          <div className="space-y-4">
            {/* Available Cash Liquidity & Wallet Reserve */}
            <div className="p-4 rounded-2xl bg-gradient-to-r from-emerald-950/80 via-slate-900 to-cyan-950/80 border border-emerald-600/70 flex items-center justify-between font-mono">
              <div>
                <span className="text-[10px] text-emerald-400 uppercase tracking-wider block font-bold">
                  Available Cash Liquidity / Wallet
                </span>
                <span className="text-2xl font-black text-emerald-300">
                  {formatINR(getCustomerBalance(selectedCust))}
                </span>
              </div>
              <div className="text-right">
                <span className="text-[10px] px-2.5 py-1 rounded-lg bg-emerald-900/90 text-emerald-200 border border-emerald-600 font-bold">
                  Verified Account Liquidity
                </span>
                <div className="text-[10px] text-slate-400 mt-1">Real-Time Instant Pre-Auth Liquidity</div>
              </div>
            </div>

            {/* Demo Liquidity Injector for High-Value Testing */}
            <div className="p-3 rounded-2xl bg-gradient-to-r from-amber-950/40 via-purple-950/30 to-indigo-950/40 border border-amber-500/30 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-lg">
              <div className="flex items-center gap-2.5">
                <span className="p-2 rounded-xl bg-amber-500/15 text-amber-400 border border-amber-500/30">
                  <Zap className="w-4 h-4 text-amber-400 animate-pulse" />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-amber-300 font-mono uppercase tracking-wider">
                      Demo Liquidity Injector
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-mono font-bold bg-amber-500/20 text-amber-200 border border-amber-500/40">
                      FRAUD DETECTION
                    </span>
                  </div>
                  <p className="text-[11px] text-slate-300 mt-0.5">
                    Inject 5, 10, or 20 Lakhs to test large-ticket anomaly scoring and FinCEN SAR rules.
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2 shrink-0">
                <button
                  type="button"
                  disabled={injectingId === selectedCust.customer_id}
                  onClick={() => handleInjectLiquidity(selectedCust.customer_id, 500000)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition flex items-center gap-1 cursor-pointer ${
                    getCustomerBalance(selectedCust) === 500000
                      ? 'bg-amber-500 text-slate-950 font-black'
                      : 'bg-slate-900 hover:bg-amber-950/60 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  <Sparkles className="w-3 h-3" />
                  ₹5L
                </button>
                <button
                  type="button"
                  disabled={injectingId === selectedCust.customer_id}
                  onClick={() => handleInjectLiquidity(selectedCust.customer_id, 1000000)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition flex items-center gap-1 cursor-pointer ${
                    getCustomerBalance(selectedCust) === 1000000
                      ? 'bg-amber-500 text-slate-950 font-black'
                      : 'bg-slate-900 hover:bg-amber-950/60 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  <Sparkles className="w-3 h-3" />
                  ₹10L
                </button>
                <button
                  type="button"
                  disabled={injectingId === selectedCust.customer_id}
                  onClick={() => handleInjectLiquidity(selectedCust.customer_id, 2000000)}
                  className={`px-3 py-1.5 rounded-xl text-xs font-mono font-bold transition flex items-center gap-1 cursor-pointer ${
                    getCustomerBalance(selectedCust) === 2000000
                      ? 'bg-amber-500 text-slate-950 font-black'
                      : 'bg-slate-900 hover:bg-amber-950/60 text-amber-300 border border-amber-500/30'
                  }`}
                >
                  <Sparkles className="w-3 h-3" />
                  ₹20L
                </button>
                <button
                  type="button"
                  disabled={injectingId === selectedCust.customer_id}
                  onClick={() => handleResetLiquidity(selectedCust.customer_id)}
                  className="px-2 py-1.5 rounded-xl text-xs font-mono text-slate-400 hover:text-white bg-slate-900 border border-slate-700 transition cursor-pointer"
                  title="Reset to baseline"
                >
                  ↺ Reset
                </button>
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
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
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
          </div>
        </GlobalCenterModal>
      )}
    </div>
  )
}
