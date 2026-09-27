import React, { useState, useEffect } from 'react'
import {
  Radio,
  ShieldAlert,
  ArrowRight,
  Layers,
  Sparkles,
  Eye,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from 'lucide-react'
import LiveTransactionMonitorView from './LiveTransactionMonitorView'
import InvestigationsView from './InvestigationsView'
import { getCustomerPersona } from '../utils/customerHelper'

/**
 * LiveMonitorAndInvestigationHub
 * Combines Live Transaction Radar (Streaming Real-Time Monitor)
 * and Fraud Investigations (Active Case Management & Evidence Triage)
 * into a single unified, interconnected module accessible to ALL user roles.
 */
export default function LiveMonitorAndInvestigationHub({
  user,
  isAdmin,
  initialTab = 'monitor',
  initialTxId = null,
  onViewExplanation,
}) {
  const [activeTab, setActiveTab] = useState(initialTab === 'investigations' ? 'investigations' : 'monitor')
  const [targetTxId, setTargetTxId] = useState(initialTxId)
  const customerPersona = getCustomerPersona(user)
  const isCustomer = customerPersona.isCustomer

  // Synchronize when initialTab or initialTxId changes from external nav
  useEffect(() => {
    if (initialTab) {
      setActiveTab(initialTab === 'investigations' ? 'investigations' : 'monitor')
    }
  }, [initialTab])

  useEffect(() => {
    if (initialTxId) {
      setTargetTxId(initialTxId)
      setActiveTab('investigations')
    }
  }, [initialTxId])

  // Cross-module interconnection handler: Clicking Investigate on Live Radar opens Case Triage
  const handleLaunchInvestigation = (txId, txObj) => {
    setTargetTxId(txId)
    setActiveTab('investigations')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  const handleSwitchToRadar = () => {
    setActiveTab('monitor')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  return (
    <div className="space-y-6">
      {/* Unified Master Header & Mode Switcher */}
      <div className="rounded-2xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/80 border border-slate-800 p-5 sm:p-6 shadow-2xl relative overflow-hidden">
        {/* Ambient Glow */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-cyan-500/5 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute bottom-0 left-1/3 w-64 h-64 bg-indigo-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-5">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-indigo-950 text-indigo-400 border border-indigo-800 flex items-center gap-1.5">
                <Layers className="w-3 h-3 text-cyan-400" />
                INTERCONNECTED RADAR &amp; CASE ENGINE
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                ACTIVE FOR ALL ROLES
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono bg-cyan-950 text-cyan-300 border border-cyan-800 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
                LIVE STREAMING TELEMETRY
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-white flex items-center gap-3">
              <div className="p-2 rounded-xl bg-gradient-to-tr from-cyan-600 via-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-500/20">
                <Radio className="w-6 h-6" />
              </div>
              <span>Live Monitor &amp; Fraud Investigation Hub</span>
            </h1>

            <p className="text-xs sm:text-sm text-slate-400 max-w-2xl leading-relaxed">
              {isCustomer ? (
                <span>
                  Watching live account telemetry for <strong className="text-emerald-300">{customerPersona.name}</strong> ({customerPersona.customerId}). Monitor real-time transaction streaming and review security investigation alerts.
                </span>
              ) : (
                <span>
                  Real-time transaction radar streaming continuously across 29 merchants. Immediately launch, triage, and resolve fraud investigation cases with evidence-grounded AI intelligence.
                </span>
              )}
            </p>
          </div>

          {/* Interactive Connected Tab Switcher */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-1.5 bg-slate-950/90 rounded-2xl border border-slate-800 shadow-inner">
            <button
              type="button"
              onClick={() => setActiveTab('monitor')}
              className={`flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-mono text-xs font-bold transition-all duration-200 ${
                activeTab === 'monitor'
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-lg shadow-cyan-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <div className="relative">
                <Radio className="w-4 h-4 text-cyan-300" />
                <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
              </div>
              <span>1. Live Transaction Radar (Stream)</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('investigations')}
              className={`flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-mono text-xs font-bold transition-all duration-200 ${
                activeTab === 'investigations'
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-lg shadow-indigo-600/30'
                  : 'text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <ShieldAlert className="w-4 h-4 text-amber-300" />
              <span>2. Active Fraud Investigations &amp; Cases</span>
            </button>
          </div>
        </div>

        {/* Current Active Mode Bar */}
        <div className="mt-4 pt-3 border-t border-slate-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 text-slate-300 font-mono text-[11px]">
            <span className="text-slate-500">Active View:</span>
            {activeTab === 'monitor' ? (
              <span className="flex items-center gap-1.5 text-cyan-300 font-bold">
                <Radio className="w-3.5 h-3.5 text-cyan-400" />
                Real-Time Streaming Transaction Radar (Auto-Refreshing every 4s)
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-indigo-300 font-bold">
                <ShieldAlert className="w-3.5 h-3.5 text-indigo-400" />
                Fraud Investigation Case Management &amp; Evidence Triage
              </span>
            )}
            {targetTxId && (
              <span className="px-2 py-0.5 rounded bg-slate-900 text-emerald-400 border border-emerald-800/80 text-[10px]">
                Target: {targetTxId}
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            {activeTab === 'monitor' ? (
              <button
                type="button"
                onClick={() => setActiveTab('investigations')}
                className="px-3 py-1 rounded-lg bg-indigo-950/80 hover:bg-indigo-900 text-indigo-300 border border-indigo-800 text-[11px] font-mono font-bold transition flex items-center gap-1.5"
                title="Switch to Active Fraud Investigations queue"
              >
                <span>Open Active Case Queue</span>
                <ArrowRight className="w-3 h-3 text-indigo-400" />
              </button>
            ) : (
              <button
                type="button"
                onClick={() => setActiveTab('monitor')}
                className="px-3 py-1 rounded-lg bg-cyan-950/80 hover:bg-cyan-900 text-cyan-300 border border-cyan-800 text-[11px] font-mono font-bold transition flex items-center gap-1.5"
                title="Switch to Live Transaction Radar stream"
              >
                <span>Return to Live Radar Stream</span>
                <ArrowRight className="w-3 h-3 text-cyan-400" />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Render Selected View */}
      {activeTab === 'monitor' ? (
        <LiveTransactionMonitorView
          user={user}
          isAdmin={isAdmin}
          onInvestigate={handleLaunchInvestigation}
        />
      ) : (
        <InvestigationsView
          user={user}
          isAdmin={isAdmin}
          initialTxId={targetTxId}
          onInspectExplanation={onViewExplanation}
          onSwitchToRadar={handleSwitchToRadar}
        />
      )}
    </div>
  )
}
