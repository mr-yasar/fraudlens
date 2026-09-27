import React, { useState, useEffect } from 'react'
import {
  Store,
  Search,
  Filter,
  ShieldAlert,
  TrendingUp,
  MapPin,
  Clock,
  DollarSign,
  AlertTriangle,
  CheckCircle2,
  ExternalLink,
  ChevronRight,
  RefreshCw,
  Building2,
  Activity,
  Layers,
  Sparkles,
  Gamepad2,
  ShoppingBag,
  Flame,
} from 'lucide-react'
import { formatINR } from '../utils/formatters'
import CANONICAL_MASTER_MERCHANTS from '../data/canonicalMerchants'
import GlobalCenterModal from './common/GlobalCenterModal'

export default function MerchantIntelligenceView() {
  const [merchants, setMerchants] = useState(CANONICAL_MASTER_MERCHANTS || [])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [selectedGroup, setSelectedGroup] = useState('ALL')
  const [selectedCity, setSelectedCity] = useState('ALL')
  const [activeMerchant, setActiveMerchant] = useState(null)
  const [merchantDetail, setMerchantDetail] = useState(null)
  const [loadingDetail, setLoadingDetail] = useState(false)

  const getToken = () => localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')

  const fetchMerchants = async () => {
    try {
      setLoading(true)
      setError(null)
      const token = getToken()
      const res = await fetch('/api/v1/merchants', {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error('Failed to load merchant intelligence')
      const data = await res.json()
      if (data.merchants && data.merchants.length > 0) {
        setMerchants(data.merchants)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const fetchMerchantDetail = async (merchantId) => {
    try {
      setLoadingDetail(true)
      const token = getToken()
      const res = await fetch(`/api/v1/merchants/${merchantId}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })
      if (!res.ok) throw new Error('Failed to load merchant details')
      const data = await res.json()
      setMerchantDetail(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingDetail(false)
    }
  }

  useEffect(() => {
    fetchMerchants()
  }, [])

  useEffect(() => {
    if (activeMerchant) {
      fetchMerchantDetail(activeMerchant.merchant_id)
    } else {
      setMerchantDetail(null)
    }
  }, [activeMerchant])

  // Categorize into the 5 requested groups
  const getMerchantGroup = (m) => {
    const idNum = parseInt(m.merchant_id.replace(/\D/g, ''), 10)
    if (idNum >= 1 && idNum <= 10) return 'SUPERMARKET'
    if (idNum >= 11 && idNum <= 15) return 'TAMIL_LOCAL'
    if (idNum >= 16 && idNum <= 20) return 'MAJOR_MART'
    if (idNum >= 21 && idNum <= 25) return 'BETTING_RUMMY'
    return 'SHADOW_CRYPTO'
  }

  const cities = ['ALL', ...new Set(merchants.map((m) => m.city).filter(Boolean))]

  const filteredMerchants = merchants.filter((m) => {
    const matchSearch =
      m.merchant_name.toLowerCase().includes(search.toLowerCase()) ||
      m.merchant_id.toLowerCase().includes(search.toLowerCase()) ||
      m.category.toLowerCase().includes(search.toLowerCase())
    const group = getMerchantGroup(m)
    const matchGroup = selectedGroup === 'ALL' || group === selectedGroup
    const matchCity = selectedCity === 'ALL' || m.city === selectedCity
    return matchSearch && matchGroup && matchCity
  })

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-slate-950 to-cyan-950/70 border border-slate-800 p-6 shadow-2xl">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold bg-cyan-950 text-cyan-400 border border-cyan-800">
                MASTER DIRECTORY • 30 MERCHANTS
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-emerald-950 text-emerald-300 border border-emerald-800">
                20 CLEAN • 10 HIGH-RISK &amp; BETTING
              </span>
            </div>
            <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2">
              <Store className="w-6 h-6 text-cyan-400" />
              Merchant Risk Intelligence &amp; Profiling
            </h1>
            <p className="text-sm text-slate-400 mt-1 max-w-2xl">
              10 Supermarkets, 5 Tamil Local Businesses, 5 Major Marts (DMart, JioMart), 5 Betting/Rummy Apps (1xBet, RummyCircle), and 5 Shadow Portals. Click any merchant card to inspect its full profile in the center of the screen.
            </p>
          </div>
          <button
            onClick={fetchMerchants}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white font-medium text-xs border border-slate-700 transition shadow"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            Refresh Telemetry
          </button>
        </div>
      </div>

      {/* Filter Tabs & Search Bar */}
      <div className="bg-slate-900/80 rounded-2xl border border-slate-800 p-4 space-y-4 shadow-lg backdrop-blur-md">
        <div className="flex flex-wrap items-center justify-between gap-3">
          {/* Category Group Filter Chips */}
          <div className="flex flex-wrap gap-2 text-xs">
            {[
              { id: 'ALL', label: 'All Merchants (30)' },
              { id: 'SUPERMARKET', label: 'Supermarkets (1-10)' },
              { id: 'TAMIL_LOCAL', label: 'Tamil Local (11-15)' },
              { id: 'MAJOR_MART', label: 'Major Marts (16-20)' },
              { id: 'BETTING_RUMMY', label: 'Betting & Rummy (21-25)' },
              { id: 'SHADOW_CRYPTO', label: 'Shadow Portals (26-30)' },
            ].map((grp) => (
              <button
                key={grp.id}
                onClick={() => setSelectedGroup(grp.id)}
                className={`px-3 py-1.5 rounded-xl font-medium transition text-xs ${
                  selectedGroup === grp.id
                    ? 'bg-cyan-600 text-white shadow-md shadow-cyan-900/50'
                    : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800 hover:border-slate-700'
                }`}
              >
                {grp.label}
              </button>
            ))}
          </div>

          {/* City Filter */}
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>City:</span>
            <select
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500"
            >
              {cities.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Search Box */}
        <div className="relative">
          <Search className="w-4 h-4 absolute left-3.5 top-3 text-slate-500" />
          <input
            type="text"
            placeholder="Search by merchant name, ID (e.g. MERCH-021), category or city..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
          />
        </div>
      </div>

      {/* Grid of Merchants */}
      {filteredMerchants.length === 0 ? (
        <div className="p-12 text-center text-xs text-slate-500 bg-slate-900/50 rounded-2xl border border-slate-800">
          No merchants matching the specified filter criteria.
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredMerchants.map((m) => {
            const num = parseInt(m.merchant_id.replace(/\D/g, ''), 10)
            const isHighRisk = num > 20
            const isBetting = num >= 21 && num <= 25
            const isShadow = num >= 26
            const isSelected = activeMerchant?.merchant_id === m.merchant_id

            return (
              <div
                key={m.merchant_id}
                onClick={() => setActiveMerchant(m)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer flex flex-col justify-between group relative overflow-hidden ${
                  isSelected
                    ? 'bg-slate-900 border-cyan-500 ring-2 ring-cyan-500/40 shadow-xl'
                    : isHighRisk
                    ? 'bg-slate-900/70 border-rose-900/40 hover:border-rose-500/70 hover:bg-slate-900'
                    : 'bg-slate-900/70 border-slate-800 hover:border-cyan-500/60 hover:bg-slate-900'
                }`}
              >
                <div>
                  {/* Top Badges */}
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-[11px] font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                      {m.merchant_id}
                    </span>
                    <span
                      className={`text-[10px] font-mono px-2 py-0.5 rounded-full font-bold ${
                        isBetting
                          ? 'bg-rose-950 text-rose-300 border border-rose-800'
                          : isShadow
                          ? 'bg-purple-950 text-purple-300 border border-purple-800'
                          : num <= 10
                          ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                          : 'bg-blue-950 text-blue-300 border border-blue-800'
                      }`}
                    >
                      {isBetting
                        ? 'GAMBLING / HIGH-RISK'
                        : isShadow
                        ? 'SHADOW PORTAL'
                        : num <= 10
                        ? 'SUPERMARKET'
                        : num <= 15
                        ? 'TAMIL LOCAL'
                        : 'MAJOR MART'}
                    </span>
                  </div>

                  {/* Merchant Name */}
                  <h3 className="font-bold text-white text-sm group-hover:text-cyan-300 transition">
                    {m.merchant_name}
                  </h3>
                  <div className="text-xs text-slate-400 mt-0.5">{m.category}</div>

                  {/* Historical Rate Pill */}
                  <div className="mt-3 flex items-center justify-between text-xs bg-slate-950 p-2 rounded-xl border border-slate-800/80 font-mono">
                    <span className="text-slate-500">Hist. Fraud Rate:</span>
                    <span
                      className={`font-bold ${
                        isHighRisk ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {m.historical_fraud_rate}% ({m.historical_fraud_count} cases)
                    </span>
                  </div>
                </div>

                {/* Bottom Footer Info */}
                <div className="mt-4 pt-2.5 border-t border-slate-800 flex items-center justify-between text-[11px] text-slate-500">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-400" />
                    {m.city}
                  </span>
                  <span className="text-cyan-400 flex items-center gap-1 group-hover:translate-x-0.5 transition-transform font-medium">
                    Inspect Modal &rarr;
                  </span>
                </div>
              </div>
            )
          })}
        </div>
      )}

      {/* Viewport-Exact Centered Global Modal for Deep Dive Profile Detail */}
      {activeMerchant && (
        <GlobalCenterModal
          isOpen={Boolean(activeMerchant)}
          onClose={() => setActiveMerchant(null)}
          title={activeMerchant.merchant_name}
          subtitle={`Master Directory ID: ${activeMerchant.merchant_id} • Category: ${activeMerchant.category} • Location: ${activeMerchant.city}`}
          badge={
            parseInt(activeMerchant.merchant_id.replace(/\D/g, ''), 10) > 20
              ? 'HIGH RISK PROFILE'
              : 'CLEAN MERCHANT'
          }
          badgeType={
            parseInt(activeMerchant.merchant_id.replace(/\D/g, ''), 10) > 20
              ? 'danger'
              : 'success'
          }
          icon={Store}
          maxWidth="max-w-3xl"
        >
          {loadingDetail ? (
            <div className="flex flex-col items-center justify-center py-16">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mb-3" />
              <div className="text-sm text-slate-300 font-mono">Fetching live risk telemetry from database...</div>
            </div>
          ) : merchantDetail ? (
            <div className="space-y-5 text-xs">
              {/* Historical Pattern Analysis */}
              <div
                className={`border rounded-2xl p-4.5 ${
                  parseInt(activeMerchant.merchant_id.replace(/\D/g, ''), 10) > 20
                    ? 'bg-rose-950/40 border-rose-800/80 text-rose-200'
                    : 'bg-emerald-950/30 border-emerald-800/60 text-emerald-200'
                }`}
              >
                <div className="flex items-center gap-2 font-bold text-sm mb-2">
                  <ShieldAlert className="w-5 h-5" />
                  Synthetic Historical Fraud Profile &amp; Risk Baseline
                </div>
                <p className="text-slate-300 text-xs leading-relaxed">
                  {merchantDetail.merchant.historical_fraud_summary || 'No historical fraud anomaly recorded.'}
                </p>
                <div className="mt-3 grid grid-cols-2 gap-3 text-xs font-mono">
                  <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Historical Fraud Rate</span>
                    <strong className="text-amber-400 text-base">{merchantDetail.merchant.historical_fraud_rate}%</strong>
                  </div>
                  <div className="bg-slate-950/80 p-3 rounded-xl border border-slate-800">
                    <span className="text-slate-500 block text-[10px] uppercase">Historical Incidents</span>
                    <strong className="text-slate-200 text-base">{merchantDetail.merchant.historical_fraud_count} cases</strong>
                  </div>
                </div>
              </div>

              {/* Live Telemetry Stats */}
              <div>
                <div className="text-slate-400 font-bold mb-2 uppercase text-[11px] tracking-wider font-mono">
                  Live Database Telemetry (Synchronized)
                </div>
                <div className="grid grid-cols-3 gap-3 text-center font-mono">
                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-slate-400 text-[10px] uppercase">Total Transactions</div>
                    <div className="text-lg font-bold text-white mt-0.5">{merchantDetail.telemetry.total_transactions}</div>
                  </div>
                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-slate-400 text-[10px] uppercase">High Risk</div>
                    <div className="text-lg font-bold text-rose-400 mt-0.5">{merchantDetail.telemetry.high_risk_transactions}</div>
                  </div>
                  <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
                    <div className="text-slate-400 text-[10px] uppercase">Fraud Flagged</div>
                    <div className="text-lg font-bold text-rose-500 mt-0.5">{merchantDetail.telemetry.fraud_transactions}</div>
                  </div>
                </div>
              </div>

              {/* Common Scenarios */}
              {merchantDetail.telemetry.common_fraud_scenarios?.length > 0 && (
                <div>
                  <div className="text-slate-400 font-bold mb-2 uppercase text-[11px] tracking-wider font-mono">
                    Observed Fraud Scenarios
                  </div>
                  <div className="space-y-2">
                    {merchantDetail.telemetry.common_fraud_scenarios.map((sc, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950/80 border border-slate-800 text-xs"
                      >
                        <span className="text-slate-300 font-sans">{sc.scenario}</span>
                        <span className="font-mono text-cyan-400 font-bold">{sc.count} txs</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Operational Details */}
              <div>
                <div className="text-slate-400 font-bold mb-2 uppercase text-[11px] tracking-wider font-mono">
                  Operational Context &amp; Channel Profile
                </div>
                <div className="space-y-1.5 bg-slate-950 p-4 rounded-xl border border-slate-800 text-xs">
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Business Age</span>
                    <span className="text-slate-200 font-mono">{merchantDetail.merchant.business_age} years</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Operating Hours</span>
                    <span className="text-slate-200 font-mono">{merchantDetail.merchant.operating_hours}</span>
                  </div>
                  <div className="flex justify-between py-1 border-b border-slate-800/60">
                    <span className="text-slate-400">Payment Channels</span>
                    <span className="text-slate-200 font-mono">{merchantDetail.merchant.payment_channel}</span>
                  </div>
                  <div className="flex justify-between py-1">
                    <span className="text-slate-400">Pincode / Location</span>
                    <span className="text-slate-200">{merchantDetail.merchant.pincode} ({merchantDetail.merchant.city})</span>
                  </div>
                </div>
              </div>

              {/* Recent Transactions List */}
              <div>
                <div className="text-slate-400 font-bold mb-2 uppercase text-[11px] tracking-wider font-mono">
                  Recent Transactions Associated with this Merchant
                </div>
                <div className="space-y-2 max-h-56 overflow-y-auto pr-1">
                  {merchantDetail.recent_transactions?.length === 0 ? (
                    <div className="p-4 text-center text-slate-500 text-xs bg-slate-950 rounded-xl border border-slate-800">
                      No recent transactions recorded for this merchant.
                    </div>
                  ) : (
                    merchantDetail.recent_transactions?.map((tx) => (
                      <div
                        key={tx.transaction_id}
                        className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs"
                      >
                        <div>
                          <div className="font-mono text-slate-200 font-bold">{formatINR(tx.amount)}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{tx.transaction_id}</div>
                        </div>
                        <div className="text-right font-mono">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              tx.risk_level === 'HIGH'
                                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                                : tx.risk_level === 'MEDIUM'
                                ? 'bg-amber-950 text-amber-300 border border-amber-800'
                                : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                            }`}
                          >
                            Score: {tx.risk_score}
                          </span>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          ) : null}
        </GlobalCenterModal>
      )}
    </div>
  )
}
