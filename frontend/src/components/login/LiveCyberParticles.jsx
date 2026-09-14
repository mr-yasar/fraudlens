import React, { useEffect, useRef } from 'react'

/**
 * LiveCyberParticles - Subtle, lightweight canvas overlay providing floating
 * cyber dust, micro-sparks, and faint scan sweeps over the cinematic background.
 * During isHyperSpeed, particles shoot outwards from the Security Core (34.2% X, 47% Y)
 * creating a cinematic camera fly-through depth transition.
 * Respects prefers-reduced-motion.
 */
export default function LiveCyberParticles({ mouseOffset = { x: 0, y: 0 }, isHyperSpeed = false }) {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    let animationFrameId
    let width = (canvas.width = canvas.offsetWidth * window.devicePixelRatio)
    let height = (canvas.height = canvas.offsetHeight * window.devicePixelRatio)

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    // Subtle ambient cyber dust particles
    const particleCount = 65
    const particles = Array.from({ length: particleCount }, () => {
      const angle = Math.random() * Math.PI * 2
      const dist = Math.random() * Math.max(width, height) * 0.7
      return {
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 1.8 + 0.8,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4 - 0.1,
        angle,
        dist,
        speed: Math.random() * 8 + 4,
        alpha: Math.random() * 0.6 + 0.2,
        color: Math.random() > 0.3 ? 'rgba(34, 211, 238,' : 'rgba(168, 85, 247,',
      }
    })

    let scanY = 0

    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Center of the AI Security Core in pixel coordinates
      const coreX = width * 0.363
      const coreY = height * 0.472

      if (!prefersReducedMotion) {
        if (isHyperSpeed) {
          // RADIAL HYPERSPACE WARP STREAKS FROM SECURITY CORE
          particles.forEach((p) => {
            p.dist += p.speed * 2.5
            if (p.dist > Math.max(width, height)) {
              p.dist = Math.random() * 40 + 10
              p.angle = Math.random() * Math.PI * 2
            }

            const x = coreX + Math.cos(p.angle) * p.dist
            const y = coreY + Math.sin(p.angle) * p.dist
            const tailLength = Math.min(p.dist * 0.25, 45)
            const tailX = coreX + Math.cos(p.angle) * (p.dist - tailLength)
            const tailY = coreY + Math.sin(p.angle) * (p.dist - tailLength)

            const grad = ctx.createLinearGradient(tailX, tailY, x, y)
            grad.addColorStop(0, 'rgba(6, 182, 212, 0)')
            grad.addColorStop(1, 'rgba(52, 211, 153, 0.85)')

            ctx.strokeStyle = grad
            ctx.lineWidth = Math.min(p.dist * 0.006 + 1, 3)
            ctx.beginPath()
            ctx.moveTo(tailX, tailY)
            ctx.lineTo(x, y)
            ctx.stroke()
          })
        } else {
          // 1. Subtle horizontal laser scan line drift
          scanY = (scanY + 1.2) % height
          const scanGrad = ctx.createLinearGradient(0, scanY, 0, scanY + 12)
          scanGrad.addColorStop(0, 'rgba(6, 182, 212, 0)')
          scanGrad.addColorStop(0.5, 'rgba(6, 182, 212, 0.08)')
          scanGrad.addColorStop(1, 'rgba(6, 182, 212, 0)')
          ctx.fillStyle = scanGrad
          ctx.fillRect(0, scanY, width, 12)

          // 2. Floating cyber dust
          particles.forEach((p) => {
            p.x += p.vx + mouseOffset.x * 0.5
            p.y += p.vy + mouseOffset.y * 0.5

            if (p.x < 0) p.x = width
            if (p.x > width) p.x = 0
            if (p.y < 0) p.y = height
            if (p.y > height) p.y = 0

            ctx.fillStyle = `${p.color} ${p.alpha})`
            ctx.beginPath()
            ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2)
            ctx.fill()
          })
        }
      }

      if (!prefersReducedMotion) {
        animationFrameId = requestAnimationFrame(render)
      }
    }

    render()

    const handleResize = () => {
      width = canvas.width = canvas.offsetWidth * window.devicePixelRatio
      height = canvas.height = canvas.offsetHeight * window.devicePixelRatio
      if (prefersReducedMotion) render()
    }

    window.addEventListener('resize', handleResize)
    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
    }
  }, [mouseOffset, isHyperSpeed])

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full pointer-events-none z-10"
      aria-hidden="true"
    />
  )
}
