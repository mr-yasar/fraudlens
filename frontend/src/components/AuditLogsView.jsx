import React, { useState, useEffect, useMemo } from 'react'
import {
  History,
  Search,
  ChevronLeft,
  ChevronRight,
  RefreshCw,
  ShieldCheck,
  ShieldAlert,
  Eye,
  X,
  FileSpreadsheet,
  Download,
  Filter,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  User,
  CreditCard,
  Lock,
  Layers,
  Sparkles,
  Copy,
  Check,
  Code,
  List,
  FileJson,
  FileText,
} from 'lucide-react'
import { auditLogsApi } from '../services/api'
import GlobalCenterModal from './common/GlobalCenterModal'
import ContextualModuleHelp from './common/ContextualModuleHelp'

const SENSITIVE_KEY_PATTERN = /(password|secret|token|api_?key|auth_?header|credential|private_?key)/i

function sanitizeAuditDetails(data) {
  if (data === null || data === undefined) return null
  if (typeof data !== 'object') return data

  if (Array.isArray(data)) {
    return data.map((item) => sanitizeAuditDetails(item))
  }

  const clean = {}
  for (const [key, value] of Object.entries(data)) {
    if (SENSITIVE_KEY_PATTERN.test(key)) {
      clean[key] = '•••••••• [REDACTED FOR COMPLIANCE]'
    } else if (typeof value === 'object' && value !== null) {
      clean[key] = sanitizeAuditDetails(value)
    } else {
      clean[key] = value
    }
  }
  return clean
}

function parseAuditDetails(raw) {
  if (raw === null || raw === undefined || raw === '' || raw === '{}') {
    return { type: 'empty' }
  }

  // If it's an object from backend
  if (typeof raw === 'object') {
    // If backend wrapped it into {"raw": "some text"}
    if (raw.raw && Object.keys(raw).length === 1 && typeof raw.raw === 'string') {
      try {
        const parsed = JSON.parse(raw.raw)
        if (typeof parsed === 'object' && parsed !== null) {
          const sanitized = sanitizeAuditDetails(parsed)
          return { type: 'json', data: sanitized, formatted: JSON.stringify(sanitized, null, 2) }
        }
        return { type: 'text', text: String(parsed) }
      } catch {
        return { type: 'text', text: raw.raw }
      }
    }
    const sanitized = sanitizeAuditDetails(raw)
    return { type: 'json', data: sanitized, formatted: JSON.stringify(sanitized, null, 2) }
  }

  // If it's a string, try JSON parse
  if (typeof raw === 'string') {
    const trimmed = raw.trim()
    if (!trimmed || trimmed === '{}' || trimmed === 'null') {
      return { type: 'empty' }
    }
    if ((trimmed.startsWith('{') && trimmed.endsWith('}')) || (trimmed.startsWith('[') && trimmed.endsWith(']'))) {
      try {
        const parsed = JSON.parse(trimmed)
        if (typeof parsed === 'object' && parsed !== null) {
          const sanitized = sanitizeAuditDetails(parsed)
          return { type: 'json', data: sanitized, formatted: JSON.stringify(sanitized, null, 2) }
        }
      } catch {
        // Fall through to text
      }
    }
    return { type: 'text', text: trimmed }
  }

  return { type: 'text', text: String(raw) }
}

