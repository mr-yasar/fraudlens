import React, { useState } from 'react'
import ModuleInfoExplainer from './ModuleInfoExplainer'

export const CONTEXTUAL_HELP_DATA = {
  analyzer: {
    title: 'Transaction Risk Analyzer',
    badge: 'AI ML INFERENCE',
  },
  dashboard: {
    title: 'Executive Overview',
    badge: 'LIVE TELEMETRY',
  },
  payment: {
    title: 'Payment Gateway',
    badge: 'PRE-AUTH SHIELD',
  },
  'fleet-security': {
    title: 'Fleet & Device Security',
    badge: 'HARDWARE TRUST',
  },
  'live-monitor': {
    title: 'Live Radar & Cases',
    badge: 'GEOSPATIAL RADAR',
  },
}

/**
 * ContextualModuleHelp - In-module trigger button connected directly
 * to the High-Graphics 60 FPS Canvas Explainer Engine.
 */
export default function ContextualModuleHelp({ moduleKey = 'analyzer', className = '' }) {
  const [isOpen, setIsOpen] = useState(false)

  return (
    <div className={`relative inline-flex items-center ${className}`}>
      {/* Contextual Trigger Button with Cyber Neon Glow */}
      <button
        type="button"
        onClick={() => setIsOpen(true)}
        className="p-1.5 rounded-xl bg-slate-900/90 hover:bg-cyan-950/60 text-slate-300 hover:text-cyan-300 border border-slate-700/80 hover:border-cyan-400/80 transition-all duration-300 shadow-md hover:shadow-[0_0_15px_rgba(6,182,212,0.35)] flex items-center gap-1.5 group cursor-pointer active:scale-95"
        title="View high-graphics interactive module guide"
        aria-label="Open high-graphics module information"
      >
        <span className="w-4 h-4 rounded-full bg-cyan-950 border border-cyan-400/80 text-cyan-300 text-[10px] font-mono font-bold flex items-center justify-center group-hover:scale-110 shadow-[0_0_8px_rgba(6,182,212,0.4)] transition-transform">
          i
        </span>
        <span className="text-[11px] font-mono font-bold text-slate-200 group-hover:text-cyan-200 hidden sm:inline tracking-tight">
          Module Info
        </span>
      </button>

      {/* High-Graphics 60 FPS HTML5 Canvas Visual Explainer Modal */}
      <ModuleInfoExplainer
        activeView={moduleKey}
        isOpenExternal={isOpen}
        onOpenChange={setIsOpen}
        showFloatingButton={false}
      />
    </div>
  )
}
