import React, { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import { X } from 'lucide-react'

/**
 * GlobalCenterModal
 * 
 * Viewport-level portal modal mounted directly to document.body:
 * - Truly escapes all parent containers, stacking contexts, transforms & overflow:hidden
 * - Always centered horizontally & vertically in the active viewport
 * - Background scroll lock with exact scroll position preservation & restoration
 * - Internal scroll with overscroll-contain & fixed sticky header (close button always accessible)
 * - Esc key, backdrop click, and smooth cyber animations
 */
export default function GlobalCenterModal({
  isOpen,
  onClose,
  title,
  subtitle,
  icon: Icon,
  badge,
  badgeType,    // 'success' | 'danger' | 'warning' | 'info'
  badgeColor,   // raw Tailwind string for full custom control
  maxWidth = 'max-w-3xl',
  children,
  footer,
  showCloseButton = true,
  closeOnBackdrop = true,
  closeOnEsc = true,
  className = '',
}) {
  // Derive badgeColor from badgeType when not explicitly provided
  const resolvedBadgeColor = badgeColor || (
    badgeType === 'success'
      ? 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60'
      : badgeType === 'danger'
      ? 'bg-rose-950/80 text-rose-300 border-rose-700/60'
      : badgeType === 'warning'
      ? 'bg-amber-950/80 text-amber-300 border-amber-700/60'
      : 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60'  // default 'info'
  )

  const scrollStateRef = useRef({
    windowY: 0,
    containerEntries: [],
  })
  const modalContentRef = useRef(null)

  // Background Scroll Lock & Exact Position Restoration
  useEffect(() => {
    if (!isOpen || typeof document === 'undefined') return

    // 1. Record window scroll position
    const windowY = window.scrollY || window.pageYOffset || 0

    // 2. Identify and record all active scroll containers in the application
    const scrollContainers = Array.from(
      document.querySelectorAll('.overflow-y-auto, .overflow-auto, main, #root')
    )
    const containerEntries = scrollContainers
      .filter((el) => !el.closest('[role="dialog"]'))
      .map((el) => ({
        el,
        scrollTop: el.scrollTop,
        originalOverflow: el.style.overflowY || el.style.overflow || '',
      }))

    scrollStateRef.current = { windowY, containerEntries }

    // 3. Compensate scrollbar width to prevent layout shift
    const scrollbarWidth = window.innerWidth - document.documentElement.clientWidth
    const originalBodyPadding = document.body.style.paddingRight
    const originalBodyOverflow = document.body.style.overflow

    if (scrollbarWidth > 0) {
      document.body.style.paddingRight = `${scrollbarWidth}px`
    }
    document.body.style.overflow = 'hidden'

    // Lock scrolling on background containers without resetting scrollTop
    containerEntries.forEach(({ el }) => {
      el.style.overflow = 'hidden'
    })

    return () => {
      // Restore body styles
      document.body.style.overflow = originalBodyOverflow || ''
      document.body.style.paddingRight = originalBodyPadding || ''

      // Restore container styles and exact scroll offsets
      containerEntries.forEach(({ el, scrollTop, originalOverflow }) => {
        el.style.overflow = originalOverflow
        el.scrollTop = scrollTop
      })

      // Restore window scroll
      window.scrollTo(0, windowY)
    }
  }, [isOpen])

  // ESC Key Listener
  useEffect(() => {
    if (!isOpen || !closeOnEsc) return

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        e.preventDefault()
        onClose && onClose()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isOpen, closeOnEsc, onClose])

  if (!isOpen || typeof document === 'undefined') return null

  const modalNode = (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="global-modal-title"
      className="fixed inset-0 z-[99999] flex items-center justify-center p-3 sm:p-5 md:p-6 select-text"
      style={{ isolation: 'isolate' }}
    >
      {/* Full-Screen Dark Frosted Glass Backdrop */}
      <div
        className="fixed inset-0 bg-black/80 backdrop-blur-md transition-opacity duration-300"
        onClick={() => closeOnBackdrop && onClose && onClose()}
        aria-hidden="true"
        onWheel={(e) => e.stopPropagation()}
        onTouchMove={(e) => e.stopPropagation()}
      />

      {/* Viewport-Exact Centered Modal Dialog Box */}
      <div
        ref={modalContentRef}
        className={`relative w-full ${maxWidth} max-h-[90vh] sm:max-h-[88vh] bg-slate-950/95 border border-cyan-500/50 rounded-3xl shadow-[0_0_50px_rgba(6,182,212,0.3),0_20px_60px_rgba(0,0,0,0.9)] flex flex-col overflow-hidden z-10 transition-all duration-300 animate-in zoom-in-95 fade-in duration-200 ${className}`}
        onClick={(e) => e.stopPropagation()}
        style={{
          width: 'min(100%, calc(100vw - 24px))',
          maxHeight: 'min(90vh, calc(100vh - 32px))',
        }}
      >
        {/* Cyber Neon Corner Brackets */}
        <div className="absolute -top-1 -left-1 w-5 h-5 border-t-2 border-l-2 border-cyan-400 rounded-tl-xl pointer-events-none z-30" />
        <div className="absolute -top-1 -right-1 w-5 h-5 border-t-2 border-r-2 border-cyan-400 rounded-tr-xl pointer-events-none z-30" />
        <div className="absolute -bottom-1 -left-1 w-5 h-5 border-b-2 border-l-2 border-cyan-400 rounded-bl-xl pointer-events-none z-30" />
        <div className="absolute -bottom-1 -right-1 w-5 h-5 border-b-2 border-r-2 border-cyan-400 rounded-br-xl pointer-events-none z-30" />

        {/* Modal Header — Always Pinned & Accessible */}
        <div className="flex items-center justify-between px-5 sm:px-6 py-4 border-b border-slate-800/90 bg-slate-900/95 shrink-0 sticky top-0 z-20">
          <div className="flex items-center gap-3 min-w-0 pr-3">
            {Icon && (
              <div className="p-2.5 rounded-xl bg-gradient-to-tr from-cyan-600/30 to-blue-600/30 border border-cyan-500/40 text-cyan-300 shrink-0 shadow-sm">
                <Icon className="w-5 h-5" />
              </div>
            )}
            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <h3
                  id="global-modal-title"
                  className="text-base sm:text-lg font-extrabold text-white tracking-wide truncate"
                >
                  {title}
                </h3>
                {badge && (
                  <span
                    className={`px-2 py-0.5 rounded-md text-[10px] font-mono font-bold border uppercase tracking-wider ${resolvedBadgeColor}`}
                  >
                    {badge}
                  </span>
                )}
              </div>
              {subtitle && (
                <p className="text-xs text-slate-400 mt-0.5 truncate font-medium">
                  {subtitle}
                </p>
              )}
            </div>
          </div>

          {/* Prominent, Accessible Close '✕' Button */}
          {showCloseButton && (
            <button
              type="button"
              onClick={onClose}
              className="p-2 rounded-xl bg-slate-800/80 hover:bg-rose-950/80 border border-slate-700 hover:border-rose-600/60 text-slate-400 hover:text-rose-300 transition shrink-0 group focus:outline-none focus:ring-2 focus:ring-cyan-500/50 cursor-pointer"
              aria-label="Close modal"
              title="Close (Esc)"
            >
              <X className="w-4 h-4 group-hover:rotate-90 transition-transform duration-200" />
            </button>
          )}
        </div>

        {/* Modal Scrollable Body — Internal Scroll with overscroll containment */}
        <div
          className="flex-1 overflow-y-auto roomy-scrollbar p-5 sm:p-6 space-y-4"
          style={{ overscrollBehavior: 'contain' }}
        >
          {children}
        </div>

        {/* Optional Sticky Footer */}
        {footer && (
          <div className="px-5 sm:px-6 py-3.5 border-t border-slate-800/90 bg-slate-900/95 shrink-0 relative z-20 flex items-center justify-between gap-3">
            {footer}
          </div>
        )}
      </div>
    </div>
  )

  return createPortal(modalNode, document.body)
}
