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
  getCustomerDashboard: async (customerId) => {
    const res = await fetch(`${BASE_URL}/dashboard/customer/${encodeURIComponent(customerId)}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 2. Transactions & Real-time Evaluation API
export const transactionsApi = {
  list: async ({ page = 1, limit = 20, risk_level = '', prediction = '', search = '', customer_id = '' } = {}) => {
    const params = new URLSearchParams({ page, limit })
    if (risk_level) params.append('risk_level', risk_level)
    if (prediction !== '' && prediction !== undefined) params.append('prediction', prediction)
    if (search) params.append('search', search)
    if (customer_id) params.append('customer_id', customer_id)

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
  getExplanation: async (transactionId, model = null) => {
    const query = model ? `?model=${encodeURIComponent(model)}` : ''
    const res = await fetch(`${BASE_URL}/transactions/${transactionId}/explanation${query}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 2b. Pre-Authorization Payment Gateway API (Phases 1-2)
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
  getWallet: async (customerId) => {
    const res = await fetch(`${BASE_URL}/payment/wallet/${customerId}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getBeneficiaries: async (customerId) => {
    const res = await fetch(`${BASE_URL}/payment/beneficiaries/${customerId}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  addBeneficiary: async (customerId, payload) => {
    const res = await fetch(`${BASE_URL}/payment/beneficiaries/${customerId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
  listPendingApprovals: async (customerId = '') => {
    const url = customerId
      ? `${BASE_URL}/payment/approvals/pending?customer_id=${encodeURIComponent(customerId)}`
      : `${BASE_URL}/payment/approvals/pending`
    const res = await fetch(url, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  processApproval: async (approvalId, { action, notes = '', challenge_response = '' }) => {
    const res = await fetch(`${BASE_URL}/payment/approvals/${approvalId}/action`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ action, notes, challenge_response }),
    })
    return handleResponse(res)
  },
  approve: async (approvalId) => {
    const res = await fetch(`${BASE_URL}/payment/approvals/${approvalId}/approve`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  reject: async (approvalId) => {
    const res = await fetch(`${BASE_URL}/payment/approvals/${approvalId}/reject`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  sendApprovalOtp: async (approvalId) => {
    const res = await fetch(`${BASE_URL}/payment/approvals/${approvalId}/send-otp`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 2c. Predictions & Counterfactual Explainability API
export const predictionsApi = {
  predict: async (payload) => {
    const res = await fetch(`${BASE_URL}/predictions/predict`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
  explain: async (payload, topK = 5) => {
    const res = await fetch(`${BASE_URL}/predictions/explain?top_k=${topK}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
  getGlobalExplanation: async () => {
    const res = await fetch(`${BASE_URL}/predictions/explain/global`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getCounterfactual: async (payload) => {
    const res = await fetch(`${BASE_URL}/predictions/explain/counterfactual`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
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
  getAiDossier: async (caseId, provider = 'gemini') => {
    const res = await fetch(`${BASE_URL}/investigations/${caseId}/ai-copilot?provider=${encodeURIComponent(provider)}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getAiVoiceHelp: async (topic = 'what_is_fraud', query = null, provider = 'gemini') => {
    let url = `${BASE_URL}/investigations/ai-voice-help/explain?topic=${encodeURIComponent(topic)}&provider=${encodeURIComponent(provider)}`
    if (query) {
      url += `&query=${encodeURIComponent(query)}`
    }
    const res = await fetch(url, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getTimeline: async (caseId) => {
    const res = await fetch(`${BASE_URL}/investigations/${caseId}/timeline`, {
      headers: getAuthHeaders(),
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
    const res = await fetch(`${BASE_URL}/health`, {
      headers: { Accept: 'application/json' },
    })
    return handleResponse(res)
  },
}

// 8. Fraud Intelligence Fabric API (Continuous Behaviour, Device/Session & Network Graph)
export const intelligenceApi = {
  getCustomerBehavior: async (customerId, amount = 100.0) => {
    const res = await fetch(`${BASE_URL}/intelligence/customer/${customerId}?amount=${amount}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  assessDeviceRisk: async (customerId, deviceType = 'web', failedAttempts = 0) => {
    const res = await fetch(`${BASE_URL}/intelligence/device/assess?customer_id=${customerId}&device_type=${deviceType}&failed_attempts=${failedAttempts}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

export const networkApi = {
  getRelationshipGraph: async (customerId, depth = 2) => {
    const res = await fetch(`${BASE_URL}/network/graph?customer_id=${customerId}&depth=${depth}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getNetworkClusters: async () => {
    const res = await fetch(`${BASE_URL}/network/clusters`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 9. Adaptive Intelligence & Federated Learning Simulation API (Phase 2)
export const adaptiveApi = {
  getThreats: async (limit = 200) => {
    const res = await fetch(`${BASE_URL}/adaptive/threats?limit=${limit}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getRuleEffectiveness: async () => {
    const res = await fetch(`${BASE_URL}/adaptive/rules/effectiveness`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getCandidateRules: async () => {
    const res = await fetch(`${BASE_URL}/adaptive/rules/candidates`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  createCandidateRule: async (data) => {
    const res = await fetch(`${BASE_URL}/adaptive/rules/candidates`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    })
    return handleResponse(res)
  },
  approveCandidateRule: async (ruleId) => {
    const res = await fetch(`${BASE_URL}/adaptive/rules/candidates/${ruleId}/approve`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  rejectCandidateRule: async (ruleId, reason = 'Rejected by Admin') => {
    const res = await fetch(`${BASE_URL}/adaptive/rules/candidates/${ruleId}/reject?reason=${encodeURIComponent(reason)}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  runFederatedSimulation: async (rounds = 3) => {
    const res = await fetch(`${BASE_URL}/adaptive/federated/simulate?rounds=${rounds}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  getModelComparison: async () => {
    const res = await fetch(`${BASE_URL}/adaptive/models/comparison`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  recordGovernanceAction: async (data) => {
    const res = await fetch(`${BASE_URL}/adaptive/governance/action`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    })
    return handleResponse(res)
  },
  recordInvestigatorFeedback: async (data) => {
    const res = await fetch(`${BASE_URL}/adaptive/feedback/record`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data),
    })
    return handleResponse(res)
  },
}

// 10. In-App Security Alerts API
export const alertsApi = {
  list: async ({ unacknowledged_only = false, severity = '', limit = 50 } = {}) => {
    const params = new URLSearchParams({ unacknowledged_only, limit })
    if (severity) params.append('severity', severity)
    const res = await fetch(`${BASE_URL}/alerts?${params.toString()}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  acknowledge: async (alertId) => {
    const res = await fetch(`${BASE_URL}/alerts/${alertId}/acknowledge`, {
      method: 'POST',
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
}

// 11. AI Assistant & Key Diagnostics API
export const aiApi = {
  getProviders: async () => {
    const res = await fetch(`${BASE_URL}/ai/providers`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  verifyKey: async (provider = 'all') => {
    const res = await fetch(`${BASE_URL}/ai/verify-key?provider=${encodeURIComponent(provider)}`, {
      headers: getAuthHeaders(),
    })
    return handleResponse(res)
  },
  chat: async (payload) => {
    const res = await fetch(`${BASE_URL}/ai/chat`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(payload),
    })
    return handleResponse(res)
  },
}



