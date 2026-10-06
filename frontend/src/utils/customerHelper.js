/**
 * customerHelper.js
 * Helpers for Customer & Admin persona resolution, authorization boundaries,
 * and role-based data isolation.
 */

export function getCustomerPersona(user, selectedPersonaId = null) {
  const email = (user?.email || '').toLowerCase()
  const name = (user?.name || '').toLowerCase()
  const role = (user?.role || '').toLowerCase()
  const isAdmin = role.includes('admin') || role.includes('investigator') || email.includes('admin') || email.includes('investigator')

  // 1. STRICT CUSTOMER ISOLATION:
  // If an actual customer is logged in, their own authenticated identity is SACROSANCT.
  // selectedPersonaId MUST NEVER hijack or override an authenticated customer's identity!
  if (user && !isAdmin) {
    // 1a. Check Monisha first
    if (email.includes('monisha') || name.includes('monisha')) {
      return {
        customerId: 'CUST_MONISHA_001',
        name: 'Monisha',
        customerName: 'Monisha',
        email: user.email,
        tier: 'STANDARD',
        fraudRate: '3.0%',
        baselineType: 'Safe Habitual (Zero-Friction Auto-Approved, No OTP)',
        badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
        color: 'emerald',
        defaultPresetId: 'scenario_monisha_safe',
        isCustomer: true,
        isPremium: false,
      }
    }

    // 1b. Check Mohana / Mogana
    if (email.includes('mohana') || name.includes('mohana') || email.includes('mogana') || name.includes('mogana')) {
      return {
        customerId: 'CUST_MOHANA_002',
        name: 'Mohana',
        customerName: 'Mohana',
        email: user.email,
        tier: 'STANDARD',
        fraudRate: '12.0%',
        baselineType: 'Elevated Velocity (Step-Up OTP)',
        badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
        color: 'amber',
        defaultPresetId: 'scenario_mohana_review',
        isCustomer: true,
        isPremium: false,
      }
    }

    // 1c. Check Sowmiya
    if (email.includes('soumya') || name.includes('soumya') || email.includes('sowmiya') || name.includes('sowmiya')) {
      return {
        customerId: 'CUST_SOWMIYA_003',
        name: 'Sowmiya',
        customerName: 'Sowmiya',
        email: user.email,
        tier: 'STANDARD',
        fraudRate: '26.0%',
        baselineType: 'Botnet ATO Attack (Pre-Auth Block)',
        badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
        color: 'rose',
        defaultPresetId: 'scenario_sowmiya_block',
        isCustomer: true,
        isPremium: false,
      }
    }

    // 1d. Check Ajay
    if (email.includes('ajay') || name.includes('ajay') || email.includes('premium') || name.includes('alexander') || email.includes('alex')) {
      return {
        customerId: 'CUST_AJAY_004',
        name: 'Ajay',
        customerName: 'Ajay',
        email: user.email || 'ajay@fraudlens.ai',
        tier: 'ENTERPRISE',
        isPremium: true,
        fraudRate: '0.2%',
        baselineType: 'Enterprise Security Tier (Adaptive AI + Enclave Vault)',
        badgeColor: 'bg-indigo-950/90 text-indigo-200 border-indigo-500/70 shadow-[0_0_15px_rgba(99,102,241,0.35)]',
        color: 'indigo',
        defaultPresetId: 'scenario_ajay_saas',
        isCustomer: true,
      }
    }

    return {
      customerId: user.id ? `CUST-${String(user.id).padStart(4, '0')}` : 'CUST-0001',
      name: user.name || 'Customer',
      customerName: user.name || 'Customer',
      email: user.email,
      tier: user.account_tier || 'STANDARD',
      fraudRate: '5.0%',
      baselineType: 'Standard Account Baseline',
      badgeColor: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60',
      color: 'cyan',
      defaultPresetId: 'scenario_4_cold_start',
      isCustomer: true,
      isPremium: user?.account_tier === 'PREMIUM',
    }
  }

  // 2. ADMIN / INVESTIGATOR PERSONA TESTING:
  // If an Admin or Investigator is selecting a persona to test, resolve according to selectedPersonaId
  if (selectedPersonaId) {
    const s = String(selectedPersonaId).toLowerCase()
    if (s.includes('ajay')) {
      return {
        customerId: 'CUST_AJAY_004',
        name: 'Ajay',
        customerName: 'Ajay',
        email: 'ajay@fraudlens.ai',
        tier: 'ENTERPRISE',
        isPremium: true,
        fraudRate: '0.2%',
        baselineType: 'Enterprise Security Tier (Adaptive AI + Enclave Vault)',
        badgeColor: 'bg-indigo-950/90 text-indigo-200 border-indigo-500/70 shadow-[0_0_15px_rgba(99,102,241,0.35)]',
        color: 'indigo',
        defaultPresetId: 'scenario_ajay_saas',
        isCustomer: true,
      }
    }
    if (s.includes('sowmiya') || s.includes('soumya')) {
      return {
        customerId: 'CUST_SOWMIYA_003',
        name: 'Sowmiya',
        customerName: 'Sowmiya',
        email: 'sowmiya@fraudlens.ai',
        tier: 'STANDARD',
        fraudRate: '26.0%',
        baselineType: 'Botnet ATO Attack (Pre-Auth Block)',
        badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
        color: 'rose',
        defaultPresetId: 'scenario_sowmiya_block',
        isCustomer: true,
      }
    }
    if (s.includes('mohana')) {
      return {
        customerId: 'CUST_MOHANA_002',
        name: 'Mohana',
        customerName: 'Mohana',
        email: 'mohana@fraudlens.ai',
        tier: 'STANDARD',
        fraudRate: '12.0%',
        baselineType: 'Elevated Velocity (Step-Up OTP)',
        badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
        color: 'amber',
        defaultPresetId: 'scenario_mohana_review',
        isCustomer: true,
      }
    }
    if (s.includes('monisha')) {
      return {
        customerId: 'CUST_MONISHA_001',
        name: 'Monisha',
        customerName: 'Monisha',
        email: 'monisha@fraudlens.ai',
        tier: 'STANDARD',
        fraudRate: '3.0%',
        baselineType: 'Safe Habitual (Zero-Friction Auto-Approved, No OTP)',
        badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
        color: 'emerald',
        defaultPresetId: 'scenario_monisha_safe',
        isCustomer: true,
      }
    }
  }

  // If Admin is logged in and no persona simulation was selected, they have NO customer persona
  if (isAdmin) {
    return {
      customerId: null,
      name: user?.name || 'Administrator',
      customerName: user?.name || 'Administrator',
      email: user?.email || 'admin@fraudlens.ai',
      tier: 'ADMIN',
      fraudRate: '0.0%',
      baselineType: 'System Administrator Mode (Full Enterprise Access)',
      badgeColor: 'bg-purple-950/80 text-purple-300 border-purple-700/60',
      color: 'purple',
      defaultPresetId: null,
      isCustomer: false,
      isAdmin: true,
      isPremium: false,
    }
  }

  // 3. Fallback when not authenticated
  return {
    customerId: null,
    name: 'Guest',
    customerName: 'Guest',
    email: '',
    tier: 'GUEST',
    fraudRate: '0.0%',
    baselineType: 'Unauthenticated Guest',
    badgeColor: 'bg-slate-950/80 text-slate-300 border-slate-700/60',
    color: 'slate',
    defaultPresetId: null,
    isCustomer: false,
    isAdmin: false,
    isPremium: false,
  }
}

