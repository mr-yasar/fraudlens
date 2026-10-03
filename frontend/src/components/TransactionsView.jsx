import React, { useState, useEffect } from 'react'
import {
  Search,
  CreditCard,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  Eye,
  ShieldAlert,
  Sparkles,
  X,
  Store,
  Building2,
} from 'lucide-react'
import { transactionsApi, investigationsApi } from '../services/api'
import { formatINR } from '../utils/formatters'
import { getCustomerPersona } from '../utils/customerHelper'
import GlobalCenterModal from './common/GlobalCenterModal'
import ContextualModuleHelp from './common/ContextualModuleHelp'

export default function TransactionsView({ onViewExplanation, user, isAdmin }) {
  const customerPersona = getCustomerPersona(user)
  const isCustomer = customerPersona.isCustomer

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

  // Case creation notification
  const [caseMsg, setCaseMsg] = useState(null)

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
        customer_id: isCustomer ? customerPersona.customerId : undefined,
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


  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className="space-y-6">
      {/* Top Header & Simulation Action */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-bold ${
              isCustomer ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-purple-950 text-purple-300 border border-purple-800'
            }`}>
              {isCustomer ? `ACCOUNT: ${customerPersona.customerName} (${customerPersona.customerId})` : 'ADMIN MASTER AUDIT MODE'}
            </span>
            <span className="text-[10px] font-mono text-slate-400">
              {isCustomer ? 'Personal Account Isolation Active (My Data Only)' : 'Full Multi-Merchant Audit (29,009 Records Across 29 Merchants)'}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <h2 className="text-xl font-bold text-white flex items-center gap-2">
              {isCustomer ? <CreditCard className="w-5 h-5 text-emerald-400" /> : <Store className="w-5 h-5 text-purple-400" />}
              {isCustomer ? 'My Account Transactions' : 'All Merchant Transactions & Master Audit Stream'}
            </h2>
            <ContextualModuleHelp moduleKey="transactions" />
          </div>
          <p className="text-xs text-slate-400 mt-0.5">
            {isCustomer
              ? `Real-time ledger of authorized payments, personal risk scores, and telemetry for ${customerPersona.customerName} (${customerPersona.fraudRate} fraud baseline).`
              : 'Audit 29,009 master financial transactions across all 29 certified merchants, evaluate multi-factor risk scores, and investigate flagged cases.'}
          </p>
        </div>
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

        <div className="flex flex-wrap items-center gap-2">
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
            <option value="LOW">Low Risk</option>
            <option value="MEDIUM">Medium Risk</option>
            <option value="HIGH">High Risk</option>
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
            <option value="">All Decisions</option>
            <option value="0">Genuine (0)</option>
            <option value="1">Fraud (1)</option>
          </select>

          <button
            onClick={() => {
              setRiskFilter('')
              setPredictionFilter('')
              setSearchQuery('')
              setPage(1)
              fetchTransactions()
            }}
            className="p-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-slate-200 border border-slate-700 transition"
            title="Reset Filters"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Transactions Table */}
      <div className="rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 text-[10px] uppercase font-mono text-slate-400 border-b border-slate-800">
              <tr>
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">Customer</th>
                <th className="py-3 px-4">Merchant</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Risk Level</th>
                <th className="py-3 px-4">ML Score</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {loading ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    <RefreshCw className="w-6 h-6 animate-spin mx-auto text-cyan-400 mb-2" />
                    Loading transaction ledger...
                  </td>
                </tr>
              ) : error ? (
                <tr>
                  <td colSpan={8} className="py-8 text-center text-rose-400">
                    {error}
                  </td>
                </tr>
              ) : transactions.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-400">
                    No transactions match the selected criteria.
                  </td>
                </tr>
              ) : (
                transactions.map((tx) => {
                  const isFraud = tx.prediction === 1 || tx.prediction === '1'
                  const isHigh = tx.risk_level === 'HIGH'
                  const isMed = tx.risk_level === 'MEDIUM'

                  return (
                    <tr
                      key={tx.id || tx.transaction_id}
                      className="hover:bg-slate-800/40 transition group cursor-pointer"
                      onClick={() => handleOpenDetail(tx.transaction_id)}
                    >
                      <td className="py-3 px-4 font-bold text-cyan-400">
                        {tx.transaction_id}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {tx.customer_id}
                      </td>
                      <td className="py-3 px-4 text-white font-sans">
                        <div className="font-medium text-xs text-slate-200">
                          {tx.merchant_name || tx.merchant_category || 'Commercial Retail'}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono">
                          {tx.merchant_id || tx.merchant_category}
                        </div>
                      </td>
                      <td className="py-3 px-4 font-bold text-white font-mono">
                        {formatINR(tx.amount)}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            isHigh
                              ? 'bg-rose-950 text-rose-300 border border-rose-800'
                              : isMed
                              ? 'bg-amber-950 text-amber-300 border border-amber-800'
                              : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          }`}
                        >
                          {tx.risk_level || 'LOW'}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`font-bold ${isHigh ? 'text-rose-400' : isMed ? 'text-amber-400' : 'text-emerald-400'}`}>
                          {tx.risk_score} / 100
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                            isFraud
                              ? 'bg-rose-950 text-rose-400 border border-rose-900'
                              : 'bg-emerald-950 text-emerald-400 border border-emerald-900'
                          }`}
                        >
                          {isFraud ? 'BLOCKED' : 'APPROVED'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-right" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-end gap-1.5">
                          <button
                            onClick={() => handleOpenDetail(tx.transaction_id)}
                            className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition"
                            title="Inspect Details"
                          >
                            <Eye className="w-3.5 h-3.5" />
                          </button>
                          {onViewExplanation && (
                            <button
                              onClick={() => onViewExplanation(tx.transaction_id)}
                              className="p-1.5 rounded-lg bg-purple-950/70 hover:bg-purple-900 border border-purple-800/80 text-purple-300 hover:text-white transition"
                              title="Explain With SHAP"
                            >
                              <Sparkles className="w-3.5 h-3.5" />
                            </button>
                          )}
                          {!isAdmin ? null : (
                            <button
                              onClick={() => handleCreateCase(tx.transaction_id)}
                              className="p-1.5 rounded-lg bg-rose-950/70 hover:bg-rose-900 border border-rose-800/80 text-rose-300 hover:text-white transition"
                              title="Open Forensic Case"
                            >
                              <ShieldAlert className="w-3.5 h-3.5" />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  )
                })
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="p-4 bg-slate-950/80 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing <strong className="text-white">{transactions.length}</strong> of{' '}
            <strong className="text-white">{total.toLocaleString()}</strong> records
          </div>

          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="font-mono text-xs text-slate-300">
              Page {page} of {totalPages}
            </span>
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

      {/* Transaction Details Modal */}
      {selectedTx && (
        <GlobalCenterModal
          isOpen={Boolean(selectedTx)}
          onClose={() => setSelectedTx(null)}
          title={`Transaction ${selectedTx.transaction_id}`}
          subtitle={`Customer ID: ${selectedTx.customer_id} • Merchant: ${selectedTx.merchant_name || selectedTx.merchant_category || 'Commercial Retail'}`}
          badge={selectedTx.risk_level || 'ANALYZED'}
          badgeType={
            selectedTx.risk_level === 'HIGH'
              ? 'danger'
              : selectedTx.risk_level === 'MEDIUM'
              ? 'warning'
              : 'success'
          }
          icon={CreditCard}
          maxWidth="max-w-2xl"
        >
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Transaction ID</span>
                <span className="font-mono font-bold text-cyan-400">{selectedTx.transaction_id}</span>
              </div>
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Customer Profile</span>
                <span className="font-mono font-bold text-slate-200">{selectedTx.customer_id}</span>
              </div>
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Amount</span>
                <span className="font-mono font-bold text-white text-sm">{formatINR(selectedTx.amount)}</span>
              </div>
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Merchant Category</span>
                <span className="capitalize text-slate-200">{selectedTx.merchant_category || 'N/A'}</span>
              </div>
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
                <span className="text-[10px] text-slate-400 uppercase font-mono block">Country &amp; Device</span>
                <span className="text-slate-200">{selectedTx.transaction_country || 'US'} • {selectedTx.device_type || 'Unknown'}</span>
              </div>
              <div className="p-3 bg-slate-950/80 border border-slate-800 rounded-xl">
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

            <div className="flex justify-end gap-2 pt-2 border-t border-slate-800">
              {onViewExplanation && (
                <button
                  onClick={() => {
                    const txId = selectedTx.transaction_id
                    setSelectedTx(null)
                    onViewExplanation(txId)
                  }}
                  className="px-3.5 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white text-xs font-semibold flex items-center gap-1.5 transition active:scale-95"
                >
                  <Sparkles className="w-3.5 h-3.5" /> View TreeSHAP Explanation &rarr;
                </button>
              )}
            </div>
          </div>
        </GlobalCenterModal>
      )}

    </div>
  )
}
