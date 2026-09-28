import React, { useEffect, useRef, useState } from 'react'
import { ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react'
import { playWelcomeVoice } from '../../utils/welcomeVoice'

/**
 * PersonalizedWelcomeOverlay
 *
 * Enterprise-grade 2.5-second personalized welcome experience upon login.
 * Tailored light streaks, particles, and typography for:
 * - Monisha: Emerald Green (Safe / Verified)
 * - Mohana: Warm Orange + Gold (Velocity Guard)
 * - Soumya: Red (ATO Defense Identity)
 * - Ajay: Purple + Cyan (Enclave Security - NORMAL USER)
 */

const USER_THEMES = {
  monisha: {
    name: 'Monisha',
    welcomeText: 'Welcome, Monisha',
    subtitle: 'Identity Verified • Safe Consumer Session Initialized',
    primaryColor: '#10b981', // Emerald Green
    secondaryColor: '#34d399',
    glowColor: 'rgba(16, 185, 129, 0.35)',
    bgRadial: 'radial-gradient(circle at 50% 45%, rgba(16, 185, 129, 0.2) 0%, rgba(2, 6, 23, 0.85) 60%, rgba(2, 6, 23, 0.96) 100%)',
    badgeText: 'SAFE IDENTITY',
    badgeBg: 'bg-emerald-950/90 text-emerald-300 border-emerald-700/60',
  },
  mohana: {
    name: 'Mohana',
    welcomeText: 'Welcome, Mohana',
    subtitle: 'Identity Verified • Adaptive Velocity Protection Armed',
    primaryColor: '#f59e0b', // Amber / Gold
    secondaryColor: '#fbbf24',
    glowColor: 'rgba(245, 158, 11, 0.35)',
    bgRadial: 'radial-gradient(circle at 50% 45%, rgba(245, 158, 11, 0.2) 0%, rgba(2, 6, 23, 0.85) 60%, rgba(2, 6, 23, 0.96) 100%)',
    badgeText: 'VELOCITY GUARD',
    badgeBg: 'bg-amber-950/90 text-amber-300 border-amber-700/60',
  },
  soumya: {
    name: 'Soumya',
    welcomeText: 'Welcome, Soumya',
    subtitle: 'Identity Verified • Threat Defense Shield Active',
    primaryColor: '#ef4444', // Red / Rose
    secondaryColor: '#f87171',
    glowColor: 'rgba(239, 68, 68, 0.35)',
    bgRadial: 'radial-gradient(circle at 50% 45%, rgba(239, 68, 68, 0.2) 0%, rgba(2, 6, 23, 0.85) 60%, rgba(2, 6, 23, 0.96) 100%)',
    badgeText: 'THREAT DEFENSE',
    badgeBg: 'bg-rose-950/90 text-rose-300 border-rose-700/60',
  },
  sowmiya: {
    name: 'Soumya',
    welcomeText: 'Welcome, Soumya',
    subtitle: 'Identity Verified • Threat Defense Shield Active',
    primaryColor: '#ef4444',
    secondaryColor: '#f87171',
    glowColor: 'rgba(239, 68, 68, 0.35)',
    bgRadial: 'radial-gradient(circle at 50% 45%, rgba(239, 68, 68, 0.2) 0%, rgba(2, 6, 23, 0.85) 60%, rgba(2, 6, 23, 0.96) 100%)',
    badgeText: 'THREAT DEFENSE',
    badgeBg: 'bg-rose-950/90 text-rose-300 border-rose-700/60',
  },
  ajay: {
    name: 'Ajay',
    welcomeText: 'Welcome, Ajay',
    subtitle: 'Identity Verified • Enterprise Enclave Security Armed',
    primaryColor: '#8b5cf6', // Violet / Purple
    secondaryColor: '#06b6d4', // Cyan accent
    glowColor: 'rgba(139, 92, 246, 0.35)',
    bgRadial: 'radial-gradient(circle at 50% 45%, rgba(139, 92, 246, 0.2) 0%, rgba(2, 6, 23, 0.85) 60%, rgba(2, 6, 23, 0.96) 100%)',
    badgeText: 'ENCLAVE ACTIVE',
    badgeBg: 'bg-purple-950/90 text-purple-300 border-purple-700/60',
  },
  admin: {
    name: 'Administrator',
    welcomeText: 'Welcome, Administrator',
    subtitle: 'Security Clearance Verified • Command Center Online',
    primaryColor: '#6366f1',
    secondaryColor: '#38bdf8',
    glowColor: 'rgba(99, 102, 241, 0.35)',
    bgRadial: 'radial-gradient(circle at 50% 45%, rgba(99, 102, 241, 0.2) 0%, rgba(2, 6, 23, 0.85) 60%, rgba(2, 6, 23, 0.96) 100%)',
    badgeText: 'SECURITY CLEARANCE',
    badgeBg: 'bg-indigo-950/90 text-indigo-300 border-indigo-700/60',
  },
}

function resolveUserTheme(user) {
  if (!user) return USER_THEMES.monisha
  const email = (user.email || '').toLowerCase()
  const name = (user.name || '').toLowerCase()
  const role = (user.role || '').toLowerCase()

  if (email.includes('admin') || role.includes('admin')) return USER_THEMES.admin
  if (email.includes('ajay') || name.includes('ajay')) return USER_THEMES.ajay
  if (email.includes('soumya') || name.includes('soumya') || email.includes('sowmiya') || name.includes('sowmiya')) return USER_THEMES.soumya
  if (email.includes('mohana') || name.includes('mohana')) return USER_THEMES.mohana
  if (email.includes('monisha') || name.includes('monisha')) return USER_THEMES.monisha

  return USER_THEMES.ajay
}

export default function PersonalizedWelcomeOverlay({ user, onComplete }) {
  const [isFadingOut, setIsFadingOut] = useState(false)
  const canvasRef = useRef(null)
  const animFrameRef = useRef(null)
  const hasSpokenRef = useRef(false)
  const theme = resolveUserTheme(user)

  // Voice Announcement (Gentle, low-volume, single-shot, non-blocking)
  useEffect(() => {
    if (!hasSpokenRef.current) {
      hasSpokenRef.current = true
      playWelcomeVoice(theme.name)
    }
  }, [theme.name])

  // Timer: 2.3s total, begins fade-out at 1.8s, completes at 2.4s
  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (prefersReducedMotion) {
      const fastTimer = setTimeout(() => {
        onComplete && onComplete()
      }, 400)
      return () => clearTimeout(fastTimer)
    }

    const fadeTimer = setTimeout(() => {
      setIsFadingOut(true)
    }, 1800)

    const finishTimer = setTimeout(() => {
      onComplete && onComplete()
    }, 2350)

    return () => {
      clearTimeout(fadeTimer)
      clearTimeout(finishTimer)
    }
  }, [onComplete])

  // Canvas Subtle Particle / Light Streak Background
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let width = (canvas.width = window.innerWidth)
    let height = (canvas.height = window.innerHeight)

    const handleResize = () => {
      if (!canvas) return
      width = canvas.width = window.innerWidth
      height = canvas.height = window.innerHeight
    }
    window.addEventListener('resize', handleResize)

    // Particles tailored to user theme
    const particleCount = 28
    const particles = []
    for (let i = 0; i < particleCount; i++) {
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        vx: (Math.random() - 0.5) * 1.2,
        vy: -0.8 - Math.random() * 1.5,
        size: 1.5 + Math.random() * 2.5,
        alpha: 0.2 + Math.random() * 0.6,
        life: Math.random() * 100,
      })
    }

    // Light Streaks
    const streaks = [
      { x: width * 0.3, y: height * 0.4, length: 140, angle: -Math.PI / 4, speed: 4, alpha: 0.4 },
      { x: width * 0.7, y: height * 0.6, length: 180, angle: -Math.PI / 4, speed: 5, alpha: 0.35 },
      { x: width * 0.5, y: height * 0.3, length: 110, angle: -Math.PI / 4, speed: 3.5, alpha: 0.5 },
    ]

    let t = 0
    const render = () => {
      t += 0.02
      ctx.clearRect(0, 0, width, height)

      // Render Floating Subtle Particles
      particles.forEach((p) => {
        p.x += p.vx
        p.y += p.vy
        p.life += 1
        if (p.y < 0) {
          p.y = height + 10
          p.x = Math.random() * width
        }

        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = theme.primaryColor
        ctx.globalAlpha = p.alpha * Math.sin((p.life % 60) / 60 * Math.PI)
        ctx.shadowColor = theme.primaryColor
        ctx.shadowBlur = 8
        ctx.fill()
        ctx.shadowBlur = 0
      })

      // Render Elegant Light Streaks
      streaks.forEach((s) => {
        s.x += Math.cos(s.angle) * s.speed
        s.y += Math.sin(s.angle) * s.speed
        if (s.x > width || s.y < 0) {
          s.x = Math.random() * width * 0.6
          s.y = height + Math.random() * 100
        }

        const grad = ctx.createLinearGradient(
          s.x,
          s.y,
          s.x - Math.cos(s.angle) * s.length,
          s.y - Math.sin(s.angle) * s.length
        )
        grad.addColorStop(0, theme.secondaryColor)
        grad.addColorStop(1, 'transparent')

        ctx.beginPath()
        ctx.moveTo(s.x, s.y)
        ctx.lineTo(
          s.x - Math.cos(s.angle) * s.length,
          s.y - Math.sin(s.angle) * s.length
        )
        ctx.strokeStyle = grad
        ctx.lineWidth = 2
        ctx.globalAlpha = s.alpha
        ctx.stroke()
      })

      ctx.globalAlpha = 1.0
      animFrameRef.current = requestAnimationFrame(render)
    }

    render()

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current)
      window.removeEventListener('resize', handleResize)
    }
  }, [theme])

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center select-none pointer-events-none transition-all duration-500 ease-out ${
        isFadingOut ? 'opacity-0 scale-105 blur-sm' : 'opacity-100 scale-100 blur-0'
      }`}
      style={{
        background: theme.bgRadial,
      }}
    >
      {/* Particle & Streak Canvas */}
      <canvas ref={canvasRef} className="absolute inset-0 w-full h-full pointer-events-none" />

      {/* Center Welcome Card */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center px-6 max-w-md animate-fade-in">
        {/* Glowing Shield Icon with User Color Aura */}
        <div
          className="relative w-20 h-20 rounded-3xl p-4 flex items-center justify-center mb-5 border shadow-2xl transition-all duration-500"
          style={{
            backgroundColor: `${theme.primaryColor}18`,
            borderColor: `${theme.primaryColor}80`,
            boxShadow: `0 0 45px ${theme.glowColor}`,
          }}
        >
          <div
            className="absolute -inset-1 rounded-3xl blur-md opacity-70 animate-pulse pointer-events-none"
            style={{ backgroundColor: theme.primaryColor }}
          />
          <ShieldCheck
            className="w-10 h-10 relative z-10"
            style={{ color: theme.secondaryColor }}
          />
        </div>

        {/* User Identity Badge */}
        <div className="mb-3">
          <span
            className={`text-[10px] font-mono px-3 py-1 rounded-full uppercase font-bold tracking-widest border shadow-md ${theme.badgeBg}`}
          >
            {theme.badgeText}
          </span>
        </div>

        {/* Personalized Welcome Headline */}
        <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight leading-tight mb-2">
          {theme.welcomeText}
        </h1>

        {/* Subtitle */}
        <p className="text-xs text-slate-300 font-medium max-w-xs leading-relaxed">
          {theme.subtitle}
        </p>

        {/* Subtle Loading / Progress Bar */}
        <div className="w-44 h-1 rounded-full bg-slate-800/80 mt-6 overflow-hidden border border-slate-700/50">
          <div
            className="h-full rounded-full transition-all duration-[2000ms] ease-out"
            style={{
              backgroundColor: theme.primaryColor,
              width: isFadingOut ? '100%' : '80%',
              boxShadow: `0 0 10px ${theme.primaryColor}`,
            }}
          />
        </div>
      </div>
    </div>
  )
}
