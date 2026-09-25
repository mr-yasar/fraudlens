import React, { useState, useRef, useEffect, useMemo } from 'react'
import {
  Store,
  Search,
  ChevronDown,
  Check,
  X,
  AlertTriangle,
  MapPin,
} from 'lucide-react'
import { formatINR } from '../../utils/formatters'
import CANONICAL_MASTER_MERCHANTS from '../../data/canonicalMerchants'

/**
 * SearchableMerchantSelect
 * Simple, friendly, and comprehensive merchant selector.
 * - ALL 29-30 merchants are visible and scrollable by default when opened
 * - Instant filtering when user types 1 or 2 letters
 * - Category filter chips for quick 1-click filtering
 * - Wide roomy custom scrollbar with zero white space
 */
export default function SearchableMerchantSelect({
  merchants = [],
  value = '',
  onChange = () => {},
  placeholder = 'Search merchant name, category, or city...',
  label = 'Target Merchant',
  id = 'merchant-select',
}) {
  const [isOpen, setIsOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState('All')
  const containerRef = useRef(null)
  const searchInputRef = useRef(null)

  // Use provided merchants or fall back to canonical master merchants list
  const availableMerchants = useMemo(() => {
    if (Array.isArray(merchants) && merchants.length > 0) {
      return merchants
    }
    return CANONICAL_MASTER_MERCHANTS || []
  }, [merchants])

  // Find currently selected merchant
  const selectedMerchant = useMemo(() => {
    return availableMerchants.find(
      (m) => m.merchant_id === value || m.merchant_name?.toLowerCase() === value?.toLowerCase()
    )
  }, [availableMerchants, value])

  // Extract unique categories for quick-filter chips
  const categories = useMemo(() => {
    const set = new Set()
    availableMerchants.forEach((m) => {
      if (m.category) set.add(m.category)
    })
    return ['All', ...Array.from(set)]
  }, [availableMerchants])

  // Filter merchants: ALL merchants visible when searchQuery is empty!
  const filteredMerchants = useMemo(() => {
    let list = availableMerchants

    // Filter by category if not 'All'
    if (selectedCategory && selectedCategory !== 'All') {
      list = list.filter((m) => m.category?.toLowerCase() === selectedCategory.toLowerCase())
    }

    // Filter by search query (instant 1-2 letters match)
    const q = searchQuery.trim().toLowerCase()
    if (!q) return list

    return list.filter((m) => {
      const matchName = m.merchant_name?.toLowerCase().includes(q)
      const matchId = m.merchant_id?.toLowerCase().includes(q)
      const matchCategory = m.category?.toLowerCase().includes(q)
      const matchCity = m.city?.toLowerCase().includes(q)
      return matchName || matchId || matchCategory || matchCity
    })
  }, [merchants, searchQuery, selectedCategory])

  // When dropdown opens, focus search input and reset query so all merchants are visible
  useEffect(() => {
    if (isOpen) {
      setSearchQuery('')
      setSelectedCategory('All')
      setTimeout(() => {
        if (searchInputRef.current) searchInputRef.current.focus()
      }, 50)
    }
  }, [isOpen])

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (merchant) => {
    onChange(merchant.merchant_id, merchant)
    setIsOpen(false)
  }

  const handleClear = (e) => {
    e.stopPropagation()
    onChange('', null)
  }

  return (
    <div className="relative w-full" ref={containerRef}>
      {label && (
        <div className="flex items-center justify-between mb-1.5">
          <label htmlFor={id} className="text-xs font-mono text-slate-300 font-medium">
            {label}
          </label>
          <span className="text-[10px] text-cyan-400 font-mono">
            {availableMerchants.length} Master Merchants Available
          </span>
        </div>
      )}

      {/* Trigger Button: Shows selected merchant or prompt */}
      <button
        id={id}
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full text-left bg-slate-950 border rounded-xl px-3.5 py-2.5 transition flex items-center justify-between gap-2 shadow-inner group ${
          isOpen
            ? 'border-cyan-500 ring-2 ring-cyan-500/20 shadow-[0_0_15px_rgba(6,182,212,0.15)]'
            : 'border-slate-800 hover:border-slate-700 bg-slate-950/80 hover:bg-slate-900/60'
        }`}
      >
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <div className="w-7 h-7 rounded-lg bg-cyan-950/80 border border-cyan-800/60 flex items-center justify-center text-cyan-400 shrink-0">
            <Store className="w-3.5 h-3.5" />
          </div>

          {selectedMerchant ? (
            <div className="min-w-0 flex-1 flex flex-wrap items-center gap-x-2 gap-y-0.5">
              <span className="font-mono text-xs font-bold text-white group-hover:text-cyan-300 transition-colors">
                {selectedMerchant.merchant_name}
              </span>
              <span className="font-mono text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-800 border border-slate-700 text-cyan-400">
                {selectedMerchant.merchant_id}
              </span>
              <span className="text-[11px] text-slate-400">
                • {selectedMerchant.category}
              </span>
              {selectedMerchant.city && (
                <span className="text-[11px] text-slate-500">
                  ({selectedMerchant.city})
                </span>
              )}
            </div>
          ) : (
            <span className="text-xs text-slate-400 font-normal">
              Click to select from all {availableMerchants.length} merchants...
            </span>
          )}
        </div>

        <div className="flex items-center gap-1 shrink-0">
          {selectedMerchant && (
            <span
              onClick={handleClear}
              className="p-1 text-slate-400 hover:text-white rounded hover:bg-slate-800 transition mr-0.5"
              title="Clear selection"
            >
              <X className="w-3.5 h-3.5" />
            </span>
          )}
          <div className={`p-1 text-slate-400 group-hover:text-cyan-400 transition-transform duration-200 ${isOpen ? 'rotate-180 text-cyan-400' : ''}`}>
            <ChevronDown className="w-4 h-4" />
          </div>
        </div>
      </button>

      {/* Selected Merchant Summary Bar (when closed) */}
      {selectedMerchant && !isOpen && (
        <div className="mt-1.5 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800/80 flex items-center justify-between text-[11px] font-mono">
          <div className="flex items-center gap-2 truncate text-slate-300">
            <span className="px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 font-semibold border border-cyan-800 text-[10px]">
              {selectedMerchant.category}
            </span>
            <span className="flex items-center gap-1 text-slate-400">
              <MapPin className="w-3 h-3 text-cyan-400" />
              {selectedMerchant.city}
            </span>
          </div>
          <div className="flex items-center gap-3 shrink-0">
            <span className="text-slate-400 text-[10px]">
              Avg Ticket: <strong className="text-white">{formatINR(selectedMerchant.average_ticket || selectedMerchant.avg_ticket_inr || 0)}</strong>
            </span>
            <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
              (selectedMerchant.historical_fraud_rate || selectedMerchant.historical_fraud_rate_pct || 0) > 15
                ? 'bg-rose-950 text-rose-300 border border-rose-800'
                : 'bg-emerald-950 text-emerald-300 border border-emerald-800'
            }`}>
              {(selectedMerchant.historical_fraud_rate || selectedMerchant.historical_fraud_rate_pct || 0)}% Fraud
            </span>
          </div>
        </div>
      )}

      {/* Friendly Dropdown List: ALL 29 Merchants Visible */}
      {isOpen && (
        <div className="absolute left-0 right-0 z-50 mt-1.5 rounded-2xl bg-slate-950/98 backdrop-blur-xl border border-slate-700/90 shadow-[0_16px_50px_rgba(0,0,0,0.85),0_0_25px_rgba(6,182,212,0.15)] overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150">
          {/* Header & Integrated Search Bar */}
          <div className="p-2.5 bg-slate-900/90 border-b border-slate-800/80 space-y-2">
            <div className="relative">
              <Search className="w-4 h-4 text-cyan-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder={placeholder}
                className="w-full pl-9 pr-8 py-2 bg-slate-950 border border-slate-700/80 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-cyan-500 transition"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery('')}
                  className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white p-0.5"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Quick Category Filter Pills */}
            <div className="flex items-center gap-1.5 overflow-x-auto pb-1 roomy-scrollbar text-[10px]">
              {categories.slice(0, 8).map((cat) => (
                <button
                  key={cat}
                  type="button"
                  onClick={() => setSelectedCategory(cat)}
                  className={`px-2 py-0.5 rounded-md font-mono shrink-0 transition ${
                    selectedCategory === cat
                      ? 'bg-cyan-600 text-white font-bold'
                      : 'bg-slate-800/80 hover:bg-slate-700 text-slate-300'
                  }`}
                >
                  {cat}
                </button>
              ))}
            </div>

            <div className="flex items-center justify-between text-[10px] font-mono text-slate-400 px-1">
              <span>All merchants visible below (scroll to explore)</span>
              <span className="text-cyan-400 font-bold">
                {filteredMerchants.length} of {availableMerchants.length} visible
              </span>
            </div>
          </div>

          {/* List of all 29 merchants with roomy scrollbar */}
          <div className="max-h-72 overflow-y-auto p-1.5 space-y-1 roomy-scrollbar">
            {filteredMerchants.length === 0 ? (
              <div className="p-6 text-center text-xs text-slate-400 space-y-2">
                <Store className="w-8 h-8 text-slate-600 mx-auto" />
                <p className="font-semibold text-slate-300">No merchants match &ldquo;{searchQuery}&rdquo;</p>
                <button
                  type="button"
                  onClick={() => {
                    setSearchQuery('')
                    setSelectedCategory('All')
                  }}
                  className="px-3 py-1 bg-cyan-950 text-cyan-300 border border-cyan-800 rounded-lg text-[11px] hover:bg-cyan-900 transition"
                >
                  Show All {availableMerchants.length} Merchants
                </button>
              </div>
            ) : (
              filteredMerchants.map((m) => {
                const isSelected = selectedMerchant?.merchant_id === m.merchant_id
                const fraudRate = Number(m.historical_fraud_rate || m.historical_fraud_rate_pct || 0)
                const isHighRisk = fraudRate > 15
                const avgAmt = m.average_ticket || m.avg_ticket_inr || 0

                return (
                  <button
                    key={m.merchant_id}
                    type="button"
                    onClick={() => handleSelect(m)}
                    className={`w-full text-left p-2.5 rounded-xl border transition flex items-center justify-between gap-3 group ${
                      isSelected
                        ? 'bg-cyan-950/80 border-cyan-500/80 text-white shadow-md'
                        : 'bg-slate-900/50 hover:bg-slate-900 border-transparent hover:border-slate-700/80 text-slate-300 hover:text-white'
                    }`}
                  >
                    <div className="flex items-center gap-2.5 min-w-0 flex-1">
                      <div
                        className={`w-7 h-7 rounded-lg flex items-center justify-center shrink-0 border ${
                          isHighRisk
                            ? 'bg-rose-950/60 border-rose-800/60 text-rose-400'
                            : 'bg-slate-800 border-slate-700 text-cyan-400'
                        }`}
                      >
                        {isHighRisk ? (
                          <AlertTriangle className="w-3.5 h-3.5" />
                        ) : (
                          <Store className="w-3.5 h-3.5" />
                        )}
                      </div>

                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-white group-hover:text-cyan-300 transition-colors">
                            {m.merchant_name}
                          </span>
                          <span className="font-mono text-[10px] font-bold px-1.5 py-0.2 rounded bg-slate-950 border border-slate-800 text-cyan-400 shrink-0">
                            {m.merchant_id}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5">
                          <span className="text-slate-300">{m.category}</span>
                          {m.city && (
                            <>
                              <span>•</span>
                              <span className="flex items-center gap-0.5 text-slate-400">
                                <MapPin className="w-2.5 h-2.5 text-slate-500" />
                                {m.city}
                              </span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 shrink-0">
                      <div className="text-right font-mono text-[10px]">
                        <div className="text-slate-300 font-semibold">{formatINR(avgAmt)}</div>
                        <div className={`text-[9px] font-bold ${isHighRisk ? 'text-rose-400' : 'text-emerald-400'}`}>
                          {fraudRate.toFixed(1)}% fraud
                        </div>
                      </div>
                      {isSelected ? (
                        <div className="w-5 h-5 rounded-full bg-cyan-500 flex items-center justify-center text-slate-950 shrink-0">
                          <Check className="w-3 h-3 stroke-[3]" />
                        </div>
                      ) : (
                        <div className="w-5 h-5 rounded-full border border-slate-700 group-hover:border-cyan-500/50 shrink-0" />
                      )}
                    </div>
                  </button>
                )
              })
            )}
          </div>
        </div>
      )}
    </div>
  )
}
