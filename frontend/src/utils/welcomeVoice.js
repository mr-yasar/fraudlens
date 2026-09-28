/**
 * welcomeVoice.js
 *
 * Dedicated, rock-solid audio & speech synthesis engine for FraudLens AI.
 * Plays a soft, natural, pleasant voice greeting: "Welcome, [UserName]."
 * Guaranteed consistent behavior for Monisha, Mohana, Soumya, Ajay, and Administrator.
 *
 * Features:
 * - One-time duplicate suppression lock (prevents React StrictMode/re-render replay).
 * - Automatic voice selection (Natural / Google / Apple English).
 * - Chrome SpeechSynthesis queue & resume unsticking.
 * - Non-blocking, fails gracefully on browser autoplay restrictions.
 */

let lastSpokenUser = ''
let lastSpokenTimestamp = 0
const DEDUPLICATION_INTERVAL_MS = 12000 // 12 seconds cooldown per user

/**
 * Normalizes any user object or string into canonical user name:
 * - Monisha
 * - Mohana
 * - Soumya
 * - Ajay
 * - Administrator
 */
export function normalizeUserName(input) {
  if (!input) return 'Operator'

  let raw = ''
  if (typeof input === 'string') {
    raw = input.toLowerCase()
  } else if (typeof input === 'object') {
    raw = `${input.name || ''} ${input.email || ''} ${input.customerName || ''}`.toLowerCase()
  }

  if (raw.includes('admin')) return 'Administrator'
  if (raw.includes('monisha')) return 'Monisha'
  if (raw.includes('mohana')) return 'Mohana'
  if (raw.includes('soumya') || raw.includes('sowmiya')) return 'Soumya'
  if (raw.includes('ajay') || raw.includes('alexander') || raw.includes('premium')) return 'Ajay'

  // Fallback to title-cased name
  if (typeof input === 'object' && input.name) {
    return input.name.trim()
  }
  return 'Operator'
}

/**
 * Plays the personalized welcome greeting voice:
 * "Welcome, [UserName]."
 *
 * @param {string|object} userOrName - User name or user object
 * @param {boolean} force - Bypass deduplication if true
 */
export function playWelcomeVoice(userOrName, force = false) {
  if (typeof window === 'undefined') return

  const userName = normalizeUserName(userOrName)
  const now = Date.now()

  // Prevent duplicate voice triggers within cooldown window
  if (!force && lastSpokenUser === userName && now - lastSpokenTimestamp < DEDUPLICATION_INTERVAL_MS) {
    return
  }

  lastSpokenUser = userName
  lastSpokenTimestamp = now

  const welcomeText = `Welcome, ${userName}.`

  try {
    if ('speechSynthesis' in window) {
      // Resume paused synthesis context in Chrome
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume()
      }

      // Cancel any old stuck speech queue
      window.speechSynthesis.cancel()

      const speakNow = () => {
        try {
          const utterance = new SpeechSynthesisUtterance(welcomeText)
          utterance.rate = 0.92 // Gentle, natural pace
          utterance.pitch = 1.0 // Natural pitch
          utterance.volume = 0.6 // Clear, medium-soft volume

          const voices = window.speechSynthesis.getVoices() || []

          // Prioritize high-quality natural voices
          const preferredVoice =
            voices.find(
              (v) =>
                (v.name.includes('Natural') ||
                  v.name.includes('Google') ||
                  v.name.includes('Samantha') ||
                  v.name.includes('Victoria') ||
                  v.name.includes('Jenny') ||
                  v.name.includes('Karen') ||
                  v.name.includes('Zira')) &&
                v.lang.startsWith('en')
            ) ||
            voices.find((v) => v.lang.startsWith('en')) ||
            voices[0]

          if (preferredVoice) {
            utterance.voice = preferredVoice
          }

          // Non-blocking invocation
          setTimeout(() => {
            try {
              window.speechSynthesis.speak(utterance)
            } catch {
              // Silently handle any browser autoplay restrictions
            }
          }, 60)
        } catch {
          // Graceful ignore
        }
      }

      // If voices are already loaded, speak immediately; otherwise wait for onvoiceschanged
      const availableVoices = window.speechSynthesis.getVoices()
      if (availableVoices && availableVoices.length > 0) {
        speakNow()
      } else {
        const onVoices = () => {
          window.speechSynthesis.removeEventListener('voiceschanged', onVoices)
          speakNow()
        }
        window.speechSynthesis.addEventListener('voiceschanged', onVoices)
        // Fallback timeout in case voiceschanged never fires
        setTimeout(speakNow, 250)
      }
    }
  } catch {
    // Autoplay restrictions safely caught
  }
}

/**
 * Resets the voice deduplication cache (e.g. on clean logout).
 */
export function resetWelcomeVoiceCache() {
  lastSpokenUser = ''
  lastSpokenTimestamp = 0
}
