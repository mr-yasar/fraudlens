import React, { useState, useEffect } from 'react'
import {
  Cpu,
  FileSpreadsheet,
  Upload,
  CheckCircle2,
  Play,
  RefreshCw,
  Database,
  Shield,
} from 'lucide-react'
import { adminMlApi } from '../services/api'


export default function AdminMlView({ initialTab = 'models' }) {
  const [activeTab, setActiveTab] = useState(initialTab) // 'models' or 'dataset'

  // Model Management state
  const [models, setModels] = useState([])
  const [comparison, setComparison] = useState(null)
  const [loadingModels, setLoadingModels] = useState(true)
  const [activatingId, setActivatingId] = useState(null)
  const [isTraining, setIsTraining] = useState(false)
  const [actionMsg, setActionMsg] = useState(null)

  // Dataset Upload state
  const [selectedFile, setSelectedFile] = useState(null)
  const [uploadLoading, setUploadLoading] = useState(false)
  const [validationResult, setValidationResult] = useState(null)
  const [uploadError, setUploadError] = useState(null)
  const [datasetStatus, setDatasetStatus] = useState(null)
  const [loadingStatus, setLoadingStatus] = useState(false)

  const fetchModelData = async () => {
    setLoadingModels(true)
    try {
      const [modelList, compData] = await Promise.all([
        adminMlApi.listModels(),
        adminMlApi.getModelComparison(),
      ])
      setModels(modelList || [])
      setComparison(compData)
    } catch (err) {
      console.error('Error fetching model registry:', err)
    } finally {
      setLoadingModels(false)
    }
  }

  const fetchDatasetStatus = async () => {
    setLoadingStatus(true)
    try {
      const status = await adminMlApi.getDatasetStatus()
      setDatasetStatus(status)
    } catch (err) {
      console.error('Error fetching dataset status:', err)
    } finally {
      setLoadingStatus(false)
    }
  }

  useEffect(() => {
    fetchModelData()
    fetchDatasetStatus()
  }, [])

  const handleActivateModel = async (modelName) => {
    if (!modelName) return
    setActivatingId(modelName)
    try {
      await adminMlApi.activateModel(modelName)
      setActionMsg(`Model '${modelName}' successfully activated into production!`)
      fetchModelData()
      setTimeout(() => setActionMsg(null), 5000)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Failed to activate model')
    } finally {
      setActivatingId(null)
    }
  }

  const handleTrainModel = async (e) => {
    e.preventDefault()
    setIsTraining(true)
    try {
      const res = await adminMlApi.trainModel({
        dataset_path: 'data/raw/financial_fraud_customer_transactions.csv',
        model_version: 'v2.0.0',
        rf_n_estimators: 200,
        xgb_n_estimators: 200,
      })
      setActionMsg(`Training complete! Champion: ${res.selected_model || 'unknown'}. Refresh to see updated metrics.`)
      fetchModelData()
      fetchDatasetStatus()
      setTimeout(() => setActionMsg(null), 6000)
    } catch (err) {
      alert(err instanceof Error ? err.message : 'Training execution failed')
    } finally {
      setIsTraining(false)
    }
  }

  const handleValidateUpload = async (e) => {
    e.preventDefault()
    if (!selectedFile) return

    setUploadLoading(true)
    setUploadError(null)
    setValidationResult(null)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const res = await adminMlApi.validateDataset(formData)
      setValidationResult(res)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Dataset validation failed')
    } finally {
      setUploadLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      {/* View Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-purple-950 text-purple-300 border border-purple-800">
              ADMIN CONTROL CENTER
            </span>
          </div>
          <h2 className="text-xl font-bold text-white flex items-center gap-2 mt-1">
            <Cpu className="w-5 h-5 text-purple-400" />
            Machine Learning Lifecycle &amp; Dataset Governance
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Audit feature leakage, train candidate classifiers, and activate production models.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-900/80 p-1 rounded-xl border border-slate-800 text-xs">
          <button
            onClick={() => setActiveTab('models')}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
              activeTab === 'models'
                ? 'bg-purple-900/80 text-purple-200 shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Cpu className="w-4 h-4" /> Model Management
          </button>
          <button
            onClick={() => setActiveTab('dataset')}
            className={`px-3 py-1.5 rounded-lg font-medium transition flex items-center gap-1.5 ${
              activeTab === 'dataset'
                ? 'bg-purple-900/80 text-purple-200 shadow-md font-bold'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <FileSpreadsheet className="w-4 h-4" /> Dataset Validation
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3.5 rounded-xl bg-emerald-950/70 border border-emerald-800 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* 1. Model Management Tab */}
      {activeTab === 'models' && (
        <div className="space-y-6">
          {/* Train Candidate Model Form */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-purple-900/50 shadow-xl backdrop-blur-md">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
              <Play className="w-4 h-4 text-purple-400" />
              Trigger Supervised Candidate Retraining
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              Executes isolated stratified train/val split, applies preprocessing pipeline, evaluates PR-AUC &amp; F1, and optimizes decision thresholds.
            </p>

            <form onSubmit={handleTrainModel} className="flex flex-wrap items-center gap-3">
              <div className="flex-1 text-xs text-slate-400 font-mono bg-slate-950/60 px-3 py-2 rounded-xl border border-slate-800">
                <span className="text-cyan-300">Dataset:</span>{' '}
                financial_fraud_customer_transactions.csv (4,581 rows)
                <br />
                <span className="text-cyan-300">Trains:</span>{' '}
                Logistic Regression + Random Forest + XGBoost (all three)
              </div>

              <button
                type="submit"
                disabled={isTraining}
                className="px-4 py-2 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold text-xs transition shadow-lg shadow-purple-950 disabled:opacity-50 flex items-center gap-2"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${isTraining ? 'animate-spin' : ''}`} />
                {isTraining ? 'Training All Models (~2 min)...' : 'Train All 3 Models'}
              </button>
            </form>
          </div>

          {/* Model Registry List */}
          <div className="rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl overflow-hidden backdrop-blur-md">
            <div className="p-4 border-b border-slate-800 flex items-center justify-between">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                Production Model Registry
              </h3>
              <button
                onClick={fetchModelData}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                title="Refresh"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingModels ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {loadingModels ? (
              <div className="p-8 text-center text-xs text-slate-400">Loading model registry...</div>
            ) : models.length === 0 ? (
              <div className="p-8 text-center text-xs text-slate-500">No models registered yet.</div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-[10px] font-mono uppercase text-slate-400 border-b border-slate-800">
                    <tr>
                      <th className="py-3 px-4">Model</th>
                      <th className="py-3 px-4">Version</th>
                      <th className="py-3 px-4">ROC-AUC</th>
                      <th className="py-3 px-4">PR-AUC</th>
                      <th className="py-3 px-4">Recall</th>
                      <th className="py-3 px-4">F1</th>
                      <th className="py-3 px-4">Threshold</th>
                      <th className="py-3 px-4">Status</th>
                      <th className="py-3 px-4 text-right">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono">
                    {models.map((m) => {
                      const isActive = m.is_active
                      const modelName = m.model_name || m.name || ''

                      return (
                        <tr key={modelName || m.id} className="hover:bg-slate-800/40 transition">
                          <td className="py-3 px-4 font-bold text-white capitalize">
                            {modelName.replace(/_/g, ' ')}
                          </td>
                          <td className="py-3 px-4 text-purple-300 font-semibold">{m.version || m.model_version || 'v1.0.0'}</td>
                          <td className="py-3 px-4 text-slate-300">
                            {m.roc_auc !== undefined ? Number(m.roc_auc).toFixed(4) : 'N/A'}
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {m.pr_auc !== undefined ? Number(m.pr_auc).toFixed(4) : 'N/A'}
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {m.recall !== undefined ? Number(m.recall).toFixed(4) : 'N/A'}
                          </td>
                          <td className="py-3 px-4 text-slate-300">
                            {m.f1_score !== undefined ? Number(m.f1_score).toFixed(4) : 'N/A'}
                          </td>
                          <td className="py-3 px-4 text-cyan-400 font-bold">
                            {m.optimal_threshold !== undefined ? Number(m.optimal_threshold).toFixed(4) : (m.threshold !== undefined ? Number(m.threshold).toFixed(4) : 'N/A')}
                          </td>
                          <td className="py-3 px-4">
                            {isActive ? (
                              <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-950 text-emerald-400 border border-emerald-800 flex items-center gap-1 w-fit">
                                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                                ACTIVE INFERENCE
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded text-[10px] uppercase bg-slate-800 text-slate-400">
                                CANDIDATE
                              </span>
                            )}
                          </td>
                          <td className="py-3 px-4 text-right">
                            {!isActive && (
                              <button
                                disabled={activatingId === modelName}
                                onClick={() => handleActivateModel(modelName)}
                                className="px-3 py-1 rounded-lg bg-cyan-900/60 hover:bg-cyan-800 text-cyan-200 border border-cyan-700 text-xs font-semibold transition"
                              >
                                {activatingId === modelName ? 'Activating...' : 'Promote to Production'}
                              </button>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 2. Dataset Validation Tab */}
      {activeTab === 'dataset' && (
        <div className="space-y-6">

          {/* Live Active Dataset Status Card */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-cyan-900/50 shadow-xl backdrop-blur-md">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                <Database className="w-4 h-4 text-cyan-400" />
                Active Training Dataset Status
              </h3>
              <button
                onClick={fetchDatasetStatus}
                className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300"
                title="Refresh dataset status"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loadingStatus ? 'animate-spin' : ''}`} />
              </button>
            </div>

            {loadingStatus ? (
              <div className="text-xs text-slate-400 text-center py-4">Loading dataset status...</div>
            ) : datasetStatus ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono text-slate-300">{datasetStatus.dataset_name}</span>
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase ${
                    datasetStatus.validation_status === 'VALID'
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-rose-950 text-rose-400 border border-rose-800'
                  }`}>
                    {datasetStatus.validation_status}
                  </span>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                  <div className="p-3 bg-slate-950 rounded-xl">
                    <span className="text-[10px] text-slate-400 uppercase block">Total Rows</span>
                    <span className="font-bold text-white text-sm">{datasetStatus.row_count?.toLocaleString() || 0}</span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-xl">
                    <span className="text-[10px] text-slate-400 uppercase block">Columns</span>
                    <span className="font-bold text-white text-sm">{datasetStatus.column_count || 0}</span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-xl">
                    <span className="text-[10px] text-slate-400 uppercase block">Fraud Cases</span>
                    <span className="font-bold text-rose-400 text-sm">
                      {datasetStatus.target_distribution?.fraud ?? 'N/A'}
                      {datasetStatus.target_distribution?.fraud_percentage != null && (
                        <span className="text-[10px] text-slate-400 ml-1">({datasetStatus.target_distribution.fraud_percentage}%)</span>
                      )}
                    </span>
                  </div>
                  <div className="p-3 bg-slate-950 rounded-xl">
                    <span className="text-[10px] text-slate-400 uppercase block">Genuine</span>
                    <span className="font-bold text-emerald-400 text-sm">{datasetStatus.target_distribution?.genuine ?? 'N/A'}</span>
                  </div>
                </div>

                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                  <span className="font-semibold text-slate-200 block mb-1">Target Column: <span className="text-cyan-300 font-mono">{datasetStatus.target_column}</span></span>
                  <span className="text-slate-400 text-[11px]">
                    Leakage-protected columns detected:{' '}
                    <strong className="text-amber-400">{datasetStatus.leakage_findings?.length || 0} columns excluded from training</strong>
                    {datasetStatus.leakage_findings?.length > 0 && (
                      <span className="ml-2 font-mono text-slate-500">
                        ({datasetStatus.leakage_findings.map(l => l.column).join(', ')})
                      </span>
                    )}
                  </span>
                </div>
              </div>
            ) : (
              <div className="text-xs text-slate-500 text-center py-4">No dataset status available.</div>
            )}
          </div>

          {/* Upload & Validate Section */}
          <div className="p-5 rounded-2xl bg-slate-900/70 border border-slate-800 shadow-xl backdrop-blur-md">
            <h3 className="text-xs font-bold text-white uppercase tracking-wider mb-2 flex items-center gap-2">
              <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
              Upload & Validate Dataset
            </h3>
            <p className="text-xs text-slate-400 mb-4 leading-relaxed">
              Audits feature columns against the primary CSV schema (<code className="text-cyan-300 font-mono">Fraud_Label</code> target),
              checks class distribution, and executes formal leakage detection.
            </p>

            <form onSubmit={handleValidateUpload} className="space-y-4">
              <div className="border-2 border-dashed border-slate-700 rounded-2xl p-6 text-center hover:border-cyan-500/60 transition bg-slate-950/40">
                <Upload className="w-8 h-8 mx-auto text-cyan-400 mb-2" />
                <label className="cursor-pointer">
                  <span className="text-xs font-semibold text-cyan-400 hover:underline">Choose CSV Dataset</span>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                    className="hidden"
                  />
                </label>
                <div className="text-[11px] text-slate-400 font-mono mt-1">
                  {selectedFile ? selectedFile.name : 'Drag & drop or browse .csv files'}
                </div>
              </div>

              {uploadError && (
                <div className="p-3 rounded-xl bg-rose-950/70 border border-rose-800 text-rose-300 text-xs">
                  {uploadError}
                </div>
              )}

              <div className="flex justify-end">
                <button
                  type="submit"
                  disabled={!selectedFile || uploadLoading}
                  className="px-4 py-2 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-semibold text-xs transition disabled:opacity-50 flex items-center gap-2"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${uploadLoading ? 'animate-spin' : ''}`} />
                  {uploadLoading ? 'Auditing Dataset...' : 'Run 11-Step Validation Pipeline'}
                </button>
              </div>
            </form>
          </div>

          {/* Validation Result Display */}
          {validationResult && (
            <div className="p-5 rounded-2xl bg-slate-900/60 border border-slate-800 shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                  Validation &amp; Leakage Audit Report
                </h3>
                <span
                  className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold uppercase ${
                    validationResult.is_valid
                      ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                      : 'bg-rose-950 text-rose-400 border border-rose-800'
                  }`}
                >
                  {validationResult.is_valid ? 'VALIDATED FOR TRAINING' : 'VALIDATION BLOCKED'}
                </span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs font-mono">
                <div className="p-3 bg-slate-950 rounded-xl">
                  <span className="text-[10px] text-slate-400 uppercase block">Total Rows</span>
                  <span className="font-bold text-white text-sm">
                    {(validationResult.total_rows || validationResult.file_format?.total_rows || 0).toLocaleString()}
                  </span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl">
                  <span className="text-[10px] text-slate-400 uppercase block">Total Columns</span>
                  <span className="font-bold text-white text-sm">
                    {validationResult.total_columns || validationResult.file_format?.total_columns || 0}
                  </span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl">
                  <span className="text-[10px] text-slate-400 uppercase block">Fraud Ratio</span>
                  <span className="font-bold text-rose-400 text-sm">
                    {validationResult.target_distribution?.fraud_percentage ||
                     validationResult.target_analysis?.fraud_rate_percentage || 0}%
                  </span>
                </div>
                <div className="p-3 bg-slate-950 rounded-xl">
                  <span className="text-[10px] text-slate-400 uppercase block">Missing Cells</span>
                  <span className="font-bold text-emerald-400 text-sm">
                    {validationResult.missing_values?.total_null_entries ||
                     validationResult.missing_values?.total_missing_cells || 0}
                  </span>
                </div>
              </div>

              {/* Leakage Audit Details */}
              {validationResult.leakage_audit && (
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-xs">
                  <span className="font-semibold text-slate-200 block mb-1">Leakage Contamination Audit:</span>
                  <div className="text-slate-400 text-[11px] space-y-1">
                    <div>Safe features: <strong className="text-emerald-400">{validationResult.leakage_audit.safe_features_count || 0}</strong></div>
                    <div>Excluded (leakage risk): <strong className="text-rose-400">{validationResult.leakage_audit.excluded_features_count || 0}</strong></div>
                    {validationResult.leakage_audit.excluded_features?.length > 0 && (
                      <div className="font-mono text-[10px] text-slate-500">
                        Excluded: {validationResult.leakage_audit.excluded_features.map(f => f.feature).join(', ')}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
