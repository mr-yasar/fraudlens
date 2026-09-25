/**
 * Indian Rupee (INR ₹) and Data Formatting Utilities.
 * Formats numbers using the Indian numbering system (Lakhs, Crores) with ₹ symbol.
 */

export function formatINR(amount, includeSymbol = true) {
  if (amount === null || amount === undefined || isNaN(Number(amount))) {
    return includeSymbol ? '₹0.00' : '0.00'
  }
  const num = Number(amount)
  const formatted = num.toLocaleString('en-IN', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return includeSymbol ? `₹${formatted}` : formatted
}

export function formatINRCompact(amount) {
  if (amount === null || amount === undefined || isNaN(Number(amount))) return '₹0'
  const num = Math.abs(Number(amount))
  if (num >= 10000000) {
    return `₹${(num / 10000000).toFixed(2)} Cr`
  }
  if (num >= 100000) {
    return `₹${(num / 100000).toFixed(2)} L`
  }
  if (num >= 1000) {
    return `₹${(num / 1000).toFixed(1)}k`
  }
  return `₹${num.toFixed(2)}`
}

export function formatDate(dateString) {
  if (!dateString) return 'N/A'
  try {
    const d = new Date(dateString)
    return d.toLocaleString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true,
    })
  } catch {
    return dateString
  }
}
