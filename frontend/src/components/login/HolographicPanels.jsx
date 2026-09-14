import React from 'react'
import {
  Cpu,
  ShieldAlert,
  CreditCard,
  BarChart3,
  Activity,
  Radio,
  CheckCircle2,
  Lock,
} from 'lucide-react'

/**
 * HolographicPanels - High-fidelity floating HUD telemetry panels matching the
 * cinematic reference image: Fraud Detection, Risk Score (92 High Risk),
 * Transaction Monitoring (₹60,000 Risk Detected), SHAP Analysis, and System Status.
 */
export default function HolographicPanels({
  sequenceStage = 'IDLE',
  isConnected = true,
  latency = 45,
}) {
  // Check if system is in handoff phase (collapsing inward toward security core)
  const isHandoff =
    sequenceStage === 'SYSTEM_HANDOFF' ||
    sequenceStage === 'ENERGY_PULSE' ||
    sequenceStage === 'COMMAND_CENTER_OPEN'

  const collapseStyle = isHandoff
    ? 'scale-50 opacity-0 translate-x-12 translate-y-8 blur-sm pointer-events-none transition-all duration-700 ease-in'
    : 'scale-100 opacity-100 transition-all duration-500'

  return (
    <div className="absolute inset-0 pointer-events-none select-none overflow-hidden">
      {/* =========================================================================
          TOP-LEFT BRAND HEADLINE
          ========================================================================= */}
      <div className={`absolute top-20 left-6 lg:left-12 max-w-xs hidden md:block ${collapseStyle}`}>
        <div className="text-[11px] font-mono font-bold tracking-widest text-cyan-400 uppercase">
          AI POWERED
        </div>
        <h2 className="text-xl lg:text-2xl font-black text-white tracking-tight leading-tight">
          FINANCIAL SECURITY COMMAND CENTER
        </h2>
        <p className="text-xs text-slate-400 mt-1 font-sans">
          Smarter detection. Clearer explanations. Safer transactions.
        </p>
      </div>

      {/* =========================================================================
          PANEL 1: FRAUD DETECTION (Top Left of Globe)
          ========================================================================= */}
      <div
        className={`absolute top-44 left-6 lg:left-12 w-52 lg:w-56 p-3 rounded-2xl hologram-glass border border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.25)] hidden md:block ${collapseStyle}`}
      >
        <div className="flex items-center gap-2 pb-1.5 border-b border-cyan-800/40 text-cyan-400 font-mono text-[10px] font-bold uppercase tracking-wider">
          <Cpu className="w-3.5 h-3.5 text-cyan-400" />
          FRAUD DETECTION
        </div>

        <div className="mt-2 text-[11px] font-mono">
          <div className="text-slate-400 text-[10px]">AI Model Active</div>
          <div className="text-white font-bold tracking-wide flex items-center justify-between">
            <span>XGBoost</span>
            <span className="text-[10px] text-emerald-400 font-normal">Active</span>
          </div>
        </div>

        {/* Dynamic Waveform */}
        <div className="mt-2 pt-1.5 border-t border-slate-800/60 flex items-center justify-between h-5 gap-1">
          {[35, 60, 45, 90, 80, 50, 65, 85, 40, 75].map((h, i) => (
            <div
              key={i}
              className="w-full bg-cyan-400 rounded-full"
              style={{
                height: `${h}%`,
                opacity: 0.6 + (i % 3) * 0.15,
                animation: `pulse ${1 + (i % 3) * 0.4}s ease-in-out infinite alternate`,
              }}
            />
          ))}
        </div>
      </div>

      {/* =========================================================================
          PANEL 2: RISK SCORE GAUGE (Top Right of Globe)
          ========================================================================= */}
      <div
        className={`absolute top-28 left-[44%] lg:left-[42%] w-48 p-3 rounded-2xl hologram-glass border border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.25)] hidden lg:block ${collapseStyle}`}
      >
        <div className="flex items-center justify-between pb-1.5 border-b border-cyan-800/40 text-cyan-400 font-mono text-[10px] font-bold uppercase tracking-wider">
          <div className="flex items-center gap-1.5">
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
            RISK SCORE
          </div>
        </div>

        <div className="mt-2 flex items-center gap-3">
          {/* Radial Speedometer Gauge */}
          <div className="relative w-14 h-14 flex items-center justify-center">
            <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
              <path
                className="text-slate-800"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                className="text-rose-500 drop-shadow-[0_0_6px_#f43f5e]"
                strokeDasharray="92, 100"
                strokeWidth="3.5"
                strokeLinecap="round"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute text-sm font-black font-mono text-white">92</span>
          </div>

          <div>
            <div className="text-[10px] font-mono text-slate-400 uppercase">Assessment</div>
            <div className="px-2 py-0.5 rounded bg-rose-950/80 border border-rose-800 text-rose-300 text-[10px] font-bold font-mono uppercase tracking-wider mt-0.5 shadow-[0_0_10px_rgba(244,63,94,0.4)]">
              HIGH RISK
            </div>
          </div>
        </div>
      </div>

      {/* =========================================================================
          PANEL 3: TRANSACTION MONITORING (Right of Globe)
          ========================================================================= */}
      <div
        className={`absolute top-64 left-[46%] lg:left-[45%] w-52 p-3 rounded-2xl hologram-glass border border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.25)] hidden lg:block ${collapseStyle}`}
      >
        <div className="flex items-center gap-1.5 pb-1.5 border-b border-cyan-800/40 text-cyan-400 font-mono text-[10px] font-bold uppercase tracking-wider">
          <CreditCard className="w-3.5 h-3.5 text-cyan-300" />
          TRANSACTION MONITORING
        </div>

        <div className="mt-2">
          <div className="text-[10px] font-mono text-slate-400">Recent Transaction</div>
          <div className="text-base font-extrabold font-mono text-white tracking-tight flex items-center justify-between">
            <span>₹60,000</span>
            <span className="text-[9px] px-1.5 py-0.5 rounded bg-rose-950 border border-rose-700 text-rose-400 font-semibold font-mono">
              • Risk Detected
            </span>
          </div>
        </div>

        {/* Dynamic Frequency Bars */}
        <div className="mt-2 pt-1 border-t border-slate-800/60 flex items-end justify-between h-4 gap-1">
          {[25, 45, 75, 95, 60, 40, 80, 50].map((val, idx) => (
            <div
              key={idx}
              className="w-full rounded bg-cyan-400"
              style={{
                height: `${val}%`,
                animation: `pulse ${0.9 + (idx % 3) * 0.3}s ease-in-out infinite alternate`,
              }}
            />
          ))}
        </div>
      </div>

      {/* =========================================================================
          PANEL 4: SHAP ANALYSIS (Bottom Left of Globe)
          ========================================================================= */}
      <div
        className={`absolute bottom-20 left-6 lg:left-12 w-56 p-3 rounded-2xl hologram-glass border border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.25)] hidden md:block ${collapseStyle}`}
      >
        <div className="flex items-center gap-1.5 pb-1.5 border-b border-cyan-800/40 text-cyan-400 font-mono text-[10px] font-bold uppercase tracking-wider">
          <BarChart3 className="w-3.5 h-3.5 text-cyan-300" />
          SHAP ANALYSIS
        </div>

        <div className="mt-2 flex items-center justify-between gap-2">
          <div className="space-y-1 font-mono text-[9px]">
            <div className="flex items-center gap-1.5 text-cyan-300">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400" />
              Amount
            </div>
            <div className="flex items-center gap-1.5 text-teal-300">
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
              Velocity
            </div>
            <div className="flex items-center gap-1.5 text-purple-300">
              <span className="w-1.5 h-1.5 rounded-full bg-purple-400" />
              Device
            </div>
            <div className="flex items-center gap-1.5 text-pink-300">
              <span className="w-1.5 h-1.5 rounded-full bg-pink-400" />
              Location
            </div>
          </div>

          {/* Bar Chart Visualization */}
          <div className="flex items-end gap-1.5 h-11 w-20 justify-end">
            <div className="w-2.5 h-[85%] bg-cyan-400 rounded-t shadow-[0_0_8px_#22d3ee]" />
            <div className="w-2.5 h-[65%] bg-teal-400 rounded-t shadow-[0_0_8px_#2dd4bf]" />
            <div className="w-2.5 h-[50%] bg-purple-400 rounded-t shadow-[0_0_8px_#c084fc]" />
            <div className="w-2.5 h-[35%] bg-pink-400 rounded-t shadow-[0_0_8px_#f472b6]" />
          </div>
        </div>
      </div>

      {/* =========================================================================
          PANEL 5: SYSTEM STATUS (Bottom Right of Globe)
          ========================================================================= */}
      <div
        className={`absolute bottom-20 left-[44%] lg:left-[43%] w-52 p-3 rounded-2xl hologram-glass border border-cyan-500/40 shadow-[0_0_20px_rgba(6,182,212,0.25)] hidden lg:block ${collapseStyle}`}
      >
        <div className="flex items-center gap-1.5 pb-1.5 border-b border-cyan-800/40 text-cyan-400 font-mono text-[10px] font-bold uppercase tracking-wider">
          <Activity className="w-3.5 h-3.5 text-cyan-300" />
          SYSTEM STATUS
        </div>

        <div className="mt-2 space-y-0.5 font-mono text-[10px]">
          <div className="flex items-center gap-1.5 text-emerald-400 font-bold">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            SYSTEM ONLINE
          </div>
          <div className="text-slate-400 text-[9px] flex items-center gap-1 pl-3">
            <span>• MODEL ACTIVE</span>
          </div>
          <div className="text-slate-400 text-[9px] flex items-center gap-1 pl-3">
            <span>• REAL-TIME MONITORING</span>
          </div>
        </div>

        {/* EKG Heartbeat Trace */}
        <div className="mt-1.5 pt-1 border-t border-slate-800/60 flex items-center justify-center">
          <svg viewBox="0 0 100 20" className="w-full h-4 stroke-cyan-400 fill-none">
            <path
              d="M 0 10 L 25 10 L 30 2 L 35 18 L 40 10 L 60 10 L 65 5 L 70 15 L 75 10 L 100 10"
              strokeWidth="1.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>
      </div>

      {/* =========================================================================
          BOTTOM-LEFT FOOTER STATUS STRIP
          ========================================================================= */}
      <div className="absolute bottom-3 left-6 lg:left-12 hidden sm:flex items-center gap-2 font-mono text-[10px] text-cyan-300">
        <Activity className="w-3.5 h-3.5 text-cyan-400 animate-pulse" />
        <span>ANALYZING TRANSACTIONS... PROTECTING YOUR FINANCIAL FUTURE</span>
      </div>

      {/* =========================================================================
          BOTTOM-RIGHT SECURITY MOTTO
          ========================================================================= */}
      <div className="absolute bottom-3 right-6 lg:right-12 hidden sm:flex items-center gap-1.5 font-mono text-[10px] text-slate-400">
        <CheckCircle2 className="w-3.5 h-3.5 text-cyan-400" />
        <span>YOUR SECURITY / OUR PRIORITY</span>
      </div>
    </div>
  )
}
