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

  const cleanCount = merchants.filter((m) => {
    const num = parseInt(m.merchant_id.replace(/\D/g, ''), 10)
    return num <= 20
  }).length

  const fraudCount = merchants.filter((m) => {
    const num = parseInt(m.merchant_id.replace(/\D/g, ''), 10)
    return num > 20
  }).length

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="relative overflow-hidden rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-cyan-950/70 border border-slate-800 p-6 shadow-xl">
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
              10 Supermarkets, 5 Tamil Local Businesses, 5 Major Marts (DMart, JioMart), 5 Betting/Rummy Apps (1xBet, RummyCircle), and 5 Shadow Portals.
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

      {/* Quick Group Selector Tabs */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setSelectedGroup('ALL')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold font-mono transition border ${
            selectedGroup === 'ALL'
              ? 'bg-cyan-950 border-cyan-600 text-cyan-300 shadow-md'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
          }`}
        >
          All 30 Merchants
        </button>

        <button
          onClick={() => setSelectedGroup('SUPERMARKET')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition border flex items-center gap-1.5 ${
            selectedGroup === 'SUPERMARKET'
              ? 'bg-emerald-950 border-emerald-600 text-emerald-300 shadow-md'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-emerald-300'
          }`}
        >
          <ShoppingBag className="w-3.5 h-3.5" />
          10 Supermarkets (Clean)
        </button>

        <button
          onClick={() => setSelectedGroup('TAMIL_LOCAL')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition border flex items-center gap-1.5 ${
            selectedGroup === 'TAMIL_LOCAL'
              ? 'bg-emerald-950 border-emerald-600 text-emerald-300 shadow-md'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-emerald-300'
          }`}
        >
          <Store className="w-3.5 h-3.5" />
          5 Tamil Businesses (Clean)
        </button>

        <button
          onClick={() => setSelectedGroup('MAJOR_MART')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition border flex items-center gap-1.5 ${
            selectedGroup === 'MAJOR_MART'
              ? 'bg-emerald-950 border-emerald-600 text-emerald-300 shadow-md'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-emerald-300'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          5 DMart / JioMart / Retail (Clean)
        </button>

        <button
          onClick={() => setSelectedGroup('BETTING_RUMMY')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition border flex items-center gap-1.5 ${
            selectedGroup === 'BETTING_RUMMY'
              ? 'bg-rose-950 border-rose-600 text-rose-300 shadow-md'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-rose-300'
          }`}
        >
          <Gamepad2 className="w-3.5 h-3.5" />
          5 Betting / Rummy Apps (High Risk)
        </button>

        <button
          onClick={() => setSelectedGroup('SHADOW_CRYPTO')}
          className={`px-3.5 py-2 rounded-xl text-xs font-bold transition border flex items-center gap-1.5 ${
            selectedGroup === 'SHADOW_CRYPTO'
              ? 'bg-rose-950 border-rose-600 text-rose-300 shadow-md'
              : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-rose-300'
          }`}
        >
          <Flame className="w-3.5 h-3.5" />
          5 Shadow &amp; Predatory Desks (High Risk)
        </button>
      </div>

      {/* Filter Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-slate-900/80 p-4 rounded-xl border border-slate-800 backdrop-blur-md">
        <div className="relative md:col-span-2">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search merchant by name, M-ID, or category..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
          />
        </div>

        <div>
          <select
            value={selectedCity}
            onChange={(e) => setSelectedCity(e.target.value)}
            className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-xs text-slate-200 focus:outline-none focus:border-cyan-500"
          >
            {cities.map((city) => (
              <option key={city} value={city}>
                {city === 'ALL' ? 'All Cities' : city}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Main Grid & Detail Drawer Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Merchant Cards Grid */}
        <div className={`space-y-4 ${activeMerchant ? 'lg:col-span-2' : 'lg:col-span-3'}`}>
          {loading ? (
            <div className="flex flex-col items-center justify-center p-12 bg-slate-900/40 rounded-2xl border border-slate-800">
              <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin mb-3" />
              <div className="text-sm font-semibold text-slate-300">Loading 30 Merchant Profiles...</div>
            </div>
          ) : error ? (
            <div className="p-6 bg-rose-950/40 border border-rose-800 rounded-2xl text-rose-300 text-sm">
              {error}
            </div>
          ) : filteredMerchants.length === 0 ? (
            <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-800 text-slate-400 text-sm">
              No merchants match the selected filters.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredMerchants.map((m) => {
                const isSelected = activeMerchant?.merchant_id === m.merchant_id
                const idNum = parseInt(m.merchant_id.replace(/\D/g, ''), 10)
                const isHighRisk = idNum > 20
                const fraudRate = m.live_telemetry?.calculated_fraud_rate_pct || 0

                return (
                  <div
                    key={m.merchant_id}
                    onClick={() => setActiveMerchant(m)}
                    className={`cursor-pointer rounded-xl p-5 border transition-all duration-200 relative overflow-hidden group ${
                      isSelected
                        ? 'bg-slate-900/90 border-cyan-500 ring-1 ring-cyan-500/50 shadow-lg shadow-cyan-950/50'
                        : isHighRisk
                        ? 'bg-rose-950/20 hover:bg-rose-950/40 border-rose-900/40 hover:border-rose-700'
                        : 'bg-slate-900/50 hover:bg-slate-900/80 border-slate-800 hover:border-slate-700 shadow-md'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2 mb-3">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                            {m.merchant_id}
                          </span>
                          <span className="text-[11px] text-slate-400 font-medium">
                            {m.category}
                          </span>
                        </div>
                        <h3 className="text-base font-bold text-white mt-1 group-hover:text-cyan-300 transition">
                          {m.merchant_name}
                        </h3>
                      </div>
                      <span
                        className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border shrink-0 ${
                          isHighRisk
                            ? 'bg-rose-950 text-rose-300 border-rose-800 animate-pulse'
                            : 'bg-emerald-950 text-emerald-300 border-emerald-800'
                        }`}
                      >
                        {isHighRisk ? `⚠ ${fraudRate}% Fraud` : '✓ Safe Profile'}
                      </span>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-400 mb-4">
                      <div className="flex items-center gap-1.5">
                        <MapPin className="w-3.5 h-3.5 text-slate-500" />
                        <span>{m.area ? `${m.area}, ` : ''}{m.city}, {m.state}</span>
                      </div>
                      <div className="flex items-center gap-1.5">
                        <DollarSign className="w-3.5 h-3.5 text-slate-500" />
                        <span>Avg Ticket: <strong className="text-slate-200 font-mono">{formatINR(m.average_ticket)}</strong></span>
                      </div>
                    </div>

                    {/* Historical Pattern Highlight */}
                    <div className={`p-2.5 rounded-lg border text-[11px] ${
                      isHighRisk
                        ? 'bg-rose-950/40 border-rose-900/60 text-rose-200'
                        : 'bg-slate-950/60 border-slate-800/80 text-slate-300'
                    }`}>
                      <div className="text-slate-500 font-mono uppercase text-[9px] mb-0.5">
                        Historical Pattern Context
                      </div>
                      <div className="line-clamp-1">
                        {m.historical_fraud_pattern || 'Routine commercial retail'}
                      </div>
                    </div>

                    <div className="mt-4 pt-3 border-t border-slate-800/80 flex items-center justify-between text-xs font-mono text-slate-400">
                      <div>
                        Observed Txs: <strong className="text-white">{m.live_telemetry?.total_transactions || 0}</strong>
                      </div>
                      <div className="flex items-center gap-1 text-cyan-400 font-medium group-hover:translate-x-0.5 transition-transform">
                        Deep Dive <ChevronRight className="w-3.5 h-3.5" />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Deep Dive Profile Detail Drawer */}
        {activeMerchant && (
          <div className="bg-slate-900 rounded-2xl border border-cyan-800/60 p-6 shadow-2xl relative space-y-6 h-fit sticky top-4">
            <div className="flex items-start justify-between border-b border-slate-800 pb-4">
              <div>
                <div className="flex items-center gap-2 mb-1">
                  <span className="font-mono text-xs font-bold text-cyan-400 bg-cyan-950 px-2 py-0.5 rounded border border-cyan-800">
                    {activeMerchant.merchant_id}
                  </span>
                  <span className="text-xs text-slate-400">{activeMerchant.category}</span>
                </div>
                <h2 className="text-lg font-black text-white">{activeMerchant.merchant_name}</h2>
              </div>
              <button
                onClick={() => setActiveMerchant(null)}
                className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 text-xs"
              >
                ✕ Close
              </button>
            </div>

            {loadingDetail ? (
              <div className="flex flex-col items-center justify-center py-12">
                <RefreshCw className="w-6 h-6 text-cyan-400 animate-spin mb-2" />
                <div className="text-xs text-slate-400">Fetching live risk telemetry...</div>
              </div>
            ) : merchantDetail ? (
              <div className="space-y-5 text-xs">
                {/* Historical Pattern Analysis */}
                <div className={`border rounded-xl p-4 ${
                  parseInt(activeMerchant.merchant_id.replace(/\D/g, ''), 10) > 20
                    ? 'bg-rose-950/40 border-rose-800/80 text-rose-200'
                    : 'bg-emerald-950/30 border-emerald-800/60 text-emerald-200'
                }`}>
                  <div className="flex items-center gap-2 font-bold mb-1.5">
                    <ShieldAlert className="w-4 h-4" />
                    Synthetic Historical Fraud Profile
                  </div>
                  <p className="text-slate-300 text-[11px] leading-relaxed">
                    {merchantDetail.merchant.historical_fraud_summary || 'No historical fraud anomaly recorded.'}
                  </p>
                  <div className="mt-3 grid grid-cols-2 gap-2 text-[11px] font-mono">
                    <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                      <span className="text-slate-500 block">Hist. Fraud Rate</span>
                      <strong className="text-amber-400">{merchantDetail.merchant.historical_fraud_rate}%</strong>
                    </div>
                    <div className="bg-slate-950/60 p-2 rounded border border-slate-800">
                      <span className="text-slate-500 block">Hist. Incidents</span>
                      <strong className="text-slate-200">{merchantDetail.merchant.historical_fraud_count} cases</strong>
                    </div>
                  </div>
                </div>

                {/* Live Telemetry Stats */}
                <div>
                  <div className="text-slate-400 font-bold mb-2 uppercase text-[10px] tracking-wider">
                    Live Database Telemetry
                  </div>
                  <div className="grid grid-cols-3 gap-2 text-center font-mono">
                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-slate-500 text-[10px]">Total Txs</div>
                      <div className="text-sm font-bold text-white">{merchantDetail.telemetry.total_transactions}</div>
                    </div>
                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-slate-500 text-[10px]">High Risk</div>
                      <div className="text-sm font-bold text-rose-400">{merchantDetail.telemetry.high_risk_transactions}</div>
                    </div>
                    <div className="bg-slate-950 p-2.5 rounded-lg border border-slate-800">
                      <div className="text-slate-500 text-[10px]">Fraud Flagged</div>
                      <div className="text-sm font-bold text-rose-500">{merchantDetail.telemetry.fraud_transactions}</div>
                    </div>
                  </div>
                </div>

                {/* Common Scenarios */}
                {merchantDetail.telemetry.common_fraud_scenarios?.length > 0 && (
                  <div>
                    <div className="text-slate-400 font-bold mb-2 uppercase text-[10px] tracking-wider">
                      Observed Fraud Scenarios
                    </div>
                    <div className="space-y-1.5">
                      {merchantDetail.telemetry.common_fraud_scenarios.map((sc, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between p-2 rounded bg-slate-950/60 border border-slate-800 text-[11px]"
                        >
                          <span className="text-slate-300">{sc.scenario}</span>
                          <span className="font-mono text-cyan-400 font-bold">{sc.count} txs</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Operational Details */}
                <div>
                  <div className="text-slate-400 font-bold mb-2 uppercase text-[10px] tracking-wider">
                    Operational Context
                  </div>
                  <div className="space-y-1 bg-slate-950 p-3 rounded-lg border border-slate-800 text-[11px]">
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-500">Business Age</span>
                      <span className="text-slate-200 font-mono">{merchantDetail.merchant.business_age} years</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-500">Operating Hours</span>
                      <span className="text-slate-200 font-mono">{merchantDetail.merchant.operating_hours}</span>
                    </div>
                    <div className="flex justify-between py-1 border-b border-slate-800/60">
                      <span className="text-slate-500">Payment Channels</span>
                      <span className="text-slate-200 font-mono">{merchantDetail.merchant.payment_channel}</span>
                    </div>
                    <div className="flex justify-between py-1">
                      <span className="text-slate-500">Pincode / Location</span>
                      <span className="text-slate-200">{merchantDetail.merchant.pincode} ({merchantDetail.merchant.city})</span>
                    </div>
                  </div>
                </div>

                {/* Recent Transactions List */}
                <div>
                  <div className="text-slate-400 font-bold mb-2 uppercase text-[10px] tracking-wider">
                    Recent Transactions
                  </div>
                  <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                    {merchantDetail.recent_transactions?.map((tx) => (
                      <div
                        key={tx.transaction_id}
                        className="flex items-center justify-between p-2 rounded bg-slate-950 border border-slate-800 text-[11px]"
                      >
                        <div>
                          <div className="font-mono text-slate-300 font-bold">{formatINR(tx.amount)}</div>
                          <div className="text-[10px] text-slate-500 font-mono">{tx.transaction_id}</div>
                        </div>
                        <div className="text-right font-mono">
                          <span
                            className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
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
                    ))}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        )}
      </div>
    </div>
  )
}