/**
 * Resolve human-friendly customer name from customer_id, real record, or user record.
 * Prioritizes actual DB record over hardcoded fallbacks.
 */
export function resolveCustomerName(customerId, fallback = 'Customer', actualName = null) {
  if (actualName && typeof actualName === 'string' && actualName.trim()) {
    return actualName.trim()
  }
  if (!customerId) return fallback
  const s = String(customerId).toUpperCase()
  if (s.includes('MONISHA')) return 'Monisha'
  if (s.includes('MOHANA')) return 'Mohana'
  if (s.includes('MOGANA')) return 'Mohana'
  if (s.includes('SOWMIYA') || s.includes('SOUMYA')) return 'Sowmiya'
  if (s.includes('AJAY')) return 'Ajay'
  return fallback
}

/**
 * Resolve appropriate non-sensitive account profile identifier for Admin Radar & audit views.
 * Guarantees zero PII leakage under ISO-27001 multi-tenant compliance.
 */
export function resolveAccountProfile(customerId, fallback = 'Standard Tier') {
  if (!customerId) return fallback
  const s = String(customerId).toUpperCase()
  if (s.includes('AJAY') || s.includes('PREM') || s.includes('_004')) return 'Enterprise Tier'
  if (s.includes('SOWMIYA') || s.includes('SOUMYA') || s.includes('_003')) return 'Suspicious ATO Tier'
  if (s.includes('MOHANA') || s.includes('MOGANA') || s.includes('_002')) return 'Elevated Velocity Tier'
  if (s.includes('MONISHA') || s.includes('_001')) return 'Standard / Safe Tier'
  return fallback
}

/**
 * Get visual badge colors, non-sensitive profile, and metadata for customer IDs
 */
export function getCustomerMeta(customerId, isAdmin = false) {
  const s = String(customerId || '').toUpperCase()
  const profile = resolveAccountProfile(customerId)

  if (s.includes('MONISHA') || s.includes('_001')) {
    return {
      name: isAdmin ? profile : 'Monisha',
      profileName: 'Standard / Safe Tier (3%)',
      color: 'emerald',
      bgBadge: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
    }
  }

  if (s.includes('MOHANA') || s.includes('MOGANA') || s.includes('_002')) {
    return {
      name: isAdmin ? profile : 'Mohana',
      profileName: 'Elevated Velocity Tier (12%)',
      color: 'amber',
      bgBadge: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
    }
  }

  if (s.includes('SOWMIYA') || s.includes('SOUMYA') || s.includes('_003')) {
    return {
      name: isAdmin ? profile : 'Sowmiya',
      profileName: 'Suspicious ATO Tier (26%)',
      color: 'rose',
      bgBadge: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
    }
  }

  if (s.includes('AJAY') || s.includes('PREM') || s.includes('_004')) {
    return {
      name: isAdmin ? profile : 'Ajay',
      profileName: 'Enterprise Security Tier (0.2%)',
      color: 'indigo',
      bgBadge: 'bg-indigo-950/90 text-indigo-300 border-indigo-600/70',
    }
  }

  return {
    name: isAdmin ? profile : (customerId || 'Customer'),
    profileName: 'Standard Profile',
    color: 'slate',
    bgBadge: 'bg-slate-900 text-slate-300 border-slate-700',
  }
}

