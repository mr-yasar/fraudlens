import React, { useState } from 'react'
import {
  Globe,
  Activity,
  Layers,
  ShieldAlert,
  ShieldCheck,
  Lock,
  FileText,
  UserCheck,
  CreditCard,
  MapPin,
  ExternalLink,
  Smartphone,
  Network,
  Share2,
  CheckCircle,
} from 'lucide-react'

/**
 * EvidenceDashboard — Forensic Evidence & Live Telemetry Panel (Right Panel).
 *
 * Exact Visual Alignment with Reference Video (gemini_generated_video_2ce150b8.mp4):
 * - Target Account #8812
 * - Interactive World Map with LATAM Geo-trajectory
 * - Transactional Clusters bar chart
 * - Connected Accounts Network Graph (Account 1, Account 2, Account 3, Account 4, Account 5)
 * - Immediate Action Triggers (Draft SAR, Step-Up OTP, Block Account, Escalate)
 * - Dual Light (Video Default) & Dark Theme Support
 */
export default function EvidenceDashboard({
  activeCase,
  selectedTxn,
  onAction,
  className = '',
  theme = 'light', // 'light' (video match) | 'dark'
}) {
  const isLight = theme === 'light'
  const [activeTab, setActiveTab] = useState('geo') // 'geo' | 'velocity' | 'shap' | 'network'

  // Default fallback data matching reference video
  const accountId = activeCase?.account_label || activeCase?.account_id || selectedTxn?.customer_id || 'Account #8812'
  const txnId = selectedTxn?.transaction_id || activeCase?.transaction_id || 'TXN-8812-BURST'
  const amount = selectedTxn?.amount || activeCase?.amount || 84200
  const riskScore = selectedTxn?.risk_score || activeCase?.risk_score || 94
  const fraudProb = selectedTxn?.fraud_probability || activeCase?.fraud_prob || 89.4

  return (
    <div
      className={`flex flex-col h-full border-l text-xs font-mono overflow-y-auto scrollbar-thin select-none transition-all duration-300 ${
        isLight
          ? 'bg-slate-50/85 backdrop-blur-xl border-slate-200/80 text-slate-800'
          : 'bg-[#070c1e]/95 border-white/10 text-slate-200'
      } ${className}`}
    >
      {/* ── Panel Header ── */}
      <div className={`p-3.5 border-b flex items-center justify-between shrink-0 ${
        isLight ? 'bg-white/80 border-slate-200/80' : 'bg-[#0b142d]/80 border-white/10'
      }`}>
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 border border-cyan-500/20">
            <Activity className="w-4 h-4" />
          </div>
          <div>
            <h3 className={`font-bold text-xs uppercase tracking-wider ${
              isLight ? 'text-slate-900 font-extrabold' : 'text-[#fefae0]'
            }`}>
              Evidence Dashboard
            </h3>
            <span className={`text-[10px] ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
              Forensic Telemetry Feed
            </span>
          </div>
        </div>

        <span className={`px-2.5 py-0.5 rounded-full text-[9px] font-bold border ${
          riskScore >= 70
            ? isLight
              ? 'bg-rose-50 text-rose-700 border-rose-200'
              : 'bg-rose-950/90 text-rose-300 border-rose-500/50'
            : isLight
            ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
            : 'bg-emerald-950/90 text-emerald-300 border-emerald-500/50'
        }`}>
          RISK: {riskScore}/100
        </span>
      </div>

      {/* ── Active Target Account Card (Video Match: Account #8812) ── */}
      <div className={`p-3 border-b shrink-0 ${
        isLight ? 'bg-white/90 border-slate-200/80' : 'bg-[#0b142d]/60 border-white/10'
      }`}>
        <div className="flex items-center justify-between mb-1.5">
          <div className="flex items-center gap-1.5 truncate">
            <CreditCard className="w-3.5 h-3.5 text-cyan-500 shrink-0" />
            <strong className={`truncate text-xs ${isLight ? 'text-slate-900 font-extrabold' : 'text-[#fefae0]'}`}>
              {accountId}
            </strong>
          </div>
          <span className={`text-[9px] px-1.5 py-0.5 rounded-full border shrink-0 font-bold ${
            isLight
              ? 'bg-slate-100 text-slate-700 border-slate-200'
              : 'bg-cyan-950 text-cyan-300 border-cyan-700/60'
          }`}>
            {txnId}
          </span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-[10px]">
          <div>
            <span className={`block text-[9px] ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
              Flagged Amount:
            </span>
            <strong className={`font-black text-sm ${isLight ? 'text-slate-900' : 'text-[#fefae0]'}`}>
              ₹{Number(amount).toLocaleString()}
            </strong>
          </div>
          <div>
            <span className={`block text-[9px] ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
              Posterior Prob:
            </span>
            <strong className="text-rose-600 dark:text-rose-400 font-bold text-sm">
              {fraudProb}%
            </strong>
          </div>
        </div>
      </div>

      {/* ── Navigation Tabs ── */}
      <div className={`px-3 pt-2 flex items-center gap-1 border-b shrink-0 ${
        isLight ? 'bg-slate-100/60 border-slate-200' : 'bg-[#070c1e]/80 border-white/10'
      }`}>
        {[
          { id: 'geo', label: 'Geo-Leap', icon: Globe },
          { id: 'velocity', label: 'Clusters', icon: Activity },
          { id: 'shap', label: 'SHAP', icon: Layers },
          { id: 'network', label: 'Nodes', icon: Network },
        ].map((tab) => {
          const Icon = tab.icon
          const isActive = activeTab === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-2.5 py-1.5 rounded-t-lg text-[10px] font-bold transition flex items-center gap-1 border-b-2 ${
                isActive
                  ? isLight
                    ? 'text-cyan-700 border-cyan-500 bg-white shadow-sm'
                    : 'text-cyan-300 border-cyan-400 bg-slate-900/80'
                  : isLight
                  ? 'text-slate-500 border-transparent hover:text-slate-800'
                  : 'text-slate-400 border-transparent hover:text-slate-200'
              }`}
            >
              <Icon className="w-3 h-3" />
              <span>{tab.label}</span>
            </button>
          )
        })}
      </div>

      {/* ── Tab Content ── */}
      <div className="p-3.5 space-y-4 flex-1">
        {/* TAB 1: GEO-LEAP INTERACTIVE VECTOR MAP (LATAM Video Match) */}
        {activeTab === 'geo' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[10px]">
              <span className={`font-bold flex items-center gap-1 ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                <MapPin className="w-3 h-3 text-rose-500" />
                Impossible Travel Trajectory
              </span>
              <span className="text-rose-600 dark:text-rose-400 font-bold">Δ 8,420 km / 18 mins</span>
            </div>

            <div className={`relative h-44 rounded-2xl border overflow-hidden flex items-center justify-center p-2 shadow-inner ${
              isLight ? 'bg-slate-100 border-slate-200' : 'bg-slate-950 border-cyan-500/30'
            }`}>
              <svg viewBox="0 0 400 200" className="w-full h-full opacity-80">
                {/* Continents */}
                <path d="M 50,40 Q 80,30 110,45 Q 130,70 120,110 Q 90,130 60,110 Z" fill={isLight ? '#cbd5e1' : '#1e293b'} />
                <path d="M 160,35 Q 210,30 250,50 Q 260,90 230,110 Q 180,100 160,70 Z" fill={isLight ? '#cbd5e1' : '#1e293b'} />
                <path d="M 270,50 Q 320,40 360,60 Q 370,110 330,130 Q 280,120 270,80 Z" fill={isLight ? '#cbd5e1' : '#1e293b'} />
                <path d="M 280,110 Q 320,110 340,140 Q 320,170 290,160 Z" fill={isLight ? '#94a3b8' : '#334155'} />

                {/* LATAM Highlight region (From Video) */}
                <rect x="75" y="115" width="45" height="40" rx="6" fill="#06b6d4" fillOpacity="0.25" stroke="#06b6d4" strokeWidth="1" />
                <text x="83" y="138" fill="#0284c7" fontSize="8" fontWeight="bold" fontFamily="monospace">LATAM</text>

                {/* Flight Trajectory Arc */}
                <path d="M 95,125 Q 180,20 280,75" fill="none" stroke="url(#leapGrad)" strokeWidth="2.5" strokeDasharray="4 4" />
                <defs>
                  <linearGradient id="leapGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#06b6d4" />
                    <stop offset="100%" stopColor="#f43f5e" />
                  </linearGradient>
                </defs>

                <circle cx="95" cy="125" r="4" fill="#06b6d4" />
                <circle cx="280" cy="75" r="5" fill="#f43f5e" />
                <text x="245" y="95" fill={isLight ? '#991b1b' : '#fecdd3'} fontSize="8" fontWeight="bold" fontFamily="monospace">
                  Bucharest (VPN)
                </text>
              </svg>

              <div className={`absolute bottom-2 left-2 right-2 p-1.5 rounded-xl border text-[9px] flex items-center justify-between ${
                isLight ? 'bg-white/95 border-slate-200 text-slate-700' : 'bg-slate-950/85 border-slate-800 text-slate-300'
              }`}>
                <span>Origin: <strong>LATAM Node</strong></span>
                <span className="text-rose-600 dark:text-rose-400 font-bold">28,066 km/h Velocity</span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: TRANSACTIONAL CLUSTERS (Video Match: Transactional Charts) */}
        {activeTab === 'velocity' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[10px]">
              <span className={`font-bold ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                Transactional Clusters
              </span>
              <span className="text-cyan-600 dark:text-cyan-400 font-bold">4 txns / 10m Burst</span>
            </div>

            <div className={`h-44 p-3 rounded-2xl border flex flex-col justify-between ${
              isLight ? 'bg-white border-slate-200' : 'bg-slate-950 border-cyan-500/30'
            }`}>
              <div className="flex items-end justify-between h-28 gap-2 px-1 pt-2">
                {[
                  { hour: '11:00', count: 0, height: '8%' },
                  { hour: '12:00', count: 1, height: '24%' },
                  { hour: '13:00', count: 1, height: '24%' },
                  { hour: '14:00', count: 4, height: '95%', highlight: true },
                  { hour: '15:00', count: 0, height: '8%' },
                ].map((col, idx) => (
                  <div key={idx} className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end">
                    <span className={`text-[9px] font-bold ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                      {col.count}
                    </span>
                    <div
                      className={`w-full rounded-t-md transition-all duration-500 ${
                        col.highlight
                          ? 'bg-gradient-to-t from-cyan-600 to-emerald-500'
                          : isLight
                          ? 'bg-slate-200'
                          : 'bg-slate-800'
                      }`}
                      style={{ height: col.height }}
                    />
                    <span className={`text-[8px] font-mono ${isLight ? 'text-slate-400' : 'text-slate-500'}`}>
                      {col.hour}
                    </span>
                  </div>
                ))}
              </div>

              <div className={`pt-2 border-t flex items-center justify-between text-[9px] ${
                isLight ? 'border-slate-100 text-slate-500' : 'border-slate-800 text-slate-400'
              }`}>
                <span>Normal Threshold: <strong>≤2 / hr</strong></span>
                <span className="text-rose-600 dark:text-rose-400 font-bold">+300% Spike Detected</span>
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: TREESHAP FEATURE ATTRIBUTION */}
        {activeTab === 'shap' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[10px]">
              <span className={`font-bold ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                TreeSHAP Feature Drivers
              </span>
              <span className="text-cyan-600 dark:text-cyan-400 font-bold">Base: 0.12 → 0.94</span>
            </div>

            <div className={`space-y-2 p-3 rounded-2xl border ${
              isLight ? 'bg-white border-slate-200' : 'bg-slate-950 border-cyan-500/30'
            }`}>
              {[
                { factor: 'distance_from_home', impact: '+0.44', width: '88%', pos: true },
                { factor: 'amt_deviation', impact: '+0.39', width: '78%', pos: true },
                { factor: 'trans_velocity_1h', impact: '+0.22', width: '44%', pos: true },
                { factor: 'device_trust_score', impact: '-0.21', width: '42%', pos: false },
              ].map((item, idx) => (
                <div key={idx} className="space-y-1">
                  <div className="flex justify-between text-[10px]">
                    <span className={`truncate max-w-[170px] ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                      {item.factor}
                    </span>
                    <span className={item.pos ? 'text-rose-600 dark:text-rose-400 font-bold' : 'text-emerald-600 dark:text-emerald-400 font-bold'}>
                      {item.impact}
                    </span>
                  </div>
                  <div className={`h-1.5 w-full rounded-full overflow-hidden ${isLight ? 'bg-slate-100' : 'bg-slate-800'}`}>
                    <div
                      className={`h-full rounded-full ${
                        item.pos ? 'bg-gradient-to-r from-amber-500 to-rose-500' : 'bg-emerald-500'
                      }`}
                      style={{ width: item.width }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 4: CONNECTED ACCOUNTS NETWORK GRAPH (Reference Video Match: Account 1, 2, 3, 4, 5) */}
        {activeTab === 'network' && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-[10px]">
              <span className={`font-bold ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                Correlated Account Cluster
              </span>
              <span className="text-amber-600 dark:text-amber-400 font-bold">5 Linked Nodes</span>
            </div>

            <div className={`h-48 p-3 rounded-2xl border relative flex items-center justify-center overflow-hidden ${
              isLight ? 'bg-white border-slate-200' : 'bg-slate-950 border-cyan-500/30'
            }`}>
              <svg viewBox="0 0 240 160" className="w-full h-full">
                {/* Connecting Links */}
                <line x1="120" y1="80" x2="50" y2="40" stroke="#06b6d4" strokeWidth="1.5" strokeDasharray="3 3" />
                <line x1="120" y1="80" x2="190" y2="40" stroke="#f43f5e" strokeWidth="2" />
                <line x1="120" y1="80" x2="50" y2="120" stroke="#06b6d4" strokeWidth="1.5" />
                <line x1="120" y1="80" x2="190" y2="120" stroke="#f59e0b" strokeWidth="1.5" />
                <line x1="120" y1="80" x2="120" y2="25" stroke="#3b82f6" strokeWidth="1.5" />

                {/* Central Account #8812 */}
                <circle cx="120" cy="80" r="16" fill={isLight ? '#0284c7' : '#0f172a'} stroke="#38bdf8" strokeWidth="2" />
                <text x="120" y="83" fill="#ffffff" fontSize="7" fontWeight="bold" textAnchor="middle">#8812</text>

                {/* Node: Account 1 */}
                <circle cx="50" cy="40" r="12" fill={isLight ? '#f1f5f9' : '#1e293b'} stroke="#06b6d4" strokeWidth="1.5" />
                <text x="50" y="43" fill={isLight ? '#0f172a' : '#93c5fd'} fontSize="6" textAnchor="middle">Account 1</text>

                {/* Node: Account 2 */}
                <circle cx="190" cy="40" r="13" fill={isLight ? '#ffe4e6' : '#881337'} stroke="#f43f5e" strokeWidth="1.5" />
                <text x="190" y="43" fill={isLight ? '#9f1239' : '#fecdd3'} fontSize="6" fontWeight="bold" textAnchor="middle">Account 2</text>

                {/* Node: Account 3 */}
                <circle cx="120" cy="25" r="11" fill={isLight ? '#f1f5f9' : '#1e293b'} stroke="#3b82f6" strokeWidth="1.5" />
                <text x="120" y="28" fill={isLight ? '#0f172a' : '#93c5fd'} fontSize="6" textAnchor="middle">Account 3</text>

                {/* Node: Account 4 */}
                <circle cx="50" cy="120" r="11" fill={isLight ? '#f1f5f9' : '#1e293b'} stroke="#06b6d4" strokeWidth="1.5" />
                <text x="50" y="123" fill={isLight ? '#0f172a' : '#93c5fd'} fontSize="6" textAnchor="middle">Account 4</text>

                {/* Node: Account 5 */}
                <circle cx="190" cy="120" r="11" fill={isLight ? '#fef3c7' : '#78350f'} stroke="#f59e0b" strokeWidth="1.5" />
                <text x="190" y="123" fill={isLight ? '#92400e' : '#fde68a'} fontSize="6" textAnchor="middle">Account 5</text>
              </svg>

              <div className={`absolute top-2 right-2 text-[8px] px-2 py-0.5 rounded border font-mono ${
                isLight ? 'bg-rose-50 text-rose-700 border-rose-200' : 'bg-rose-950 text-rose-300 border-rose-600'
              }`}>
                Mule Ring Correlation
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Investigator Immediate Actions (Video Match: Bottom action triggers) ── */}
      <div className={`p-3.5 border-t shrink-0 space-y-2 ${
        isLight ? 'bg-white/90 border-slate-200' : 'bg-[#0b142d]/90 border-white/10'
      }`}>
        <div className={`text-[10px] uppercase font-bold tracking-wider ${
          isLight ? 'text-slate-500' : 'text-slate-400'
        }`}>
          INVESTIGATOR ACTIONS:
        </div>

        <div className="grid grid-cols-2 gap-1.5">
          <button
            onClick={() => onAction && onAction('SAR_FILING', accountId)}
            className={`py-2 px-2.5 rounded-xl text-[11px] font-bold transition flex items-center justify-center gap-1.5 shadow-sm border ${
              isLight
                ? 'bg-cyan-50 hover:bg-cyan-100 text-cyan-800 border-cyan-200'
                : 'bg-cyan-950 hover:bg-cyan-900 text-cyan-200 border-cyan-500/40'
            }`}
          >
            <FileText className="w-3.5 h-3.5 text-cyan-500" />
            <span>Draft SAR</span>
          </button>

          <button
            onClick={() => onAction && onAction('STEP_UP_OTP', accountId)}
            className={`py-2 px-2.5 rounded-xl text-[11px] font-bold transition flex items-center justify-center gap-1.5 shadow-sm border ${
              isLight
                ? 'bg-amber-50 hover:bg-amber-100 text-amber-800 border-amber-200'
                : 'bg-amber-950 hover:bg-amber-900 text-amber-200 border-amber-500/40'
            }`}
          >
            <Smartphone className="w-3.5 h-3.5 text-amber-500" />
            <span>Step Up OTP</span>
          </button>

          <button
            onClick={() => onAction && onAction('BLOCK_CARD', accountId)}
            className={`py-2 px-2.5 rounded-xl text-[11px] font-bold transition flex items-center justify-center gap-1.5 shadow-sm border ${
              isLight
                ? 'bg-rose-50 hover:bg-rose-100 text-rose-800 border-rose-200'
                : 'bg-rose-950 hover:bg-rose-900 text-rose-200 border-rose-500/50'
            }`}
          >
            <Lock className="w-3.5 h-3.5 text-rose-500" />
            <span>Block Account</span>
          </button>

          <button
            onClick={() => onAction && onAction('CLEAR_FP', accountId)}
            className={`py-2 px-2.5 rounded-xl text-[11px] font-bold transition flex items-center justify-center gap-1.5 shadow-sm border ${
              isLight
                ? 'bg-slate-100 hover:bg-slate-200 text-slate-700 border-slate-300'
                : 'bg-slate-800 hover:bg-slate-700 text-slate-300 border-slate-600'
            }`}
          >
            <ExternalLink className="w-3.5 h-3.5 text-slate-400" />
            <span>Escalate</span>
          </button>
        </div>
      </div>
    </div>
  )
}