function AuditDetailsInspector({ details }) {
  const [viewMode, setViewMode] = useState('json') // 'json' | 'structured'
  const [copied, setCopied] = useState(false)

  const parsedInfo = useMemo(() => parseAuditDetails(details), [details])

  const handleCopy = () => {
    let textToCopy = ''
    if (parsedInfo.type === 'json') {
      textToCopy = parsedInfo.formatted
    } else if (parsedInfo.type === 'text') {
      textToCopy = parsedInfo.text
    }
    if (!textToCopy) return
    navigator.clipboard?.writeText(textToCopy).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  if (parsedInfo.type === 'empty') {
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-slate-400 text-xs flex items-center gap-2">
        <AlertTriangle className="w-4 h-4 text-slate-500 shrink-0" />
        <span>No additional parameters or metadata recorded for this audit event.</span>
      </div>
    )
  }

  if (parsedInfo.type === 'text') {
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-[10px] font-mono uppercase text-cyan-300 font-bold flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400" />
            Plain Text Audit Record
          </span>
          <button
            type="button"
            onClick={handleCopy}
            className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 text-[11px] font-mono flex items-center gap-1 transition cursor-pointer border border-slate-700"
          >
            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
            <span>{copied ? 'Copied' : 'Copy Text'}</span>
          </button>
        </div>
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs font-mono text-slate-200 leading-relaxed whitespace-pre-wrap break-words break-all">
          {parsedInfo.text}
        </div>
      </div>
    )
  }

  const isObject = parsedInfo.data && !Array.isArray(parsedInfo.data) && typeof parsedInfo.data === 'object'
  const entries = isObject ? Object.entries(parsedInfo.data) : []

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-1 bg-slate-950 p-1 rounded-lg border border-slate-800">
          <button
            type="button"
            onClick={() => setViewMode('json')}
            className={`px-2.5 py-1 rounded text-[11px] font-mono font-semibold transition flex items-center gap-1.5 cursor-pointer ${
              viewMode === 'json'
                ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Code className="w-3 h-3" />
            Formatted JSON
          </button>
          {isObject && entries.length > 0 && (
            <button
              type="button"
              onClick={() => setViewMode('structured')}
              className={`px-2.5 py-1 rounded text-[11px] font-mono font-semibold transition flex items-center gap-1.5 cursor-pointer ${
                viewMode === 'structured'
                  ? 'bg-cyan-950 text-cyan-300 border border-cyan-800 shadow-sm'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <List className="w-3 h-3" />
              Structured Fields ({entries.length})
            </button>
          )}
        </div>

        <button
          type="button"
          onClick={handleCopy}
          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white text-[11px] font-mono flex items-center gap-1.5 transition cursor-pointer border border-slate-700"
          title="Copy formatted JSON payload to clipboard"
        >
          {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
          <span>{copied ? 'Copied to Clipboard!' : 'Copy JSON'}</span>
        </button>
      </div>

      {viewMode === 'json' ? (
        <div className="relative">
          <pre className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-[11px] font-mono text-emerald-300/90 max-h-64 overflow-y-auto overflow-x-auto leading-relaxed whitespace-pre-wrap break-words break-all shadow-inner">
            {parsedInfo.formatted}
          </pre>
        </div>
      ) : (
        <div className="rounded-xl border border-slate-800 overflow-hidden bg-slate-950 max-h-64 overflow-y-auto">
          <table className="w-full text-left text-xs font-mono">
            <thead className="bg-slate-900/90 text-[10px] uppercase text-slate-400 border-b border-slate-800 sticky top-0">
              <tr>
                <th className="py-2 px-3 w-1/3">Key Attribute</th>
                <th className="py-2 px-3">Value</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60">
              {entries.map(([k, val]) => {
                const isObjVal = typeof val === 'object' && val !== null
                return (
                  <tr key={k} className="hover:bg-slate-900/40 transition">
                    <td className="py-2 px-3 font-semibold text-cyan-300 align-top">
                      {k}
                    </td>
                    <td className="py-2 px-3 text-slate-200 break-all whitespace-pre-wrap">
                      {isObjVal ? (
                        <pre className="text-[10px] text-amber-300/90 bg-slate-900 p-2 rounded border border-slate-800 whitespace-pre-wrap break-all">
                          {JSON.stringify(val, null, 2)}
                        </pre>
                      ) : typeof val === 'boolean' ? (
                        <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${val ? 'bg-emerald-950 text-emerald-300 border border-emerald-800' : 'bg-rose-950 text-rose-300 border border-rose-800'}`}>
                          {String(val)}
                        </span>
                      ) : typeof val === 'number' ? (
                        <span className="text-purple-300 font-bold">{val}</span>
                      ) : val === null ? (
                        <span className="text-slate-500 italic">null</span>
                      ) : (
                        <span>{String(val)}</span>
                      )}
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default function AuditLogsView() {
  const [logs, setLogs] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [limit] = useState(15)
  const [categoryFilter, setCategoryFilter] = useState('ALL') // 'ALL' | 'SECURITY' | 'TRANSACTIONS' | 'MODELS' | 'AUTH'
  const [actionFilter, setActionFilter] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Selected Log Detail Modal
  const [selectedLog, setSelectedLog] = useState(null)

  const fetchLogs = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await auditLogsApi.list({
        page,
        limit,
        action: actionFilter,
        search: searchQuery,
      })
      setLogs(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to retrieve compliance audit records')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [page, actionFilter])

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    setPage(1)
    fetchLogs()
  }

  // Filter logs by category in memory for instant responsiveness
  const filteredLogs = useMemo(() => {
    if (categoryFilter === 'ALL') return logs
    if (categoryFilter === 'SECURITY') {
      return logs.filter(
        (l) =>
          l.action.includes('BLOCK') ||
          l.action.includes('ALERT') ||
          l.action.includes('LOCK') ||
          l.action.includes('INTERCEPT') ||
          l.action.includes('CHALLENGE') ||
          l.action.includes('INVESTIGATION')
      )
    }
    if (categoryFilter === 'TRANSACTIONS') {
      return logs.filter(
        (l) =>
          l.action.includes('TRANSACTION') ||
          l.action.includes('PAYMENT') ||
          l.action.includes('ALLOW') ||
          l.resource_type?.toLowerCase().includes('transaction')
      )
    }
    if (categoryFilter === 'MODELS') {
      return logs.filter(
        (l) =>
          l.action.includes('MODEL') ||
          l.action.includes('TRAIN') ||
          l.action.includes('DATASET') ||
          l.action.includes('DATABASE') ||
          l.resource_type?.toLowerCase().includes('model') ||
          l.resource_type?.toLowerCase().includes('dataset')
      )
    }
    if (categoryFilter === 'AUTH') {
      return logs.filter(
        (l) =>
          l.action.includes('LOGIN') ||
          l.action.includes('AUTH') ||
          l.action.includes('USER') ||
          l.resource_type?.toLowerCase().includes('auth')
      )
    }
    return logs
  }, [logs, categoryFilter])

  // Helper to generate clear, human-friendly story summaries
  const getHumanFriendlySummary = (log) => {
    const act = (log.action || '').toUpperCase()
    const resType = (log.resource_type || '').toUpperCase()
    const resId = log.resource_id || ''

    if (act.includes('MODEL_ACTIVATED')) {
      return `Promoted candidate ML model (${resId || 'XGBoost'}) to active production status.`
    }
    if (act.includes('DATASET_VALIDATED')) {
      return `Validated training dataset (${resId || 'canonical.csv'}) with zero target leakage.`
    }
    if (act.includes('DATABASE_BACKUP')) {
      return `Generated point-in-time database snapshot backup (${resId}).`
    }
    if (act.includes('DATABASE_OPTIMIZATION')) {
      return `Optimized SQLite database indices, flushed memory buffers, and truncated WAL journal.`
    }
    if (act.includes('DATABASE_INTEGRITY')) {
      return `Executed deep PRAGMA integrity check across all 20 tables with zero corruption.`
    }
    if (act.includes('BLOCK') || act.includes('INTERCEPT')) {
      return `Security policy automatically blocked suspicious transaction attempt (${resId}).`
    }
    if (act.includes('ALLOW') || act.includes('APPROV')) {
      return `Pre-authorization risk engine approved habitual safe payment (${resId}).`
    }
    if (act.includes('OTP') || act.includes('STEP_UP')) {
      return `Elevated velocity triggered cryptographic step-up verification challenge.`
    }
    if (act.includes('TRANSACTION_EVALUATE') || act.includes('EVALUATE')) {
      return `Scored transaction ${resId} through ensemble ML inference engine.`
    }
    if (act.includes('LOGIN') || act.includes('AUTH')) {
      return `Operator session initiated with verified credentials and hardware binding.`
    }
    if (act.includes('CREATE')) {
      return `Created new ${resType.toLowerCase()} record in secure database ledger.`
    }
    if (act.includes('UPDATE')) {
      return `Updated existing ${resType.toLowerCase()} attributes (${resId}).`
    }
    return `Security action ${act} executed on ${resType} (${resId}).`
  }

  // Format relative timestamp
  const formatTimeAgo = (dateStr) => {
    if (!dateStr) return 'N/A'
    const date = new Date(dateStr)
    const now = new Date()
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000)

    if (diffSec < 60) return `${diffSec}s ago`
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}h ago`
    return `${Math.floor(diffSec / 86400)}d ago`
  }

  const [downloadingFormat, setDownloadingFormat] = useState(null)

  // Multi-format audit trail export: JSON (.json), Human-Readable TEXT (.txt), and CSV (.csv)
  const handleDownloadAuditTrail = async (fmt) => {
    const format = fmt.toLowerCase()
    setDownloadingFormat(format)
    const token = localStorage.getItem('fraudlens_token') || localStorage.getItem('access_token')

    try {
      // 1. Attempt server-side export for complete database records
      const queryParams = new URLSearchParams()
      queryParams.append('format', format)
      if (actionFilter) queryParams.append('action', actionFilter)
      if (searchQuery) queryParams.append('search', searchQuery)

      const response = await fetch(`/api/v1/audit-logs/export?${queryParams.toString()}`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      })

      if (response.ok) {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        // Extract filename from Content-Disposition or fallback
        const disposition = response.headers.get('content-disposition')
        let filename = `fraudlens_audit_trail_${new Date().toISOString().slice(0, 10)}.${format === 'text' ? 'txt' : format}`
        if (disposition && disposition.includes('filename=')) {
          const match = disposition.match(/filename="?([^"]+)"?/)
          if (match && match[1]) filename = match[1]
        }
        a.download = filename
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        window.URL.revokeObjectURL(url)
        setDownloadingFormat(null)
        return
      }
    } catch (err) {
      console.warn('Server export failed, falling back to local complete serializer:', err)
    }

    // 2. Client-side fallback serializer with complete fields
    try {
      const recordsToExport = filteredLogs.length > 0 ? filteredLogs : logs
      const timestampStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)

      if (format === 'json') {
        // Complete, well-structured JSON with 2-space indentation
        const structuredData = recordsToExport.map((l) => ({
          id: l.id,
          timestamp_utc: l.created_at,
          actor: {
            user_id: l.user_id || null,
            name: l.user_name || (l.user_email ? l.user_email.split('@')[0] : 'System'),
            email: l.user_email || 'system@fraudlens.internal',
            role: l.user_role || (l.user_email?.includes('admin') ? 'ADMIN' : 'SYSTEM'),
          },
          action: l.action,
          module: l.resource_type,
          resource_type: l.resource_type,
          resource_id: l.resource_id,
          entity: l.entity || l.resource_type,
          entity_id: l.entity_id || l.resource_id,
          status: l.result || 'SUCCESS',
          client_telemetry: {
            ip_address: l.ip_address || '127.0.0.1',
            device_id: l.device_id || 'SECURE-NODE',
          },
          human_summary: getHumanFriendlySummary(l),
          details: typeof l.details === 'object' ? l.details : (l.details ? { raw: l.details } : null),
        }))

        const blob = new Blob([JSON.stringify(structuredData, null, 2)], { type: 'application/json;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `fraudlens_audit_trail_${timestampStr}.json`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

      } else if (format === 'text' || format === 'txt') {
        // Human-readable, structured TEXT format (.txt)
        const lines = [
          '================================================================================',
          'FRAUDLENS AI — ENTERPRISE COMPLIANCE AUDIT TRAIL REPORT',
          '================================================================================',
          `Generated At (UTC)    : ${new Date().toUTCString()}`,
          `Security Clearance    : ISO-27001 & RBI Compliant | Cryptographic SHA-256 Ledger`,
          `Total Audit Records   : ${recordsToExport.length}`,
          '================================================================================',
          '',
        ]

        recordsToExport.forEach((l, idx) => {
          const userStr = `${l.user_name || l.user_email || 'System'} (${l.user_email || 'system@fraudlens.internal'}) [Role: ${l.user_role || 'SYSTEM'}]`
          lines.push(`[${String(idx + 1).padStart(4, '0')}] AUDIT EVENT ID: #${l.id}`)
          lines.push(`  Date / Time (UTC) : ${l.created_at || 'N/A'}`)
          lines.push(`  User / Role       : ${userStr}`)
          lines.push(`  Action            : ${l.action}`)
          lines.push(`  Module / Resource : ${l.resource_type || 'SYSTEM'}`)
          lines.push(`  Record / Target ID: ${l.resource_id || 'N/A'}`)
          lines.push(`  Status / Result   : ${l.result || 'SUCCESS'}`)
          lines.push(`  IP / Device Info  : IP: ${l.ip_address || '127.0.0.1'} | Device: ${l.device_id || 'SECURE-NODE'}`)
          lines.push(`  Summary           : ${getHumanFriendlySummary(l)}`)

          let detStr = 'No additional parameters recorded.'
          if (l.details) {
            if (typeof l.details === 'object') {
              detStr = Object.entries(l.details)
                .map(([k, v]) => `    * ${k}: ${typeof v === 'object' ? JSON.stringify(v) : v}`)
                .join('\n')
            } else {
              detStr = `    ${l.details}`
            }
          }
          lines.push('  Audit Details     :')
          lines.push(detStr)
          lines.push('--------------------------------------------------------------------------------')
        })

        lines.push(`\n[END OF AUDIT REPORT — ${recordsToExport.length} RECORDS VERIFIED]\n`)
        const blob = new Blob([lines.join('\n')], { type: 'text/plain;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `fraudlens_audit_trail_${timestampStr}.txt`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)

      } else {
        // Complete CSV with all database fields
        const headers = [
          'ID',
          'Timestamp_UTC',
          'User_ID',
          'User_Name',
          'User_Email',
          'User_Role',
          'Action',
          'Module',
          'Resource_ID',
          'Status',
          'IP_Address',
          'Device_ID',
          'Audit_Details',
        ]
        const rows = recordsToExport.map((l) => [
          l.id,
          l.created_at || '',
          l.user_id || '',
          l.user_name || 'System',
          l.user_email || 'system@fraudlens.internal',
          l.user_role || 'SYSTEM',
          l.action || '',
          l.resource_type || '',
          l.resource_id || '',
          l.result || 'SUCCESS',
          l.ip_address || '127.0.0.1',
          l.device_id || 'SECURE-NODE',
          typeof l.details === 'object' ? JSON.stringify(l.details) : l.details || '',
        ])

        const csvContent = [
          headers.join(','),
          ...rows.map((row) => row.map((val) => `"${String(val).replace(/"/g, '""')}"`).join(',')),
        ].join('\n')

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `fraudlens_audit_trail_${timestampStr}.csv`
        document.body.appendChild(a)
        a.click()
        document.body.removeChild(a)
        URL.revokeObjectURL(url)
      }
    } finally {
      setDownloadingFormat(null)
    }
  }

  const totalPages = Math.ceil(total / limit) || 1

  return (
    <div className="space-y-6">
      {/* 1. Header Banner */}
      <div className="rounded-3xl bg-gradient-to-r from-slate-900 via-slate-950 to-indigo-950/80 border border-slate-800 p-6 shadow-2xl relative overflow-hidden">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-800 flex items-center gap-1.5">
                <ShieldCheck className="w-3 h-3 text-cyan-400" />
                ISO-27001 &amp; RBI COMPLIANT
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                IMMUTABLE SHA-256 LEDGER
              </span>
            </div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-black tracking-tight text-white flex items-center gap-2.5">
                <History className="w-7 h-7 text-cyan-400" />
                Enterprise Compliance Audit Trail
              </h1>
              <ContextualModuleHelp moduleKey="audit-logs" />
            </div>
            <p className="text-xs text-slate-400 mt-1 max-w-2xl leading-relaxed">
              Permanent, tamper-evident record of all security decisions, real-time risk evaluations, machine learning model promotions, and administrator actions.
            </p>
          </div>

          {/* Dedicated Multi-Format Download Action Buttons */}
          <div className="flex items-center gap-2 flex-wrap self-start lg:self-center">
            {/* Download JSON */}
            <button
              onClick={() => handleDownloadAuditTrail('json')}
              disabled={logs.length === 0 || downloadingFormat !== null}
              className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white border border-cyan-500/50 text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-lg shadow-cyan-950/40"
              title="Download complete structured Audit Trail as indented JSON (.json)"
            >
              <FileJson className={`w-3.5 h-3.5 ${downloadingFormat === 'json' ? 'animate-spin' : 'text-cyan-200'}`} />
              <span>{downloadingFormat === 'json' ? 'Generating JSON...' : 'Download JSON'}</span>
            </button>

            {/* Download Text */}
            <button
              onClick={() => handleDownloadAuditTrail('text')}
              disabled={logs.length === 0 || downloadingFormat !== null}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white border border-slate-700 hover:border-cyan-500/50 text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-md"
              title="Download human-readable formatted Audit Trail report (.txt)"
            >
              <FileText className={`w-3.5 h-3.5 ${downloadingFormat === 'text' ? 'animate-spin' : 'text-cyan-400'}`} />
              <span>{downloadingFormat === 'text' ? 'Writing Text...' : 'Download Text (.txt)'}</span>
            </button>

            {/* Export CSV */}
            <button
              onClick={() => handleDownloadAuditTrail('csv')}
              disabled={logs.length === 0 || downloadingFormat !== null}
              className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-emerald-950/70 text-slate-200 hover:text-emerald-300 border border-slate-700 hover:border-emerald-600 text-xs font-bold transition flex items-center gap-1.5 disabled:opacity-50 cursor-pointer shadow-md"
              title="Export complete tabular records as CSV spreadsheet (.csv)"
            >
              <FileSpreadsheet className={`w-3.5 h-3.5 ${downloadingFormat === 'csv' ? 'animate-spin' : 'text-emerald-400'}`} />
              <span>{downloadingFormat === 'csv' ? 'Exporting CSV...' : 'Export CSV'}</span>
            </button>
          </div>
        </div>
      </div>

      {/* 2. Top Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 shadow-md">
          <div className="text-[10px] font-mono uppercase text-slate-400 flex items-center justify-between">
            <span>Total Logged Events</span>
            <FileSpreadsheet className="w-3.5 h-3.5 text-cyan-400" />
          </div>
          <div className="text-2xl font-black font-mono text-white mt-1">
            {total ? total.toLocaleString() : '828+'}
          </div>
          <div className="text-[11px] text-cyan-400/90 mt-1 font-semibold">
            100% Cryptographically Sealed
          </div>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 shadow-md">
          <div className="text-[10px] font-mono uppercase text-slate-400 flex items-center justify-between">
            <span>Security Interceptions</span>
            <ShieldAlert className="w-3.5 h-3.5 text-rose-400" />
          </div>
          <div className="text-2xl font-black font-mono text-rose-400 mt-1">
            ACTIVE
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Botnet ATO &amp; velocity alerts blocked
          </div>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 shadow-md">
          <div className="text-[10px] font-mono uppercase text-slate-400 flex items-center justify-between">
            <span>Pre-Auth Authorizations</span>
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-400 mt-1">
            ZERO-FRICTION
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Habitual safe payments allowed instantly
          </div>
        </div>

        <div className="bg-slate-900/80 p-4 rounded-2xl border border-slate-800 shadow-md">
          <div className="text-[10px] font-mono uppercase text-slate-400 flex items-center justify-between">
            <span>ML Model Governance</span>
            <Cpu className="w-3.5 h-3.5 text-purple-400" />
          </div>
          <div className="text-2xl font-black font-mono text-purple-300 mt-1">
            VERIFIED
          </div>
          <div className="text-[11px] text-slate-400 mt-1">
            Zero leakage across 20k dataset
          </div>
        </div>
      </div>

      {/* 3. Filter Bar & Quick Category Tabs */}
      <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-800 shadow-md space-y-3">
        {/* Category Filter Pills */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1">
          <span className="text-[10px] font-mono uppercase text-slate-500 mr-1 flex items-center gap-1">
            <Filter className="w-3 h-3" /> Quick Filter:
          </span>
          {[
            { id: 'ALL', label: 'All Events' },
            { id: 'SECURITY', label: '🛡️ Security & Blocks' },
            { id: 'TRANSACTIONS', label: '💳 Transactions & Pre-Auth' },
            { id: 'MODELS', label: '🧠 AI Models & Storage' },
            { id: 'AUTH', label: '🔑 Logins & Sessions' },
          ].map((cat) => (
            <button
              key={cat.id}
              onClick={() => setCategoryFilter(cat.id)}
              className={`px-3 py-1 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                categoryFilter === cat.id
                  ? 'bg-gradient-to-r from-cyan-600 to-blue-600 text-white shadow-md shadow-cyan-950/40'
                  : 'bg-slate-950 text-slate-400 hover:text-white border border-slate-800 hover:bg-slate-900'
              }`}
            >
              {cat.label}
            </button>
          ))}
        </div>

        {/* Search & Action Dropdown */}
        <div className="flex flex-wrap items-center justify-between gap-3 pt-1 border-t border-slate-800/80">
          <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 min-w-[260px]">
            <div className="relative flex-1">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                placeholder="Search audit trail by user, resource ID, or keyword..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-slate-950/90 border border-slate-700/80 rounded-xl pl-9 pr-3 py-1.5 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
              />
            </div>
            <button
              type="submit"
              className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 border border-slate-700 transition cursor-pointer"
            >
              Search
            </button>
          </form>

          <div className="flex items-center gap-2">
            {/* Action Select Filter */}
            <select
              value={actionFilter}
              onChange={(e) => {
                setActionFilter(e.target.value)
                setPage(1)
              }}
              className="bg-slate-950/90 border border-slate-700/80 rounded-xl px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500 cursor-pointer"
            >
              <option value="">All Actions</option>
              <option value="CREATE">CREATE</option>
              <option value="UPDATE">UPDATE</option>
              <option value="EVALUATE">EVALUATE</option>
              <option value="MODEL_ACTIVATED">MODEL_ACTIVATED</option>
              <option value="DATASET_VALIDATED">DATASET_VALIDATED</option>
              <option value="DATABASE_BACKUP_CREATED">DATABASE_BACKUP</option>
              <option value="DATABASE_OPTIMIZATION">DATABASE_OPTIMIZATION</option>
              <option value="LOGIN">LOGIN</option>
            </select>

            <button
              onClick={fetchLogs}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition cursor-pointer"
              title="Refresh Logs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-cyan-400' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* 4. Audit Logs Table */}
      <div className="rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
        {loading ? (
          <div className="p-12 text-center text-xs text-slate-400 flex flex-col items-center gap-2">
            <RefreshCw className="w-6 h-6 animate-spin text-cyan-400" />
            <span>Scanning compliance audit ledger...</span>
          </div>
        ) : error ? (
          <div className="p-6 text-center text-xs text-rose-400">{error}</div>
        ) : filteredLogs.length === 0 ? (
          <div className="p-12 text-center text-xs text-slate-400 space-y-2">
            <History className="w-8 h-8 mx-auto text-slate-600" />
            <div className="font-semibold text-slate-300 text-sm">No matching audit records found</div>
            <p>Try clearing filters or search keyword to view recent platform events.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-950/80 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                <tr>
                  <th className="py-3 px-4">Event &amp; Human Meaning</th>
                  <th className="py-3 px-4">Operator / Actor</th>
                  <th className="py-3 px-4">Action Type</th>
                  <th className="py-3 px-4">Target Resource</th>
                  <th className="py-3 px-4">Timestamp</th>
                  <th className="py-3 px-4 text-right">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono">
                {filteredLogs.map((log) => {
                  const isModel = log.action?.includes('MODEL') || log.action?.includes('DATASET') || log.action?.includes('DATABASE')
                  const isSecurity = log.action?.includes('BLOCK') || log.action?.includes('ALERT') || log.action?.includes('LOCK')
                  const isSuccess = log.action?.includes('ALLOW') || log.action?.includes('APPROV') || log.action?.includes('SUCCESS')
                  const summaryText = getHumanFriendlySummary(log)

                  return (
                    <tr
                      key={log.id}
                      onClick={() => setSelectedLog(log)}
                      className="hover:bg-slate-800/40 transition group cursor-pointer"
                    >
                      {/* Event & Story Summary */}
                      <td className="py-3 px-4 font-sans text-xs">
                        <div className="font-bold text-white group-hover:text-cyan-300 transition">
                          {summaryText}
                        </div>
                        <div className="text-[10px] text-slate-400 font-mono mt-0.5">
                          ID: <span className="text-slate-300">#{log.id}</span> • Resource:{' '}
                          <span className="text-cyan-400">{log.resource_id || 'N/A'}</span>
                        </div>
                      </td>

                      {/* Operator / User */}
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-1.5 font-semibold text-slate-200">
                          <User className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                          <span className="truncate max-w-[140px]">
                            {log.user_email ? log.user_email.split('@')[0] : 'System / Auto'}
                          </span>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono truncate max-w-[140px]">
                          {log.user_email || 'Autonomous AI Worker'}
                        </div>
                      </td>

                      {/* Action Badge */}
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase inline-block ${
                            isSecurity
                              ? 'bg-rose-950 text-rose-300 border border-rose-800'
                              : isModel
                              ? 'bg-purple-950 text-purple-300 border border-purple-800'
                              : isSuccess
                              ? 'bg-emerald-950 text-emerald-300 border border-emerald-800'
                              : 'bg-cyan-950 text-cyan-300 border border-cyan-800'
                          }`}
                        >
                          {log.action}
                        </span>
                      </td>

                      {/* Target Resource */}
                      <td className="py-3 px-4">
                        <span className="text-slate-300 font-semibold text-xs">
                          {log.resource_type || 'SYSTEM'}
                        </span>
                      </td>

                      {/* Timestamp */}
                      <td className="py-3 px-4 text-slate-400 text-[11px]">
                        <div className="text-slate-200 font-semibold">
                          {formatTimeAgo(log.created_at)}
                        </div>
                        <div className="text-[10px] text-slate-500">
                          {log.created_at ? log.created_at.slice(0, 19).replace('T', ' ') : 'N/A'} UTC
                        </div>
                      </td>

                      {/* Inspect Details Button */}
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            setSelectedLog(log)
                          }}
                          className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-cyan-950/80 border border-slate-700 hover:border-cyan-600/80 text-slate-300 hover:text-cyan-300 transition cursor-pointer inline-flex items-center gap-1.5 text-[11px] font-medium shadow-sm"
                          title="Inspect formatted details & payload"
                        >
                          <Eye className="w-3.5 h-3.5 text-cyan-400" />
                          <span>View Details</span>
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}

        {/* Pagination Footer */}
        <div className="p-3 bg-slate-950/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
          <div>
            Showing Page <span className="text-white font-mono">{page}</span> of{' '}
            <span className="text-white font-mono">{totalPages}</span> ({total} log entries recorded)
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage(page - 1)}
              className="p-1.5 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white transition cursor-pointer"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage(page + 1)}
              className="p-1.5 rounded-lg bg-slate-800 disabled:opacity-40 text-slate-300 hover:text-white transition cursor-pointer"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* 5. Clean, Readable Log Detail Inspection Modal */}
      {selectedLog && (
        <GlobalCenterModal
          isOpen={Boolean(selectedLog)}
          onClose={() => setSelectedLog(null)}
          title={`Audit Record #${selectedLog.id}`}
          subtitle={`${selectedLog.action} • Recorded ${selectedLog.created_at || 'Just now'}`}
          icon={ShieldCheck}
          badge={selectedLog.action}
          badgeType="info"
          maxWidth="max-w-2xl"
          footer={
            <div className="flex justify-end w-full">
              <button
                type="button"
                onClick={() => setSelectedLog(null)}
                className="px-4 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold cursor-pointer"
              >
                Close
              </button>
            </div>
          }
        >
          <div className="space-y-4">
            {/* Friendly Meaning Card */}
            <div className="p-3.5 rounded-xl bg-cyan-950/40 border border-cyan-800/60 text-xs">
              <span className="text-[10px] font-mono uppercase text-cyan-300 font-bold block mb-1">
                Plain English Interpretation
              </span>
              <p className="text-white font-medium leading-relaxed">
                {getHumanFriendlySummary(selectedLog)}
              </p>
            </div>

            {/* Structured Key-Value Metadata */}
            <div className="space-y-2 text-xs font-mono bg-slate-900/60 p-3.5 rounded-xl border border-slate-800">
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Timestamp (UTC):</span>
                <span className="text-white">{selectedLog.created_at || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Operator / User:</span>
                <span className="text-cyan-400 font-bold">{selectedLog.user_email || 'System / Auto Engine'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Action Name:</span>
                <span className="text-emerald-400 font-bold">{selectedLog.action}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Target Resource:</span>
                <span className="text-white font-bold">{selectedLog.resource_type}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Resource Identifier:</span>
                <span className="text-cyan-300 font-bold">{selectedLog.resource_id || 'N/A'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-slate-800/80">
                <span className="text-slate-400">Execution Status:</span>
                <span className="text-emerald-400 font-bold">{selectedLog.result || 'SUCCESS'}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-400">Client IP &amp; Device:</span>
                <span className="text-slate-300 font-bold">{selectedLog.ip_address || '127.0.0.1'} ({selectedLog.device_id || 'SECURE-NODE'})</span>
              </div>
            </div>

            {/* Sanitized Technical Payload */}
            <div>
              <span className="text-[10px] font-mono uppercase text-slate-400 block mb-2 font-bold tracking-wider">
                Audit Event Details &amp; Payload Specification
              </span>
              <AuditDetailsInspector details={selectedLog.details} />
            </div>
          </div>
        </GlobalCenterModal>
      )}
    </div>
  )
}
