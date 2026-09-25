/**
 * customerHelper.js
 * Helpers for Customer & Admin persona resolution, authorization boundaries,
 * and role-based data isolation.
 */

export function getCustomerPersona(user) {
  if (!user) {
    return {
      customerId: 'CUST_MONISHA_001',
      name: 'Monisha',
      customerName: 'Monisha',
      fraudRate: '3.0%',
      baselineType: 'Safe Habitual (Auto-Approved)',
      badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
      color: 'emerald',
      isCustomer: false,
    }
  }

  const email = (user.email || '').toLowerCase()
  const name = (user.name || '').toLowerCase()
  const role = (user.role || '').toLowerCase()
  const isAdmin = role.includes('admin') || email.includes('admin')
  const isCustomer = !isAdmin && (role === 'customer' || role === 'user')

  if (email.includes('monisha') || name.includes('monisha')) {
    return {
      customerId: 'CUST_MONISHA_001',
      name: 'Monisha',
      customerName: 'Monisha',
      email: user.email,
      fraudRate: '3.0%',
      baselineType: 'Safe Habitual (Auto-Approved)',
      badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
      color: 'emerald',
      defaultPresetId: 'scenario_monisha_safe',
      isCustomer,
    }
  }

  if (email.includes('mohana') || name.includes('mohana')) {
    return {
      customerId: 'CUST_MOHANA_002',
      name: 'Mohana',
      customerName: 'Mohana',
      email: user.email,
      fraudRate: '12.0%',
      baselineType: 'Elevated Velocity (Step-Up OTP)',
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
      color: 'amber',
      defaultPresetId: 'scenario_mohana_review',
      isCustomer,
    }
  }

  if (email.includes('sowmiya') || name.includes('sowmiya')) {
    return {
      customerId: 'CUST_SOWMIYA_003',
      name: 'Sowmiya',
      customerName: 'Sowmiya',
      email: user.email,
      fraudRate: '26.0%',
      baselineType: 'Botnet ATO Attack (Pre-Auth Block)',
      badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
      color: 'rose',
      defaultPresetId: 'scenario_sowmiya_block',
      isCustomer,
    }
  }

  return {
    customerId: user.id ? `CUST-${String(user.id).padStart(4, '0')}` : 'CUST-0001',
    name: user.name || 'Customer',
    customerName: user.name || 'Customer',
    email: user.email,
    fraudRate: '5.0%',
    baselineType: 'Standard Account Baseline',
    badgeColor: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60',
    color: 'cyan',
    defaultPresetId: 'scenario_4_cold_start',
    isCustomer,
  }
}
