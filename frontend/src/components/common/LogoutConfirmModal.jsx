import React, { useEffect } from 'react'
import { LogOut, ShieldAlert, X, Lock } from 'lucide-react'

/**
 * LogoutConfirmModal
 *
 * Clean, enterprise-grade confirmation modal before initiating the
 * digital security door lockdown sequence.
 */
export default function LogoutConfirmModal({ isOpen, onClose, onConfirm, userName = 'Operator' }) {
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape' && isOpen) {
        onClose && onClose()
      }
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, onClose])

  if (!isOpen) return null

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="logout-confirm-title"
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in"
      onClick={onClose}
    >
      <div
        onClick={(e) => e.stopPropagation()}
        className="relative w-full max-w-md rounded-3xl bg-slate-950/95 border border-slate-800 p-6 sm:p-7 shadow-[0_25px_60px_rgba(0,0,0,0.9),0_0_30px_rgba(225,29,72,0.15)] text-left animate-scale-in space-y-5"
      >
        {/* Glow Accent */}
        <div className="absolute top-0 right-1/4 w-40 h-40 bg-rose-500/10 rounded-full blur-3xl pointer-events-none" />

        {/* Close 'X' Button */}
        <button
          type="button"
          onClick={onClose}
          className="absolute top-4 right-4 p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent hover:border-slate-800 transition"
          aria-label="Close dialog"
        >
          <X className="w-4 h-4" />
        </button>

        {/* Icon & Title */}
        <div className="flex items-start gap-4">
          <div className="p-3.5 rounded-2xl bg-gradient-to-tr from-rose-950 via-slate-900 to-rose-900/60 border border-rose-600/50 text-rose-400 shadow-[0_0_20px_rgba(225,29,72,0.3)] shrink-0">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold tracking-wider bg-rose-950/80 text-rose-300 border border-rose-800/80">
                SESSION TERMINATION
              </span>
            </div>
            <h2 id="logout-confirm-title" className="text-lg font-black text-white tracking-tight">
              Sign out of FraudLens AI?
            </h2>
          </div>
        </div>

        {/* Description */}
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          You are signed in as <strong className="text-white font-semibold">{userName}</strong>. Signing out will securely close your active session, invalidate local cryptographic tokens, and seal hardware enclave bindings.
        </p>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-2 border-t border-slate-800/80">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-800 hover:border-slate-700 text-xs font-bold text-slate-300 hover:text-white transition cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={onConfirm}
            className="flex items-center gap-2 px-5 py-2.5 rounded-xl bg-gradient-to-r from-rose-600 via-red-600 to-rose-700 hover:from-rose-500 hover:to-red-500 text-xs font-bold text-white shadow-lg shadow-rose-950/60 border border-rose-400/40 transition active:scale-95 cursor-pointer"
          >
            <LogOut className="w-4 h-4" />
            <span>Confirm Sign Out</span>
          </button>
        </div>
      </div>
    </div>
  )
}
