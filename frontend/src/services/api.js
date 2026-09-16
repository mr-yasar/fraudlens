/**
 * Centralized API Client for FraudLens AI Financial Fraud & Risk Detection System.
 * Ensures consistent JWT header injection, centralized error handling, and robust routing.
 */

const BASE_URL = '/api/v1'

function getAuthHeaders() {
  const token = localStorage.getItem('fraudlens_token')
  return {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
  }
}

async function handleResponse(response) {
  if (response.status === 401) {
    // If unauthorized, clear cached credentials
    localStorage.removeItem('fraudlens_token')
    localStorage.removeItem('fraudlens_user')
  }

  if (!response.ok) {
    let errorMessage = `HTTP Error ${response.status}: ${response.statusText}`
    try {
      const errorJson = await response.json()
      if (errorJson.detail) {
        errorMessage = typeof errorJson.detail === 'string' ? errorJson.detail : JSON.stringify(errorJson.detail)
      }
    } catch {
      // Non-JSON response
    }
    const error = new Error(errorMessage)
    error.status = response.status
    throw error
  }

  // Handle empty bodies
  if (response.status === 204) return null
  return response.json()
}

// 1. Dashboard & Reports API
export const dashboardApi = {
  getStats: async () => {
    const res = await fetch(`${BASE_URL}/dashboard/stats`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getReports: async () => {
    const res = await fetch(`${BASE_URL}/dashboard/reports`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 2. Transactions & Real-time Evaluation API
export const transactionsApi = {
  list: async ({ page = 1, limit = 20, risk_level = '', prediction = '', search = '' } = {}) => {
    const params = new URLSearchParams({ page, limit })
    if (risk_level) params.append('risk_level', risk_level)
    if (prediction !== '' && prediction !== undefined) params.append('prediction', prediction)
    if (search) params.append('search', search)

    const res = await fetch(`${BASE_URL}/transactions?${params.toString()}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  get: async (transactionId) => {
    const res = await fetch(`${BASE_URL}/transactions/${transactionId}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  evaluate: async (payload) => {
    const res = await fetch(`${BASE_URL}/transactions/evaluate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
  getExplanation: async (transactionId) => {
    const res = await fetch(`${BASE_URL}/transactions/${transactionId}/explanation`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 2b. Pre-Authorization Payment Gateway API (Phase 6 & 7)
export const paymentApi = {
  initiate: async (payload) => {
    const res = await fetch(`${BASE_URL}/payment/initiate`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
  getCustomerProfile: async (customerId) => {
    const res = await fetch(`${BASE_URL}/payment/customer-profile/${customerId}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 3. Customers API
export const customersApi = {
  list: async ({ page = 1, limit = 20, search = '' } = {}) => {
    const params = new URLSearchParams({ page, limit })
    if (search) params.append('search', search)

    const res = await fetch(`${BASE_URL}/customers?${params.toString()}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  get: async (customerId) => {
    const res = await fetch(`${BASE_URL}/customers/${customerId}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getTransactions: async (customerId, { page = 1, limit = 10 } = {}) => {
    const params = new URLSearchParams({ page, limit })
    const res = await fetch(`${BASE_URL}/customers/${customerId}/transactions?${params.toString()}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 4. Investigations API
export const investigationsApi = {
  list: async ({ page = 1, limit = 20, status = '', decision = '' } = {}) => {
    const params = new URLSearchParams({ page, limit })
    if (status) params.append('status', status)
    if (decision) params.append('decision', decision)

    const res = await fetch(`${BASE_URL}/investigations?${params.toString()}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  get: async (caseId) => {
    const res = await fetch(`${BASE_URL}/investigations/${caseId}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  create: async (payload) => {
    const res = await fetch(`${BASE_URL}/investigations`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
  update: async (caseId, payload) => {
    const res = await fetch(`${BASE_URL}/investigations/${caseId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
}

// 5. Audit Logs API
export const auditLogsApi = {
  list: async ({ page = 1, limit = 20, action = '', resource_type = '', search = '' } = {}) => {
    const params = new URLSearchParams({ page, limit })
    if (action) params.append('action', action)
    if (resource_type) params.append('resource_type', resource_type)
    if (search) params.append('search', search)

    const res = await fetch(`${BASE_URL}/audit-logs?${params.toString()}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 6. Admin ML & Dataset API (ADMIN Only)
export const adminMlApi = {
  listModels: async () => {
    const res = await fetch(`${BASE_URL}/admin/models`, {
      headers: getAuthHeaders(),
    })
    const data = await handleResponse(res)
    // Backend returns { models: [...], active_model: ..., model_version: ... }
    // Return the models array for the frontend list
    if (data && Array.isArray(data.models)) return data.models
    if (data && Array.isArray(data)) return data
    return []
  },
  getModelComparison: async () => {
    const res = await fetch(`${BASE_URL}/admin/models/comparison`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  trainModel: async (payload) => {
    // payload may contain { model_type } from the UI
    // Backend expects TrainModelRequest: { dataset_path, model_version, rf_n_estimators, xgb_n_estimators }
    const backendPayload = {
      dataset_path: 'data/raw/financial_fraud_customer_transactions.csv',
      model_version: 'v2.0.0',
      rf_n_estimators: 200,
      xgb_n_estimators: 200,
      ...payload,
    }
    const res = await fetch(`${BASE_URL}/admin/models/train`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(backendPayload),
    })
    return handleResponse(res)
  },
  activateModel: async (modelNameOrId) => {
    // modelNameOrId can be an integer DB id or a string model name
    // The backend expects the string model name: logistic_regression / random_forest / xgboost
    const res = await fetch(`${BASE_URL}/admin/models/${modelNameOrId}/activate`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  validateDataset: async (formData) => {
    const token = localStorage.getItem('fraudlens_token')
    const res = await fetch(`${BASE_URL}/admin/datasets/validate`, {
      method: 'POST',
      headers: {
        'Accept': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
      },
      body: formData,
    })
    return handleResponse(res)
  },
  getDatasetStatus: async () => {
    const res = await fetch(`${BASE_URL}/admin/datasets/status`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 7. System Health API
export const systemApi = {
  getHealth: async () => {
    const res = await fetch('/api/health', {
      headers: { Accept: 'application/json' },
    })
    return handleResponse(res)
  },
}
