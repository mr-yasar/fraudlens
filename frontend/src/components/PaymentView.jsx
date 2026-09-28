import React, { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import {
  CreditCard,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Lock,
  ArrowRight,
  Activity,
  CheckCircle2,
  XCircle,
  Clock,
  Sparkles,
  RefreshCw,
  Sliders,
  Smartphone,
  Globe,
  HelpCircle,
  ChevronRight,
  ChevronDown,
  UserCheck,
  Wallet,
  UserPlus,
  Send,
  Zap,
  Info,
  IndianRupee,
  Search,
  Check,
  Store,
  MapPin,
  Building2,
  Receipt,
  FileText,
  Download,
  Printer,
  Share2,
  History,
  QrCode,
  KeyRound,
  Eye,
  EyeOff,
  Radio,
  Users,
  Layers,
  ArrowUpRight,
  TrendingDown,
  Cpu,
  Flame,
  Tv,
  Wifi,
  Droplets,
  Lightbulb,
} from 'lucide-react'
import { paymentApi, transactionsApi } from '../services/api'
import { formatINR, formatDateTime } from '../utils/formatters'
import { getCustomerPersona } from '../utils/customerHelper'
import MobileSecurityApprovalModal from './MobileSecurityApprovalModal'
import GlobalCenterModal from './common/GlobalCenterModal'
import ContextualModuleHelp from './common/ContextualModuleHelp'

// Bank accounts available for customer debit
const LINKED_BANK_ACCOUNTS = [
  {
    id: 'hdfc_primary',
    bankName: 'HDFC Bank',
    accountType: 'Savings Account',
    accountNumberMasked: '•••• •••• 4821',
    ifsc: 'HDFC0000240',
    branch: 'Anna Nagar, Chennai',
    balance: 547855.0,
    isPrimary: true,
    logoColor: 'from-blue-700 to-indigo-800',
  },
  {
    id: 'sbi_salary',
    bankName: 'State Bank of India',
    accountType: 'Salary Account',
    accountNumberMasked: '•••• •••• 9102',
    ifsc: 'SBIN0001542',
    branch: 'Nungambakkam, Chennai',
    balance: 242100.0,
    isPrimary: false,
    logoColor: 'from-cyan-700 to-blue-900',
  },
  {
    id: 'icici_digital',
    bankName: 'ICICI Bank',
    accountType: 'Digital iMobile A/C',
    accountNumberMasked: '•••• •••• 3341',
    ifsc: 'ICIC0000001',
    branch: 'T Nagar, Chennai',
    balance: 547855.0,
    isPrimary: false,
    logoColor: 'from-orange-700 to-amber-900',
  },
  {
    id: 'fraudlens_wallet',
    bankName: 'FraudLens Instant Wallet',
    accountType: 'Prepaid Escrow Wallet',
    accountNumberMasked: '•••• 1500',
    ifsc: 'FLNS000001',
    branch: 'Digital Cyber Wallet',
    balance: 547855.0,
    isPrimary: false,
    logoColor: 'from-emerald-600 to-teal-800',
  },
]

// Popular NetBanking banks in India
const NETBANKING_BANKS = [
  { code: 'HDFC', name: 'HDFC Bank', icon: '🏦' },
  { code: 'SBI', name: 'State Bank of India', icon: '🏛️' },
  { code: 'ICICI', name: 'ICICI Bank', icon: '🏢' },
  { code: 'AXIS', name: 'Axis Bank', icon: '💳' },
  { code: 'KOTAK', name: 'Kotak Mahindra Bank', icon: '🏦' },
  { code: 'PNB', name: 'Punjab National Bank', icon: '🏛️' },
]

// Bill categories
const BILL_CATEGORIES = [
  { id: 'electricity', label: 'Electricity', icon: Lightbulb, sampleBiller: 'TNEB Tamil Nadu Electricity' },
  { id: 'mobile', label: 'Mobile Recharge', icon: Smartphone, sampleBiller: 'Jio Prepaid / Postpaid' },
  { id: 'broadband', label: 'Broadband / WiFi', icon: Wifi, sampleBiller: 'Airtel Xstream Fiber' },
  { id: 'dth', label: 'DTH / Cable TV', icon: Tv, sampleBiller: 'Tata Play DTH' },
  { id: 'gas', label: 'Piped Gas / Cylinders', icon: Flame, sampleBiller: 'Indane Gas Bharat Petroleum' },
  { id: 'water', label: 'Water Utility', icon: Droplets, sampleBiller: 'Chennai CMWSSB Water Board' },
]

export default function PaymentView({
  user,
  isAdmin,
  onViewExplanation,
  onNavigateToInvestigations,
  onSelectTransaction,
  initialPreset = 'scenario_monisha_safe',
}) {
  const isCustomer = user?.role?.toLowerCase() === 'customer' || user?.role?.toLowerCase() === 'user'
  const customerPersona = useMemo(() => getCustomerPersona(user), [user])

  // Active top navigation tab: 'gateway' | 'history'
  const [activeTab, setActiveTab] = useState('gateway')

  // Transfer Type Tab: 'merchant' | 'p2p' | 'bills' | 'self'
  const [transferType, setTransferType] = useState('merchant')

  // Payment Method Selector: 'upi' | 'credit_card' | 'debit_card' | 'net_banking' | 'wallet'
  const [paymentMethod, setPaymentMethod] = useState('upi')

  // Selected Debit Bank Account
  const [selectedBankId, setSelectedBankId] = useState('hdfc_primary')

  // Card details state
  const [cardNumber, setCardNumber] = useState('4532 •••• •••• 8819')
  const [cardExpiry, setCardExpiry] = useState('08/29')
  const [cardCvv, setCardCvv] = useState('412')
  const [cardHolder, setCardHolder] = useState(customerPersona.name || 'Monisha R')
  const [cardNetwork, setCardNetwork] = useState('VISA')

  // UPI ID state
  const [upiId, setUpiId] = useState(
    customerPersona.name?.toLowerCase().includes('monisha')
      ? 'monisha@okhdfcbank'
      : customerPersona.name?.toLowerCase().includes('mohana')
      ? 'mohana@icici'
      : 'customer@okaxis'
  )

  // NetBanking state
  const [selectedNetBank, setSelectedNetBank] = useState('HDFC')
  const [netBankUserId, setNetBankUserId] = useState(
    customerPersona.customerId ? `NB_${customerPersona.customerId}` : 'NB_992140'
  )

  // Direct Bank Transfer / P2P fields
  const [beneficiaryAccount, setBeneficiaryAccount] = useState('50100482910482')
  const [beneficiaryIfsc, setBeneficiaryIfsc] = useState('HDFC0000240')
  const [beneficiaryBankInfo, setBeneficiaryBankInfo] = useState('HDFC Bank, Anna Nagar, Chennai')
  const [transferRemarks, setTransferRemarks] = useState('Payment for retail purchase')

  // Bill payment state
  const [selectedBillCategory, setSelectedBillCategory] = useState('electricity')
  const [billerName, setBillerName] = useState('TNEB Tamil Nadu Electricity')
  const [consumerNumber, setConsumerNumber] = useState('04-129-883921')

  // Self Transfer destination account
  const [selfDestBankId, setSelfDestBankId] = useState('fraudlens_wallet')

  // Transaction PIN / MPIN field
  const [transactionPin, setTransactionPin] = useState('9214')
  const [showPin, setShowPin] = useState(false)

  // Digital Receipt Modal State
  const [receiptModalOpen, setReceiptModalOpen] = useState(false)
  const [receiptTx, setReceiptTx] = useState(null)

  // Recent Transaction History State
  const [recentTransactions, setRecentTransactions] = useState([])
  const [loadingHistory, setLoadingHistory] = useState(false)

  // Comprehensive Preset Scenarios
  const presets = [
    // Monisha (3% Safe Habitual)
    {
      id: 'scenario_monisha_safe',
      title: '1. Monisha: Habitual Grocery (₹1,250)',
      badge: 'MONISHA (3%) → SAFE ALLOW',
      badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
      description: 'Routine ₹1,250 grocery payment at NovaMart Fresh from trusted iPhone in Chennai. Clean baseline (3% fraud rate) -> Auto-Approved with Zero Friction.',
      data: {
        customer_id: 'CUST_MONISHA_001',
        amount: 1250.0,
        currency: 'INR',
        merchant_name: 'NovaMart Fresh',
        merchant_category: 'grocery',
        beneficiary_name: 'NovaMart Fresh',
        payment_method: 'upi',
        device_type: 'mobile_ios',
        location: 'Chennai',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },
    {
      id: 'scenario_monisha_coffee',
      title: 'Monisha: Cafe & Snacks (₹280)',
      badge: 'MONISHA → SAFE ALLOW',
      badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
      description: 'Daily ₹280 coffee & snacks at Blue Tokai Cafe via UPI QR code in Chennai -> Instant Auto-Approval.',
      data: {
        customer_id: 'CUST_MONISHA_001',
        amount: 280.0,
        currency: 'INR',
        merchant_name: 'Blue Tokai Coffee Roasters',
        merchant_category: 'dining',
        beneficiary_name: 'Blue Tokai Cafe',
        payment_method: 'upi',
        device_type: 'mobile_ios',
        location: 'Chennai',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },
    {
      id: 'scenario_monisha_swiggy',
      title: 'Monisha: Swiggy Dinner (₹650)',
      badge: 'MONISHA → SAFE ALLOW',
      badgeColor: 'bg-emerald-950/80 text-emerald-300 border-emerald-700/60',
      description: 'Dinner delivery ₹650 from Swiggy via HDFC Credit Card. Matches historic spending patterns -> Auto-Approved.',
      data: {
        customer_id: 'CUST_MONISHA_001',
        amount: 650.0,
        currency: 'INR',
        merchant_name: 'Swiggy Gourmet Orders',
        merchant_category: 'dining',
        beneficiary_name: 'Swiggy Bundl Tech',
        payment_method: 'credit_card',
        device_type: 'mobile_ios',
        location: 'Chennai',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },

    // Mohana (12% Elevated Velocity)
    {
      id: 'scenario_mohana_review',
      title: '2. Mohana: Suspicious Device & Region (₹14,500)',
      badge: 'MOHANA (12%) → STEP-UP OTP REVIEW',
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
      description: 'Moderate ₹14,500 electronics purchase via unfamiliar web browser with cross-city distance. Risk 45/100 -> Triggers Step-Up OTP Verification.',
      data: {
        customer_id: 'CUST_MOHANA_002',
        amount: 14500.0,
        currency: 'INR',
        merchant_name: 'CircuitBay Electronics',
        merchant_category: 'electronics',
        beneficiary_name: 'CircuitBay Electronics',
        payment_method: 'credit_card',
        device_type: 'web',
        location: 'Salem',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 1,
      },
    },
    {
      id: 'scenario_mohana_urgent_p2p',
      title: 'Mohana: Late-Night P2P Transfer (₹8,500)',
      badge: 'MOHANA → STEP-UP OTP',
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
      description: 'Urgent person-to-person transfer of ₹8,500 at 2:15 AM to unverified beneficiary -> Step-Up OTP triggered.',
      data: {
        customer_id: 'CUST_MOHANA_002',
        amount: 8500.0,
        currency: 'INR',
        merchant_name: 'P2P Transfer to Ananya K',
        merchant_category: 'retail',
        beneficiary_name: 'Ananya Krishnan (P2P)',
        payment_method: 'upi',
        device_type: 'mobile_android',
        location: 'Coimbatore',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 1,
      },
    },
    {
      id: 'scenario_mohana_voucher',
      title: 'Mohana: Gaming Voucher (₹18,000)',
      badge: 'MOHANA → STEP-UP OTP',
      badgeColor: 'bg-amber-950/80 text-amber-300 border-amber-700/60',
      description: 'Digital gift card ₹18,000 purchase on new website with high velocity -> Step-Up Security Check.',
      data: {
        customer_id: 'CUST_MOHANA_002',
        amount: 18000.0,
        currency: 'INR',
        merchant_name: 'GameZone Global Credits',
        merchant_category: 'retail',
        beneficiary_name: 'GameZone Digital Inc',
        payment_method: 'net_banking',
        device_type: 'web',
        location: 'Bangalore',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 1,
      },
    },

    // Sowmiya (26% Botnet ATO)
    {
      id: 'scenario_sowmiya_block',
      title: '3. Sowmiya: Botnet Account Takeover (₹75,000)',
      badge: 'SOWMIYA (26%) → CRITICAL BLOCK',
      badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
      description: 'High-value ₹75,000 gold jewellery attempt at 2:30 AM from automated bot emulator in Lagos with foreign IP proxy. Instant Pre-Auth Block!',
      data: {
        customer_id: 'CUST_SOWMIYA_003',
        amount: 75000.0,
        currency: 'INR',
        merchant_name: 'Aurelia Gold House',
        merchant_category: 'luxury_goods',
        beneficiary_name: 'Mule-Quick-Payout-99',
        payment_method: 'credit_card',
        device_type: 'unknown_bot',
        location: 'Lagos',
        transaction_country: 'NG',
        transaction_type: 'online_payment',
        failed_attempts: 3,
      },
    },
    {
      id: 'scenario_sowmiya_drain',
      title: 'Sowmiya: Rapid Account Drain (₹1,20,000)',
      badge: 'SOWMIYA → PRE-AUTH BLOCK',
      badgeColor: 'bg-rose-950/80 text-rose-300 border-rose-700/60',
      description: 'High velocity account drain attempt of ₹1,20,000 to offshore cryptocurrency exchange via Tor exit node -> Instant Block.',
      data: {
        customer_id: 'CUST_SOWMIYA_003',
        amount: 120000.0,
        currency: 'INR',
        merchant_name: 'CryptoXchange Global Ltd',
        merchant_category: 'crypto',
        beneficiary_name: 'Offshore Crypto Vault',
        payment_method: 'net_banking',
        device_type: 'unknown_bot',
        location: 'Dubai',
        transaction_country: 'AE',
        transaction_type: 'online_payment',
        failed_attempts: 4,
      },
    },

    // New User Cold Start
    {
      id: 'scenario_4_cold_start',
      title: '4. New Customer Cafe (₹250)',
      badge: 'NEW USER → SAFE ALLOW',
      badgeColor: 'bg-cyan-950/80 text-cyan-300 border-cyan-700/60',
      description: 'First-time user paying ₹250 for cafe dining in Delhi. Verifies that brand new customer accounts do not get false alarms.',
      data: {
        customer_id: 'CUST_MONISHA_001',
        amount: 250.0,
        currency: 'INR',
        merchant_name: 'GreenLeaf Wellness',
        merchant_category: 'dining',
        beneficiary_name: 'GreenLeaf Wellness',
        payment_method: 'upi',
        device_type: 'mobile_ios',
        location: 'Chennai',
        transaction_country: 'IN',
        transaction_type: 'online_payment',
        failed_attempts: 0,
      },
    },
  ]

  // Filter presets for customer
  const visiblePresets = useMemo(() => {
    if (!isCustomer) return presets
    const filtered = presets.filter((p) => p.data.customer_id === customerPersona.customerId)
    return filtered.length > 0 ? filtered : [presets[0]]
  }, [isCustomer, customerPersona.customerId, presets])

  // Master Merchants List for autocomplete
  const [merchantsList, setMerchantsList] = useState([])
  const [merchantSuggestions, setMerchantSuggestions] = useState([])
  const [showMerchantSuggestions, setShowMerchantSuggestions] = useState(false)
  const merchantBoxRef = useRef(null)

  useEffect(() => {
    const fetchMerchants = async () => {
      try {
        const token = localStorage.getItem('fraudlens_token')
        const res = await fetch('/api/v1/merchants', {
          headers: { Authorization: `Bearer ${token}` },
        })
        if (res.ok) {
          const data = await res.json()
          setMerchantsList(data.merchants || [])
        }
      } catch (err) {
        console.error('Failed to load merchants list for payment view:', err)
      }
    }
    fetchMerchants()
  }, [])

  // Close merchant autocomplete dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (merchantBoxRef.current && !merchantBoxRef.current.contains(e.target)) {
        setShowMerchantSuggestions(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const defaultPreset = useMemo(() => {
    if (isCustomer) {
      const match = presets.find((p) => p.data.customer_id === customerPersona.customerId)
      return match || presets[0]
    }
    const match = presets.find((p) => p.id === initialPreset)
    return match || presets[0]
  }, [isCustomer, customerPersona.customerId, initialPreset])

  const [activePreset, setActivePreset] = useState(defaultPreset.id)
  const [formData, setFormData] = useState(defaultPreset.data)
  const [showHelperGuide, setShowHelperGuide] = useState(true)

  // Wallet & Profile Data
  const [wallet, setWallet] = useState(null)
  const [walletLoading, setWalletLoading] = useState(false)
  const [pendingApprovals, setPendingApprovals] = useState([])

  // Pre-auth decision & approval state
  const [evaluating, setEvaluating] = useState(false)
  const [decisionResult, setDecisionResult] = useState(null)
  const [error, setError] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionSuccessMsg, setActionSuccessMsg] = useState(null)

  // Mobile Security Push Notification Phone Modal state
  const [showPhoneModal, setShowPhoneModal] = useState(false)
  const [phoneModalTx, setPhoneModalTx] = useState(null)
  const [phoneModalApprovalId, setPhoneModalApprovalId] = useState(null)

  // Load wallet & customer details
  const loadWallet = useCallback(async (customerId) => {
    if (!customerId) return
    setWalletLoading(true)
    try {
      const data = await paymentApi.getWallet(customerId)
      setWallet(data)
    } catch {
      setWallet(null)
    } finally {
      setWalletLoading(false)
    }
  }, [])

  // Load pending approvals (Monisha never has pending approvals or OTP)
  const loadPendingApprovals = useCallback(async (customerId) => {
    if (!customerId || customerId.toLowerCase().includes('monisha')) {
      setPendingApprovals([])
      return
    }
    try {
      const list = await paymentApi.listPendingApprovals(customerId)
      setPendingApprovals(list || [])
    } catch {
      setPendingApprovals([])
    }
  }, [])

  // Load Recent Transactions for the customer
  const loadRecentTransactions = useCallback(async (customerId) => {
    if (!customerId) return
    setLoadingHistory(true)
    try {
      const res = await transactionsApi.list({ customer_id: customerId, limit: 10 })
      if (res && res.transactions) {
        setRecentTransactions(res.transactions)
      }
    } catch (e) {
      console.warn('Failed to fetch recent transactions:', e)
    } finally {
      setLoadingHistory(false)
    }
  }, [])

  useEffect(() => {
    loadWallet(formData.customer_id)
    loadPendingApprovals(formData.customer_id)
    loadRecentTransactions(formData.customer_id)
  }, [formData.customer_id, loadWallet, loadPendingApprovals, loadRecentTransactions])

  useEffect(() => {
    if (isCustomer) {
      const match = presets.find((p) => p.data.customer_id === customerPersona.customerId)
      if (match) {
        setActivePreset(match.id)
        setFormData({ ...match.data, customer_id: customerPersona.customerId })
        setPaymentMethod(match.data.payment_method || 'upi')
        setDecisionResult(null)
        setError(null)
        setActionSuccessMsg(null)
      }
    } else if (initialPreset) {
      const match = presets.find((p) => p.id === initialPreset)
      if (match) {
        setActivePreset(match.id)
        setFormData(match.data)
        setPaymentMethod(match.data.payment_method || 'upi')
        setDecisionResult(null)
        setError(null)
        setActionSuccessMsg(null)
      }
    }
  }, [isCustomer, customerPersona.customerId, initialPreset])

  const handleMerchantNameChange = (text) => {
    handleInputChange('merchant_name', text)
    const query = text.trim().toLowerCase()
    if (query.length >= 1) {
      const matches = merchantsList.filter(
        (m) =>
          m.merchant_name?.toLowerCase().includes(query) ||
          m.merchant_id?.toLowerCase().includes(query) ||
          m.category?.toLowerCase().includes(query) ||
          m.city?.toLowerCase().includes(query)
      )
      setMerchantSuggestions(matches)
      setShowMerchantSuggestions(true)
    } else {
      setMerchantSuggestions(merchantsList)
      setShowMerchantSuggestions(true)
    }
  }

  const handleSelectMerchant = (m) => {
    let catVal = 'retail'
    const catLower = (m.category || '').toLowerCase()
    if (catLower.includes('grocery') || catLower.includes('supermarket')) catVal = 'grocery'
    else if (catLower.includes('dining') || catLower.includes('food')) catVal = 'dining'
    else if (catLower.includes('electronic')) catVal = 'electronics'
    else if (catLower.includes('jewel') || catLower.includes('gold')) catVal = 'luxury_goods'
    else if (catLower.includes('travel') || catLower.includes('flight')) catVal = 'travel'
    else if (catLower.includes('crypto') || catLower.includes('betting') || catLower.includes('rummy')) catVal = 'crypto'

    setFormData((prev) => ({
      ...prev,
      merchant_name: m.merchant_name,
      beneficiary_name: m.merchant_name,
      merchant_category: catVal,
    }))
    setShowMerchantSuggestions(false)
  }

  const handleSelectPreset = (preset) => {
    setActivePreset(preset.id)
    setFormData(preset.data)
    setPaymentMethod(preset.data.payment_method || 'upi')
    setDecisionResult(null)
    setError(null)
    setActionSuccessMsg(null)
  }

  const handleInputChange = (field, value) => {
    setFormData((prev) => {
      const updated = {
        ...prev,
        [field]: field === 'amount' || field === 'failed_attempts' ? (value === '' ? '' : Number(value)) : value,
      }
      if (field === 'merchant_name' && (!prev.beneficiary_name || prev.beneficiary_name === prev.merchant_name)) {
        updated.beneficiary_name = value
      }
      return updated
    })
    setActivePreset('custom')
  }

  const setPresetAmount = (amt) => {
    handleInputChange('amount', amt)
  }

  // Check if beneficiary is new for customer
  const isBeneficiaryNew = (name) => {
    if (!name || !wallet || !wallet.known_beneficiaries) return false
    const match = wallet.known_beneficiaries.some(
      (b) => b.beneficiary_name?.toLowerCase() === name.trim().toLowerCase()
    )
    return !match && wallet.total_transactions > 0
  }

  // Check if device is new for customer
  const isDeviceNew = (dev) => {
    if (!dev || !wallet || !wallet.known_devices) return false
    const match = wallet.known_devices.some((d) => d.toLowerCase() === dev.toLowerCase())
    return !match && wallet.total_transactions > 0
  }

  // Real-time Pre-Flight AI Risk Forecast (Live ML Fraud Score Predictor)
  const riskForecast = useMemo(() => {
    const amt = Number(formData.amount) || 0
    const cat = formData.merchant_category || 'retail'
    const dev = formData.device_type || 'mobile_ios'
    const country = formData.transaction_country || 'IN'
    const failed = Number(formData.failed_attempts) || 0
    const custId = (formData.customer_id || '').toLowerCase()

    let estimatedScore = 4
    const signals = []

    // Persona-baseline adjustment
    if (custId.includes('sowmiya')) {
      estimatedScore += 40
      signals.push('Sowmiya ATO baseline profile (26% risk history)')
    } else if (custId.includes('mohana')) {
      estimatedScore += 15
      signals.push('Mohana elevated velocity baseline (12% risk history)')
    } else {
      signals.push('Monisha clean habitual baseline (3% low-risk)')
    }

    // Amount thresholds
    if (amt >= 50000) {
      estimatedScore += 35
      signals.push(`High value ticket (₹${amt.toLocaleString('en-IN')})`)
    } else if (amt >= 10000) {
      estimatedScore += 18
      signals.push(`Moderate ticket value (₹${amt.toLocaleString('en-IN')})`)
    }

    // Category risk
    if (cat === 'luxury_goods' || cat === 'crypto') {
      estimatedScore += 30
      signals.push('High-risk category (Gold / Luxury / Crypto)')
    } else if (cat === 'electronics') {
      estimatedScore += 10
      signals.push('Consumer electronics category')
    }

    // Device risk
    if (dev === 'unknown_bot') {
      estimatedScore += 45
      signals.push('Automated bot emulator / Tor exit node')
    } else if (dev === 'web' || dev === 'web_browser') {
      estimatedScore += 8
      signals.push('Desktop web browser session')
    }

    // Cross-border check
    if (country !== 'IN') {
      estimatedScore += 40
      signals.push(`Cross-border international origin (${country})`)
    }

    // Failed authentication
    if (failed > 0) {
      estimatedScore += failed * 12
      signals.push(`${failed} failed PIN attempt(s)`)
    }

    const cappedScore = Math.min(Math.max(estimatedScore, 3), 98)
    const level = cappedScore <= 30 ? 'LOW' : cappedScore <= 70 ? 'MEDIUM' : 'HIGH'
    const color = level === 'LOW' ? 'emerald' : level === 'MEDIUM' ? 'amber' : 'rose'
    const estimatedProb = (cappedScore / 100).toFixed(2)

    return { score: cappedScore, level, color, signals, estimatedProb }
  }, [formData])

  // Handle Form Submission / Payment Initiation
  const handleInitiatePayment = async (e) => {
    e.preventDefault()
    setEvaluating(true)
    setError(null)
    setDecisionResult(null)
    setActionSuccessMsg(null)

    // Normalize device_type for backend enum
    let normalizedDevice = formData.device_type
    if (normalizedDevice === 'web_browser') normalizedDevice = 'web'

    // Determine final merchant/beneficiary based on transfer type
    let finalMerchantName = formData.merchant_name || 'NovaMart Fresh'
    let finalCategory = formData.merchant_category || 'retail'

    if (transferType === 'bills') {
      finalMerchantName = billerName
      finalCategory = 'utilities'
    } else if (transferType === 'p2p') {
      finalMerchantName = formData.beneficiary_name || 'Direct P2P Transfer'
      finalCategory = 'retail'
    } else if (transferType === 'self') {
      const destBank = LINKED_BANK_ACCOUNTS.find((b) => b.id === selfDestBankId)
      finalMerchantName = `Self Transfer -> ${destBank?.bankName || 'FraudLens Wallet'}`
      finalCategory = 'retail'
    }

    const payload = {
      customer_id: formData.customer_id,
      amount: Number(formData.amount),
      currency: formData.currency || 'INR',
      merchant_name: finalMerchantName,
      merchant_category: finalCategory,
      payment_method: paymentMethod,
      device_type: normalizedDevice,
      location: formData.location || 'Chennai',
      transaction_country: formData.transaction_country || 'IN',
      transaction_type: formData.transaction_type || 'online_payment',
      beneficiary_name: finalMerchantName,
      beneficiary_account: transferType === 'p2p' ? beneficiaryAccount : undefined,
      failed_attempts: Number(formData.failed_attempts) || 0,
      notes: transferRemarks,
    }

    try {
      const result = await paymentApi.initiate(payload)
      setDecisionResult(result)
      loadWallet(formData.customer_id)
      loadPendingApprovals(formData.customer_id)
      loadRecentTransactions(formData.customer_id)

      // Monisha is a safe habitual consumer (3% baseline) with ZERO friction -> NEVER pop up OTP modal
      const isMonisha = (formData.customer_id || '').toLowerCase().includes('monisha')

      // When step-up review is detected for elevated cases (e.g. Mohana), pop up Mobile Phone Push Notification Modal
      if (
        !isMonisha &&
        (result.decision === 'REVIEW' ||
          result.verification_required ||
          (result.decision === 'BLOCK' && result.approval_id))
      ) {
        setPhoneModalTx({
          ...formData,
          merchant_name: finalMerchantName,
          amount: result.amount || formData.amount,
          risk_score: result.risk_score,
          risk_level: result.risk_level,
          fraud_probability: result.fraud_probability,
          otp_code: result.otp_code,
          rule_triggered:
            result.triggered_rules?.[0]?.rule_name || 'Behavioral Risk Anomaly Detected',
        })
        setPhoneModalApprovalId(result.approval_id || null)
        setShowPhoneModal(true)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Transaction evaluation failed')
    } finally {
      setEvaluating(false)
    }
  }

  // Execute Step-Up Approval / Rejection with strict real OTP response matching
  const handleApprovalAction = async (approvalId, action, challengeResponse = '') => {
    if (!approvalId || approvalId === 'PEND_DEMO_01' || approvalId.startsWith('DEMO_')) {
      setActionSuccessMsg(
        action === 'APPROVE'
          ? `Demo Transaction authorized successfully via SMS OTP (${challengeResponse || '921457'}).`
          : 'Demo Transaction blocked and card frozen.'
      )
      loadWallet(formData.customer_id)
      return
    }
    setActionLoading(true)
    setError(null)
    try {
      const res = await paymentApi.processApproval(approvalId, {
        action,
        challenge_response: challengeResponse,
        notes: challengeResponse ? `Customer verified via real mobile OTP: ${challengeResponse}` : '',
      })
      setActionSuccessMsg(res.message || `Transaction ${action} successfully.`)

      if (decisionResult && decisionResult.approval_id === approvalId) {
        setDecisionResult((prev) => ({
          ...prev,
          lifecycle_status: res.lifecycle_status,
          decision: action === 'APPROVE' ? 'ALLOW' : 'BLOCK',
          status_message: res.message,
          verification_required: false,
          simulated_balance_after:
            res.simulated_balance !== null ? res.simulated_balance : prev.simulated_balance_after,
        }))
      }

      loadWallet(formData.customer_id)
      loadPendingApprovals(formData.customer_id)
      loadRecentTransactions(formData.customer_id)
    } catch (err) {
      setError(err instanceof Error ? err.message : `Failed to ${action.toLowerCase()} transaction`)
    } finally {
      setActionLoading(false)
    }
  }

  const selectedBank = LINKED_BANK_ACCOUNTS.find((b) => b.id === selectedBankId) || LINKED_BANK_ACCOUNTS[0]

  return (
    <div className="space-y-6">
      {/* Top Banner & Wallet Status Bar in INR */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 bg-gradient-to-r from-slate-900 via-slate-900/95 to-cyan-950/50 p-6 rounded-2xl border border-slate-800 shadow-xl relative overflow-hidden">
        <div className="absolute right-0 top-0 w-96 h-full bg-cyan-500/5 blur-3xl pointer-events-none" />
        <div className="flex items-center gap-4 relative z-10">
          <div className="p-3.5 bg-gradient-to-tr from-cyan-600 to-blue-600 rounded-2xl shadow-lg shadow-cyan-500/20 text-white">
            <CreditCard className="w-7 h-7" />
          </div>
          <div>
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="text-xl font-bold text-white tracking-wide">
                Real-Time Pre-Auth Payment Gateway
              </h1>
              <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-cyan-950 text-cyan-300 border border-cyan-700">
                REAL-TIME PRE-AUTH AI
              </span>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-bold bg-emerald-950 text-emerald-300 border border-emerald-800">
                INR (₹) LIVE
              </span>
              <ContextualModuleHelp moduleKey="payment" />
            </div>
            <p className="text-xs text-slate-300 mt-1 max-w-2xl">
              {isCustomer ? (
                <>
                  Live multi-channel payment engine with instant pre-authorization fraud evaluation and pre-decision security protection for{' '}
                  <strong className="text-emerald-300">{customerPersona.name}</strong>.
                </>
              ) : (
                <>
                  Live multi-channel payment engine with instant pre-authorization fraud evaluation and real-time defense. Pre-decision protection stops fraud before funds transfer.
                </>
              )}
            </p>
          </div>
        </div>

        {/* Live Balance Summary & Mobile Demo Push Button */}
        <div className="flex flex-wrap items-center gap-3 relative z-10">
          <button
            type="button"
            onClick={() => {
              setPhoneModalTx({
                amount: formData.amount || 14500,
                merchant_name: formData.merchant_name || 'CircuitBay Electronics',
                customer_id: formData.customer_id,
                location: formData.location || 'Salem (Cross-City Anomaly)',
                device: formData.device_type || 'Unrecognized Web Browser',
                risk_score: decisionResult?.risk_score || 45,
                risk_level: decisionResult?.risk_level || 'MEDIUM',
                fraud_probability: decisionResult?.fraud_probability || 0.45,
                rule_triggered: 'Suspicious Geo-Velocity & Step-Up Check',
              })
              setPhoneModalApprovalId(decisionResult?.approval_id || 'PEND_DEMO_01')
              setShowPhoneModal(true)
            }}
            className="px-3.5 py-2 rounded-xl bg-gradient-to-r from-purple-600 via-indigo-600 to-cyan-600 hover:from-purple-500 hover:to-cyan-500 text-white font-bold text-xs shadow-lg shadow-purple-950/60 border border-purple-400/40 flex items-center gap-2 transition active:scale-95"
            title="Demonstrate mobile lockscreen push notification & approval flow"
          >
            <Smartphone className="w-4 h-4 text-cyan-300 animate-pulse" />
            <span>📱 Phone Push Alert (Demo)</span>
          </button>

          <div className="flex items-center gap-3 bg-slate-950/90 px-4 py-2.5 rounded-xl border border-slate-800 text-xs font-mono">
            <Wallet className="w-5 h-5 text-emerald-400 shrink-0" />
            <div>
              <div className="text-[10px] text-slate-400 uppercase font-semibold">
                Available Balance
              </div>
              <div className="text-base font-extrabold text-white">
                <span className="text-emerald-400">
                  {formatINR(wallet ? wallet.simulated_balance : selectedBank.balance)}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Top Navigation: Make Payment vs Recent History & Receipts */}
      <div className="flex items-center justify-between border-b border-slate-800/80 pb-3">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setActiveTab('gateway')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'gateway'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                : 'text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent'
            }`}
          >
            <CreditCard className="w-4 h-4" />
            <span>Pay &amp; Transfer</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setActiveTab('history')
              loadRecentTransactions(formData.customer_id)
            }}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold transition-all ${
              activeTab === 'history'
                ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 shadow-[0_0_15px_rgba(6,182,212,0.2)]'
                : 'text-slate-400 hover:text-white hover:bg-slate-900 border border-transparent'
            }`}
          >
            <History className="w-4 h-4" />
            <span>Recent Payments &amp; Receipts ({recentTransactions.length})</span>
          </button>
        </div>

        {/* Active Authenticated Persona Badge */}
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-mono text-slate-400 uppercase">Authenticated As:</span>
          <span className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${customerPersona.badgeColor}`}>
            👤 {customerPersona.name} ({customerPersona.fraudRate})
          </span>
        </div>
      </div>

      {/* TAB 1: PAY & TRANSFER GATEWAY */}
      {activeTab === 'gateway' && (
        <div className="space-y-6">

          {/* Preset Scenario Selector Buttons */}
          <div className="space-y-1.5">
            <div className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <Zap className="w-3.5 h-3.5 text-cyan-400" />
                <span>
                  {isCustomer
                    ? `1-Click Payment Scenarios for ${customerPersona.name}:`
                    : 'Select a 1-Click Test Scenario (All 3 Personas Available):'}
                </span>
              </div>
              {isCustomer && (
                <span className="text-[10px] font-mono text-emerald-400">
                  🔒 Filtered to your customer baseline
                </span>
              )}
            </div>
            <div
              className={`grid grid-cols-1 gap-3 ${
                visiblePresets.length === 1
                  ? 'sm:grid-cols-1'
                  : visiblePresets.length === 2
                  ? 'sm:grid-cols-2'
                  : visiblePresets.length === 3
                  ? 'sm:grid-cols-3'
                  : 'sm:grid-cols-2 lg:grid-cols-4'
              }`}
            >
              {visiblePresets.map((preset) => {
                const isSelected = activePreset === preset.id
                return (
                  <button
                    key={preset.id}
                    type="button"
                    onClick={() => handleSelectPreset(preset)}
                    className={`text-left p-3.5 rounded-xl border transition-all duration-200 relative ${
                      isSelected
                        ? 'bg-slate-900/90 border-cyan-500/80 shadow-lg shadow-cyan-950/50 ring-1 ring-cyan-500/40'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-900/40'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-xs font-bold text-slate-200">{preset.title}</span>
                      <span
                        className={`text-[9px] font-mono px-1.5 py-0.5 rounded border font-semibold ${preset.badgeColor}`}
                      >
                        {preset.badge}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2">
                      {preset.description}
                    </p>
                  </button>
                )
              })}
            </div>
          </div>

          {/* MAIN CHECKOUT GRID: Left (Form + Instruments) | Right (Debit Account + Virtual Card + Live Risk Meter) */}
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* LEFT COLUMN: Payment Formulation & Methods (7 cols) */}
            <div className="lg:col-span-7 bg-slate-900/70 border border-slate-800/80 backdrop-blur-md rounded-2xl p-6 shadow-xl space-y-5">
              {/* Transfer Mode Tabs */}
              <div>
                <label className="block text-[11px] font-mono uppercase font-bold text-slate-400 mb-2">
                  Select Transfer Category:
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                  <button
                    type="button"
                    onClick={() => setTransferType('merchant')}
                    className={`p-2.5 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      transferType === 'merchant'
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/60 shadow-[0_0_12px_rgba(6,182,212,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Store className="w-4 h-4" />
                    <span>Merchant Pay</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setTransferType('p2p')}
                    className={`p-2.5 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      transferType === 'p2p'
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/60 shadow-[0_0_12px_rgba(6,182,212,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Send className="w-4 h-4" />
                    <span>Person-to-Person</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setTransferType('bills')}
                    className={`p-2.5 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      transferType === 'bills'
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/60 shadow-[0_0_12px_rgba(6,182,212,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Zap className="w-4 h-4" />
                    <span>Bill Payment</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => setTransferType('self')}
                    className={`p-2.5 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      transferType === 'self'
                        ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/60 shadow-[0_0_12px_rgba(6,182,212,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Building2 className="w-4 h-4" />
                    <span>Self / Topup</span>
                  </button>
                </div>
              </div>

              {/* Payment Method Selector Tabs */}
              <div>
                <label className="block text-[11px] font-mono uppercase font-bold text-slate-400 mb-2">
                  Payment Instrument (Select Method):
                </label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
                  <button
                    type="button"
                    onClick={() => {
                      setPaymentMethod('upi')
                      handleInputChange('payment_method', 'upi')
                    }}
                    className={`p-2 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      paymentMethod === 'upi'
                        ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/60 shadow-[0_0_12px_rgba(16,185,129,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Smartphone className="w-4 h-4 text-emerald-400" />
                    <span>UPI / QR</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setPaymentMethod('credit_card')
                      handleInputChange('payment_method', 'credit_card')
                    }}
                    className={`p-2 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      paymentMethod === 'credit_card'
                        ? 'bg-indigo-500/20 text-indigo-300 border-indigo-500/60 shadow-[0_0_12px_rgba(99,102,241,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <CreditCard className="w-4 h-4 text-indigo-400" />
                    <span>Credit Card</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setPaymentMethod('debit_card')
                      handleInputChange('payment_method', 'debit_card')
                    }}
                    className={`p-2 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      paymentMethod === 'debit_card'
                        ? 'bg-blue-500/20 text-blue-300 border-blue-500/60 shadow-[0_0_12px_rgba(59,130,246,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <CreditCard className="w-4 h-4 text-blue-400" />
                    <span>Debit Card</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setPaymentMethod('net_banking')
                      handleInputChange('payment_method', 'net_banking')
                    }}
                    className={`p-2 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      paymentMethod === 'net_banking'
                        ? 'bg-purple-500/20 text-purple-300 border-purple-500/60 shadow-[0_0_12px_rgba(168,85,247,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Building2 className="w-4 h-4 text-purple-400" />
                    <span>Net Banking</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => {
                      setPaymentMethod('wallet')
                      handleInputChange('payment_method', 'wallet')
                    }}
                    className={`p-2 rounded-xl border text-xs font-bold flex flex-col items-center gap-1 transition ${
                      paymentMethod === 'wallet'
                        ? 'bg-amber-500/20 text-amber-300 border-amber-500/60 shadow-[0_0_12px_rgba(245,158,11,0.25)]'
                        : 'bg-slate-950/60 text-slate-400 border-slate-800 hover:text-white'
                    }`}
                  >
                    <Wallet className="w-4 h-4 text-amber-400" />
                    <span>Wallet</span>
                  </button>
                </div>
              </div>

              {/* Main Checkout Form */}
              <form onSubmit={handleInitiatePayment} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {/* Amount (₹ INR) */}
                  <div className="sm:col-span-2">
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-xs font-bold text-slate-200">
                        Transfer Amount (₹ INR)
                      </label>
                      <span className="text-[10px] font-mono text-emerald-400 font-bold">
                        Avail in {selectedBank.bankName}: {formatINR(selectedBank.balance)}
                      </span>
                    </div>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-cyan-400 text-sm font-bold">
                        ₹
                      </div>
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        required
                        value={formData.amount}
                        onChange={(e) => handleInputChange('amount', e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-9 pr-4 py-2.5 text-sm text-white focus:outline-none focus:border-cyan-500 transition font-mono font-extrabold"
                        placeholder="0.00"
                      />
                    </div>

                    {/* Quick Preset Amount Buttons */}
                    <div className="flex items-center gap-1.5 mt-2 overflow-x-auto pb-1">
                      <span className="text-[10px] text-slate-500 font-mono">Quick:</span>
                      {[250, 650, 1250, 8500, 14500, 75000].map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          onClick={() => setPresetAmount(amt)}
                          className="px-2 py-0.5 bg-slate-950 hover:bg-cyan-950/80 border border-slate-800 hover:border-cyan-600 text-[10px] text-slate-300 hover:text-cyan-300 rounded-lg font-mono transition shrink-0"
                        >
                          ₹{amt.toLocaleString('en-IN')}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* MODE 1: MERCHANT PAY RECIPIENT */}
                  {transferType === 'merchant' && (
                    <div className="sm:col-span-2 relative" ref={merchantBoxRef}>
                      <div className="flex items-center justify-between mb-1">
                        <label className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                          <span>Merchant / Recipient Name</span>
                        </label>
                        <div className="flex items-center gap-2">
                          {isBeneficiaryNew(formData.merchant_name) ? (
                            <span className="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded bg-amber-950 text-amber-300 border border-amber-800">
                              NEW BENEFICIARY (+RISK SIGNAL)
                            </span>
                          ) : (
                            <span className="text-[9px] font-mono text-emerald-400 font-bold">
                              KNOWN RECIPIENT
                            </span>
                          )}
                        </div>
                      </div>

                      {/* Dropdown with All 29 Registered Merchants */}
                      <div className="mb-2">
                        <select
                          id="recipient-dropdown-all-names"
                          value={
                            merchantsList.some((m) => m.merchant_name === formData.merchant_name)
                              ? formData.merchant_name
                              : formData.merchant_name
                              ? '__custom__'
                              : ''
                          }
                          onChange={(e) => {
                            const selectedVal = e.target.value
                            if (!selectedVal || selectedVal === '__custom__') return
                            const match = merchantsList.find((m) => m.merchant_name === selectedVal)
                            if (match) {
                              handleSelectMerchant(match)
                            } else {
                              handleMerchantNameChange(selectedVal)
                            }
                          }}
                          className="w-full bg-slate-950/90 border border-cyan-800/60 hover:border-cyan-500 rounded-xl px-3 py-2 text-xs text-cyan-200 font-mono focus:outline-none focus:ring-1 focus:ring-cyan-500 transition shadow-inner cursor-pointer"
                        >
                          <option value="">
                            ▼ Select merchant ({merchantsList.length} available)...
                          </option>
                          <optgroup label="🏢 Registered Canonical Merchants">
                            {merchantsList.map((m) => (
                              <option key={m.merchant_id || m.merchant_name} value={m.merchant_name}>
                                {m.merchant_id ? `[${m.merchant_id}] ` : ''}
                                {m.merchant_name} • {m.category || 'Retail'} ({m.city || 'India'})
                              </option>
                            ))}
                          </optgroup>
                          <option value="__custom__">
                            ✏️ Custom / Other Merchant (Type below)...
                          </option>
                        </select>
                      </div>

                      <div className="relative">
                        <input
                          type="text"
                          required
                          value={formData.merchant_name}
                          onChange={(e) => handleMerchantNameChange(e.target.value)}
                          onFocus={() => handleMerchantNameChange(formData.merchant_name || '')}
                          className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-3.5 pr-16 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono"
                          placeholder="Selected merchant appears here..."
                        />
                      </div>
                    </div>
                  )}

                  {/* MODE 2: PERSON-TO-PERSON (P2P) */}
                  {transferType === 'p2p' && (
                    <div className="sm:col-span-2 space-y-3 p-3 bg-slate-950/80 rounded-xl border border-cyan-800/40">
                      <div className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                        <Users className="w-3.5 h-3.5" />
                        <span>Direct Person-to-Person Beneficiary Details</span>
                      </div>
                      <div>
                        <label className="block text-[10px] text-slate-400 mb-0.5">Beneficiary Full Name</label>
                        <input
                          type="text"
                          required
                          value={formData.beneficiary_name || ''}
                          onChange={(e) => {
                            handleInputChange('beneficiary_name', e.target.value)
                            handleInputChange('merchant_name', e.target.value)
                          }}
                          className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono"
                          placeholder="e.g. Ananya Krishnan"
                        />
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-0.5">
                            Bank Account Number
                          </label>
                          <input
                            type="text"
                            value={beneficiaryAccount}
                            onChange={(e) => setBeneficiaryAccount(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono"
                            placeholder="50100482910482"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-0.5">
                            Bank IFSC Code
                          </label>
                          <input
                            type="text"
                            value={beneficiaryIfsc}
                            onChange={(e) => setBeneficiaryIfsc(e.target.value.toUpperCase())}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-cyan-300 font-mono uppercase"
                            placeholder="HDFC0000240"
                          />
                        </div>
                      </div>
                      <div className="text-[10px] font-mono text-slate-400 bg-slate-900/60 p-1.5 rounded border border-slate-800">
                        📍 Auto-Detected Branch: <span className="text-cyan-300">{beneficiaryBankInfo}</span>
                      </div>
                    </div>
                  )}

                  {/* MODE 3: BILL PAYMENT */}
                  {transferType === 'bills' && (
                    <div className="sm:col-span-2 space-y-3 p-3 bg-slate-950/80 rounded-xl border border-cyan-800/40">
                      <div className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                        <Zap className="w-3.5 h-3.5" />
                        <span>Select Utility Biller &amp; Account Number</span>
                      </div>
                      <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
                        {BILL_CATEGORIES.map((cat) => {
                          const IconComp = cat.icon
                          return (
                            <button
                              key={cat.id}
                              type="button"
                              onClick={() => {
                                setSelectedBillCategory(cat.id)
                                setBillerName(cat.sampleBiller)
                                handleInputChange('merchant_name', cat.sampleBiller)
                                handleInputChange('merchant_category', 'utilities')
                              }}
                              className={`p-2 rounded-lg border text-center transition flex flex-col items-center gap-1 ${
                                selectedBillCategory === cat.id
                                  ? 'bg-cyan-500/20 border-cyan-500 text-cyan-300'
                                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-white'
                              }`}
                            >
                              <IconComp className="w-4 h-4" />
                              <span className="text-[9px] font-mono leading-tight">{cat.label}</span>
                            </button>
                          )
                        })}
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-0.5">Biller Provider</label>
                          <input
                            type="text"
                            value={billerName}
                            onChange={(e) => {
                              setBillerName(e.target.value)
                              handleInputChange('merchant_name', e.target.value)
                            }}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-0.5">Consumer / Account ID</label>
                          <input
                            type="text"
                            value={consumerNumber}
                            onChange={(e) => setConsumerNumber(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* MODE 4: SELF TRANSFER / WALLET TOPUP */}
                  {transferType === 'self' && (
                    <div className="sm:col-span-2 space-y-3 p-3 bg-slate-950/80 rounded-xl border border-cyan-800/40">
                      <div className="text-xs font-bold text-cyan-300 flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5" />
                        <span>Self Transfer Destination (Transfer To)</span>
                      </div>
                      <select
                        value={selfDestBankId}
                        onChange={(e) => setSelfDestBankId(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-emerald-300 font-mono"
                      >
                        {LINKED_BANK_ACCOUNTS.filter((b) => b.id !== selectedBankId).map((bank) => (
                          <option key={bank.id} value={bank.id}>
                            {bank.bankName} ({bank.accountNumberMasked}) • Avail: {formatINR(bank.balance)}
                          </option>
                        ))}
                      </select>
                    </div>
                  )}

                  {/* DYNAMIC PAYMENT INSTRUMENT INPUTS */}
                  {/* UPI Inputs */}
                  {paymentMethod === 'upi' && (
                    <div className="sm:col-span-2 space-y-2 p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                      <div className="flex items-center justify-between">
                        <label className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
                          <Smartphone className="w-3.5 h-3.5" />
                          <span>Customer VPA / UPI ID</span>
                        </label>
                        <span className="text-[10px] font-mono text-slate-400">NPCI Verified</span>
                      </div>
                      <input
                        type="text"
                        value={upiId}
                        onChange={(e) => setUpiId(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-2 text-xs text-emerald-300 font-mono focus:outline-none focus:border-emerald-500"
                        placeholder="username@okhdfcbank"
                      />
                      <div className="flex items-center gap-1.5 flex-wrap">
                        {['@okhdfcbank', '@oksbi', '@icici', '@paytm', '@okaxis'].map((suffix) => (
                          <button
                            key={suffix}
                            type="button"
                            onClick={() => {
                              const prefix = upiId.split('@')[0] || customerPersona.name.toLowerCase()
                              setUpiId(`${prefix}${suffix}`)
                            }}
                            className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-900 text-slate-300 hover:text-emerald-400 border border-slate-700"
                          >
                            {suffix}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Card Inputs */}
                  {(paymentMethod === 'credit_card' || paymentMethod === 'debit_card') && (
                    <div className="sm:col-span-2 space-y-3 p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                      <div className="flex items-center justify-between">
                        <span className="text-xs font-bold text-indigo-300 flex items-center gap-1.5">
                          <CreditCard className="w-3.5 h-3.5" />
                          <span>Card Credentials</span>
                        </span>
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            onClick={() => setCardNetwork('VISA')}
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                              cardNetwork === 'VISA'
                                ? 'bg-blue-600 text-white'
                                : 'bg-slate-900 text-slate-400'
                            }`}
                          >
                            VISA
                          </button>
                          <button
                            type="button"
                            onClick={() => setCardNetwork('MASTERCARD')}
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                              cardNetwork === 'MASTERCARD'
                                ? 'bg-red-600 text-white'
                                : 'bg-slate-900 text-slate-400'
                            }`}
                          >
                            MC
                          </button>
                          <button
                            type="button"
                            onClick={() => setCardNetwork('RUPAY')}
                            className={`text-[9px] font-bold px-1.5 py-0.5 rounded ${
                              cardNetwork === 'RUPAY'
                                ? 'bg-emerald-600 text-white'
                                : 'bg-slate-900 text-slate-400'
                            }`}
                          >
                            RuPay
                          </button>
                        </div>
                      </div>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                        <div className="sm:col-span-2">
                          <label className="block text-[10px] text-slate-400 mb-0.5">Card Number</label>
                          <input
                            type="text"
                            value={cardNumber}
                            onChange={(e) => setCardNumber(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-indigo-500"
                            placeholder="4532 •••• •••• 8819"
                          />
                        </div>
                        <div>
                          <label className="block text-[10px] text-slate-400 mb-0.5">Expiry</label>
                          <input
                            type="text"
                            maxLength={5}
                            value={cardExpiry}
                            onChange={(e) => setCardExpiry(e.target.value)}
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-white font-mono focus:outline-none focus:border-indigo-500 text-center"
                            placeholder="08/29"
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Net Banking Inputs */}
                  {paymentMethod === 'net_banking' && (
                    <div className="sm:col-span-2 space-y-2 p-3 bg-slate-950/80 rounded-xl border border-slate-800">
                      <label className="block text-xs font-bold text-purple-300">
                        Select NetBanking Portal:
                      </label>
                      <div className="grid grid-cols-3 sm:grid-cols-6 gap-1.5">
                        {NETBANKING_BANKS.map((b) => (
                          <button
                            key={b.code}
                            type="button"
                            onClick={() => setSelectedNetBank(b.code)}
                            className={`p-2 rounded-lg border text-center transition ${
                              selectedNetBank === b.code
                                ? 'bg-purple-900/60 border-purple-500 text-white'
                                : 'bg-slate-900 border-slate-700 text-slate-400 hover:text-white'
                            }`}
                          >
                            <div className="text-sm">{b.icon}</div>
                            <div className="text-[10px] font-bold font-mono mt-0.5">{b.code}</div>
                          </button>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Location & Country */}
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Origin City &amp; Country
                    </label>
                    <div className="grid grid-cols-2 gap-2">
                      <input
                        type="text"
                        value={formData.location}
                        onChange={(e) => handleInputChange('location', e.target.value)}
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono"
                        placeholder="City (Chennai/Mumbai)"
                      />
                      <input
                        type="text"
                        maxLength={2}
                        value={formData.transaction_country}
                        onChange={(e) =>
                          handleInputChange('transaction_country', e.target.value.toUpperCase())
                        }
                        className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition font-mono uppercase"
                        placeholder="Country (IN/AE/US)"
                      />
                    </div>
                  </div>

                  {/* Hardware Device */}
                  <div>
                    <label className="block text-xs font-medium text-slate-300 mb-1">
                      Client Hardware / Platform
                    </label>
                    <select
                      value={formData.device_type}
                      onChange={(e) => handleInputChange('device_type', e.target.value)}
                      className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2 text-xs text-white focus:outline-none focus:border-cyan-500 transition"
                    >
                      <option value="mobile_ios">iOS Mobile App (iPhone - Trusted)</option>
                      <option value="mobile_android">Android UPI App (GPay / PhonePe)</option>
                      <option value="web">Web Browser (Desktop Chrome)</option>
                      <option value="pos">In-Person POS Terminal</option>
                      <option value="unknown_bot">Automated Bot / Tor Proxy (High Risk)</option>
                    </select>
                  </div>

                  {/* Transaction PIN / Password Field */}
                  <div className="sm:col-span-2 p-3 bg-slate-950/90 rounded-xl border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <label className="text-xs font-bold text-slate-200 flex items-center gap-1.5">
                        <KeyRound className="w-4 h-4 text-cyan-400" />
                        <span>Security PIN / Transaction Password</span>
                      </label>
                      <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1">
                        <Lock className="w-2.5 h-2.5" /> 256-Bit Banking AES Encrypted
                      </span>
                    </div>
                    <div className="relative">
                      <input
                        type={showPin ? 'text' : 'password'}
                        maxLength={6}
                        required
                        value={transactionPin}
                        onChange={(e) => setTransactionPin(e.target.value)}
                        className="w-full bg-slate-900 border border-slate-700 focus:border-cyan-400 rounded-xl pl-4 pr-10 py-2 text-sm text-white font-mono tracking-widest text-center"
                        placeholder="••••"
                      />
                      <button
                        type="button"
                        onClick={() => setShowPin(!showPin)}
                        className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-200 transition"
                        title={showPin ? 'Hide PIN' : 'Show PIN'}
                      >
                        {showPin ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Error Banner */}
                {error && (
                  <div className="p-3.5 bg-rose-950/80 border border-rose-800/80 rounded-xl text-rose-300 text-xs flex items-center gap-2">
                    <XCircle className="w-4 h-4 shrink-0 text-rose-400" />
                    <span>{error}</span>
                  </div>
                )}

                {/* Success Banner */}
                {actionSuccessMsg && (
                  <div className="p-3.5 bg-emerald-950/80 border border-emerald-800/80 rounded-xl text-emerald-300 text-xs flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-400" />
                    <span>{actionSuccessMsg}</span>
                  </div>
                )}

                {/* Submit Button */}
                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={evaluating || actionLoading}
                    className="w-full py-3.5 px-6 bg-gradient-to-r from-cyan-600 via-blue-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg shadow-cyan-900/30 flex items-center justify-center gap-2 transition duration-200 disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    {evaluating ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Evaluating AI Risk &amp; Pre-Auth Rules...</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-4 h-4" />
                        <span>PAY &amp; AUTHORIZE (₹{Number(formData.amount || 0).toLocaleString('en-IN')})</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            </div>

            {/* RIGHT COLUMN: Debit Bank Selector + Realistic 3D Virtual Card + Real-time Risk Preview (5 cols) */}
            <div className="lg:col-span-5 space-y-5">
              {/* Debit Account Selector */}
              <div className="bg-slate-900/70 border border-slate-800/80 backdrop-blur-md rounded-2xl p-4 shadow-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-cyan-400" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                      Debit Account (Pay From)
                    </h3>
                  </div>
                  <span className="text-[10px] font-mono text-slate-400">
                    {LINKED_BANK_ACCOUNTS.length} Accounts Linked
                  </span>
                </div>

                <div className="space-y-2">
                  {LINKED_BANK_ACCOUNTS.map((bank) => {
                    const isSelected = selectedBankId === bank.id
                    return (
                      <button
                        key={bank.id}
                        type="button"
                        onClick={() => setSelectedBankId(bank.id)}
                        className={`w-full text-left p-2.5 rounded-xl border transition flex items-center justify-between ${
                          isSelected
                            ? 'bg-slate-950 border-cyan-500 ring-1 ring-cyan-500/40 shadow-md'
                            : 'bg-slate-950/60 border-slate-800/80 hover:border-slate-700'
                        }`}
                      >
                        <div className="flex items-center gap-2.5 min-w-0">
                          <div
                            className={`w-8 h-8 rounded-lg bg-gradient-to-tr ${bank.logoColor} flex items-center justify-center text-white text-xs font-bold shrink-0 shadow`}
                          >
                            {bank.bankName.slice(0, 2).toUpperCase()}
                          </div>
                          <div className="min-w-0">
                            <div className="flex items-center gap-1.5">
                              <span className="text-xs font-bold text-white font-mono truncate">
                                {bank.bankName}
                              </span>
                              {bank.isPrimary && (
                                <span className="text-[8px] font-mono px-1 py-0.2 rounded bg-cyan-950 text-cyan-300 border border-cyan-800">
                                  PRIMARY
                                </span>
                              )}
                            </div>
                            <div className="text-[10px] text-slate-400 font-mono">
                              {bank.accountNumberMasked} • {bank.branch}
                            </div>
                          </div>
                        </div>
                        <div className="text-right shrink-0">
                          <div className="text-xs font-bold text-emerald-400 font-mono flex items-center gap-1 justify-end">
                            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                            <span>Linked &amp; Active</span>
                          </div>
                          <div className="text-[9px] text-slate-500 font-mono">•••• •••• Verified</div>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </div>

              {/* Realistic Glassmorphism Virtual Card Display */}
              {(paymentMethod === 'credit_card' || paymentMethod === 'debit_card') && (
                <div className="p-5 rounded-2xl bg-gradient-to-tr from-slate-900 via-indigo-950 to-slate-900 border border-indigo-500/40 shadow-[0_0_25px_rgba(99,102,241,0.25)] relative overflow-hidden text-white space-y-4">
                  <div className="absolute top-0 right-0 w-48 h-48 bg-indigo-500/10 rounded-full blur-2xl pointer-events-none" />
                  <div className="flex items-center justify-between relative z-10">
                    <span className="text-[10px] font-mono tracking-widest text-indigo-300 font-bold uppercase">
                      FRAUDLENS SECURE {paymentMethod === 'credit_card' ? 'CREDIT' : 'DEBIT'}
                    </span>
                    <span className="text-sm font-extrabold tracking-wider font-mono text-cyan-300">
                      {cardNetwork}
                    </span>
                  </div>

                  <div className="flex items-center gap-3 relative z-10 my-2">
                    <div className="w-9 h-7 rounded-md bg-gradient-to-tr from-amber-300 to-amber-600 shadow-inner flex items-center justify-center text-[9px] font-mono font-bold text-amber-950">
                      CHIP
                    </div>
                    <Radio className="w-4 h-4 text-indigo-300 rotate-90" />
                  </div>

                  <div className="text-base sm:text-lg font-mono tracking-widest text-slate-100 font-bold relative z-10">
                    {cardNumber || '4532 •••• •••• 8819'}
                  </div>

                  <div className="flex items-center justify-between text-xs font-mono relative z-10 pt-1">
                    <div>
                      <div className="text-[8px] text-indigo-300 uppercase">Cardholder</div>
                      <div className="font-bold text-white uppercase">{cardHolder}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-[8px] text-indigo-300 uppercase">Expires</div>
                      <div className="font-bold text-white">{cardExpiry}</div>
                    </div>
                  </div>
                </div>
              )}

              {/* Real-Time Pre-Flight AI Risk Forecast Meter */}
              <div className="bg-slate-900/70 border border-slate-800/80 backdrop-blur-md rounded-2xl p-4 shadow-xl space-y-3">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <div className="flex items-center gap-1.5">
                    <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                    <h3 className="text-xs font-bold text-white uppercase tracking-wider">
                      Live Real-Time Fraud Score Meter
                    </h3>
                  </div>
                  <span
                    className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded border ${
                      riskForecast.level === 'LOW'
                        ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                        : riskForecast.level === 'MEDIUM'
                        ? 'bg-amber-950 text-amber-300 border-amber-800'
                        : 'bg-rose-950 text-rose-300 border-rose-800'
                    }`}
                  >
                    {riskForecast.level} RISK ({riskForecast.score}/100)
                  </span>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-400">Pre-Flight AI Fraud Likelihood:</span>
                    <span className="font-bold text-cyan-300">{(riskForecast.estimatedProb * 100).toFixed(0)}%</span>
                  </div>

                  <div className="w-full bg-slate-950 rounded-full h-2 overflow-hidden border border-slate-800">
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${
                        riskForecast.level === 'LOW'
                          ? 'bg-gradient-to-r from-emerald-500 to-cyan-500'
                          : riskForecast.level === 'MEDIUM'
                          ? 'bg-gradient-to-r from-amber-500 to-orange-500'
                          : 'bg-gradient-to-r from-rose-600 to-red-500'
                      }`}
                      style={{ width: `${riskForecast.score}%` }}
                    />
                  </div>

                  {/* Signals List */}
                  <div className="space-y-1 pt-1">
                    <div className="text-[10px] text-slate-500 uppercase font-mono">
                      Active Behavioral &amp; Network Signals:
                    </div>
                    {riskForecast.signals.map((sig, idx) => (
                      <div
                        key={idx}
                        className="text-[11px] text-slate-300 flex items-center gap-1.5 font-mono"
                      >
                        <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shrink-0" />
                        <span>{sig}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* AUTHORITATIVE PRE-AUTH DECISION OUTCOME CARD */}
          {decisionResult && (
            <div
              className={`p-6 rounded-2xl border transition-all duration-500 shadow-2xl space-y-6 ${
                decisionResult.decision === 'ALLOW'
                  ? 'bg-gradient-to-b from-slate-900 via-slate-900 to-emerald-950/40 border-emerald-700/60 shadow-emerald-950/30'
                  : decisionResult.decision === 'REVIEW'
                  ? 'bg-gradient-to-b from-slate-900 via-slate-900 to-amber-950/40 border-amber-700/60 shadow-amber-950/30'
                  : 'bg-gradient-to-b from-slate-900 via-slate-900 to-rose-950/40 border-rose-700/60 shadow-rose-950/30'
              }`}
            >
              {/* Decision Header */}
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-800 pb-5">
                <div className="flex items-center gap-4">
                  <div
                    className={`p-3.5 rounded-2xl text-white shadow-lg ${
                      decisionResult.decision === 'ALLOW'
                        ? 'bg-emerald-600 shadow-emerald-600/30'
                        : decisionResult.decision === 'REVIEW'
                        ? 'bg-amber-600 shadow-amber-600/30'
                        : 'bg-rose-600 shadow-rose-600/30'
                    }`}
                  >
                    {decisionResult.decision === 'ALLOW' && <CheckCircle2 className="w-8 h-8" />}
                    {decisionResult.decision === 'REVIEW' && <AlertTriangle className="w-8 h-8" />}
                    {decisionResult.decision === 'BLOCK' && <XCircle className="w-8 h-8" />}
                  </div>

                  <div>
                    <div className="flex items-center gap-2">
                      <h3 className="text-xl font-extrabold text-white tracking-wider">
                        {decisionResult.decision === 'ALLOW' && 'TRANSACTION AUTHORIZED & PROCEEDED'}
                        {decisionResult.decision === 'REVIEW' &&
                          'STEP-UP VERIFICATION REQUIRED (HELD)'}
                        {decisionResult.decision === 'BLOCK' && 'TRANSACTION PROHIBITED & BLOCKED'}
                      </h3>
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-xs font-mono font-bold border ${
                          decisionResult.decision === 'ALLOW'
                            ? 'bg-emerald-950 text-emerald-300 border-emerald-700'
                            : decisionResult.decision === 'REVIEW'
                            ? 'bg-amber-950 text-amber-300 border-amber-700'
                            : 'bg-rose-950 text-rose-300 border-rose-700'
                        }`}
                      >
                        {decisionResult.risk_level} RISK
                      </span>
                    </div>
                    <p className="text-xs text-slate-300 mt-1 font-medium">
                      {decisionResult.status_message}
                    </p>
                  </div>
                </div>

                {/* View Official Receipt Button */}
                <div className="flex flex-wrap items-center gap-3">
                  {decisionResult.decision === 'ALLOW' && (
                    <button
                      type="button"
                      onClick={() => {
                        setReceiptTx({
                          ...formData,
                          ...decisionResult,
                          timestamp: new Date().toISOString(),
                          debit_bank: selectedBank.bankName,
                          debit_account: selectedBank.accountNumberMasked,
                        })
                        setReceiptModalOpen(true)
                      }}
                      className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white rounded-xl text-xs font-bold uppercase tracking-wider shadow-lg flex items-center gap-2 transition"
                    >
                      <Receipt className="w-4 h-4" />
                      <span>View Official Digital Receipt</span>
                    </button>
                  )}

                  <div className="text-right font-mono">
                    <div className="text-[10px] text-slate-400 uppercase">Decision Speed</div>
                    <div className="text-xs font-bold text-white">
                      {decisionResult.processing_time_ms} ms
                    </div>
                  </div>
                </div>
              </div>

              {/* Metric Telemetry Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">
                    ML Fraud Likelihood
                  </div>
                  <div className="text-xl font-extrabold font-mono text-cyan-300 mt-1">
                    {(decisionResult.fraud_probability * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    Model: {decisionResult.model_name} ({decisionResult.model_version})
                  </div>
                </div>

                <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">
                    Independent Risk Score
                  </div>
                  <div className="text-xl font-extrabold font-mono text-white mt-1">
                    {decisionResult.risk_score} <span className="text-xs text-slate-500">/ 100</span>
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    Multi-Factor Metric (0–30 L / 31–70 M / 71–100 H)
                  </div>
                </div>

                <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">
                    Behavioral Deviation
                  </div>
                  <div className="text-xl font-extrabold font-mono text-purple-300 mt-1">
                    {(decisionResult.behavioural_deviation_score * 100).toFixed(0)}%
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    vs Customer Historical Baseline
                  </div>
                </div>

                <div className="p-4 bg-slate-950/80 rounded-xl border border-slate-800">
                  <div className="text-[10px] text-slate-400 font-mono uppercase">
                    Simulated Wallet Impact
                  </div>
                  <div className="text-base font-bold font-mono mt-1 text-emerald-400">
                    {formatINR(
                      decisionResult.simulated_balance_after !== null &&
                        decisionResult.simulated_balance_after !== undefined
                        ? decisionResult.simulated_balance_after
                        : wallet?.simulated_balance || 50000
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500 font-mono mt-0.5">
                    {decisionResult.decision === 'ALLOW'
                      ? 'Deducted on Success'
                      : 'Protected (Held / Untouched)'}
                  </div>
                </div>
              </div>

              {/* Triggered Rules Breakdown */}
              {decisionResult.triggered_rules && decisionResult.triggered_rules.length > 0 && (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-white uppercase tracking-wider flex items-center gap-2">
                    <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
                    <span>Triggered Security &amp; Anomaly Rules</span>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2.5">
                    {decisionResult.triggered_rules.map((rule, idx) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-950/90 rounded-xl border border-slate-800 text-xs space-y-1"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-bold text-slate-200">{rule.rule_name}</span>
                          <span
                            className={`text-[9px] font-mono px-1.5 py-0.2 rounded border font-bold ${
                              rule.severity === 'CRITICAL'
                                ? 'bg-rose-950 text-rose-300 border-rose-800'
                                : 'bg-amber-950 text-amber-300 border-amber-800'
                            }`}
                          >
                            {rule.severity}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-400">{rule.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: RECENT PAYMENTS & DIGITAL RECEIPTS */}
      {activeTab === 'history' && (
        <div className="bg-slate-900/70 border border-slate-800/80 backdrop-blur-md rounded-2xl p-6 shadow-xl space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-3">
            <div className="flex items-center gap-2">
              <History className="w-5 h-5 text-cyan-400" />
              <div>
                <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                  Payment History &amp; Official Receipts
                </h2>
                <p className="text-[11px] text-slate-400">
                  Showing authenticated transaction receipts for {customerPersona.name} ({customerPersona.customerId})
                </p>
              </div>
            </div>
            <button
              type="button"
              onClick={() => loadRecentTransactions(formData.customer_id)}
              disabled={loadingHistory}
              className="px-3 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold flex items-center gap-1.5 border border-slate-700"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${loadingHistory ? 'animate-spin' : ''}`} />
              <span>Refresh History</span>
            </button>
          </div>

          {loadingHistory ? (
            <div className="py-12 text-center text-xs text-slate-500 flex items-center justify-center gap-2">
              <RefreshCw className="w-4 h-4 animate-spin text-cyan-400" />
              <span>Fetching authenticated transaction ledger...</span>
            </div>
          ) : recentTransactions.length === 0 ? (
            <div className="py-12 text-center text-xs text-slate-400 space-y-2">
              <Receipt className="w-8 h-8 text-slate-600 mx-auto" />
              <div>No transactions recorded yet in this active session.</div>
              <button
                type="button"
                onClick={() => setActiveTab('gateway')}
                className="text-cyan-400 hover:underline font-bold"
              >
                Make a payment now &rarr;
              </button>
            </div>
          ) : (
            <div className="space-y-2.5">
              {recentTransactions.map((tx) => {
                const isAllow =
                  tx.decision === 'ALLOW' ||
                  tx.is_fraud === false ||
                  (tx.prediction !== 1 && (tx.risk_level === 'LOW' || !tx.risk_level))
                const isReview =
                  tx.decision === 'REVIEW' || tx.risk_level === 'MEDIUM'
                const isBlock =
                  tx.decision === 'BLOCK' || tx.is_fraud === true || tx.prediction === 1

                return (
                  <div
                    key={tx.transaction_id || tx.id}
                    className="p-4 bg-slate-950/80 rounded-xl border border-slate-800/80 hover:border-slate-700 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-10 h-10 rounded-xl flex items-center justify-center text-white shrink-0 ${
                          isAllow
                            ? 'bg-emerald-600/20 text-emerald-400 border border-emerald-600/40'
                            : isReview
                            ? 'bg-amber-600/20 text-amber-400 border border-amber-600/40'
                            : 'bg-rose-600/20 text-rose-400 border border-rose-600/40'
                        }`}
                      >
                        {isAllow ? (
                          <CheckCircle2 className="w-5 h-5" />
                        ) : isReview ? (
                          <AlertTriangle className="w-5 h-5" />
                        ) : (
                          <XCircle className="w-5 h-5" />
                        )}
                      </div>

                      <div>
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold text-white font-mono">
                            {tx.merchant_name || tx.merchant || 'Merchant Transfer'}
                          </span>
                          <span
                            className={`text-[9px] font-mono font-bold px-2 py-0.5 rounded border ${
                              isAllow
                                ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                                : isReview
                                ? 'bg-amber-950 text-amber-300 border-amber-800'
                                : 'bg-rose-950 text-rose-300 border-rose-800'
                            }`}
                          >
                            {isAllow ? 'AUTHORIZED' : isReview ? 'STEP-UP REVIEW' : 'BLOCKED'}
                          </span>
                        </div>
                        <div className="text-[11px] text-slate-400 flex items-center gap-2 mt-0.5 font-mono">
                          <span>{formatDateTime(tx.timestamp || tx.created_at)}</span>
                          <span>•</span>
                          <span className="uppercase">{tx.payment_method || 'UPI'}</span>
                          {tx.location && (
                            <>
                              <span>•</span>
                              <span>{tx.location}</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between sm:justify-end gap-4 shrink-0">
                      <div className="text-left sm:text-right">
                        <div className="text-sm font-extrabold text-white font-mono">
                          {formatINR(tx.amount)}
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono">
                          Ref: {(tx.transaction_id || tx.id || '').slice(0, 14)}
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => {
                          setReceiptTx({
                            ...tx,
                            debit_bank: selectedBank.bankName,
                            debit_account: selectedBank.accountNumberMasked,
                          })
                          setReceiptModalOpen(true)
                        }}
                        className="p-2 rounded-xl bg-slate-900 hover:bg-cyan-950 text-slate-300 hover:text-cyan-300 border border-slate-700 hover:border-cyan-600 transition flex items-center gap-1.5 text-xs font-bold"
                        title="View Official Receipt"
                      >
                        <Receipt className="w-4 h-4 text-cyan-400" />
                        <span>Receipt</span>
                      </button>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      )}

      {/* OFFICIAL DIGITAL RECEIPT SLIP MODAL */}
      {receiptModalOpen && receiptTx && (
        <GlobalCenterModal
          isOpen={receiptModalOpen && Boolean(receiptTx)}
          onClose={() => setReceiptModalOpen(false)}
          title="FRAUDLENS DIGITAL RECEIPT"
          subtitle={`TXN REF: ${(receiptTx.transaction_id || receiptTx.id || 'PAY-99214').slice(0, 16)}`}
          icon={ShieldCheck}
          badge="PRE-AUTH VERIFIED"
          badgeType="success"
          maxWidth="max-w-md"
          footer={
            <div className="grid grid-cols-2 gap-2 w-full">
              <button
                type="button"
                onClick={() => {
                  window.print()
                }}
                className="py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-bold transition flex items-center justify-center gap-1.5 border border-slate-700 cursor-pointer"
              >
                <Printer className="w-3.5 h-3.5" />
                <span>Print Receipt</span>
              </button>
              <button
                type="button"
                onClick={() => setReceiptModalOpen(false)}
                className="py-2.5 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-bold transition flex items-center justify-center gap-1.5 shadow-md shadow-cyan-900/50 cursor-pointer"
              >
                <Check className="w-3.5 h-3.5" />
                <span>Done</span>
              </button>
            </div>
          }
        >
          {/* Receipt Body */}
          <div className="space-y-3 bg-slate-900/90 p-4 rounded-2xl border border-slate-800 text-xs font-mono">
            <div className="text-center py-2 border-b border-slate-800">
              <div className="text-[10px] text-slate-400 uppercase">Paid Monetary Amount</div>
              <div className="text-2xl font-black text-emerald-400 mt-0.5">
                {formatINR(receiptTx.amount)}
              </div>
              <div className="text-[10px] text-emerald-300 font-bold mt-1 flex items-center justify-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>PRE-AUTH VERIFIED &amp; TRANSFERRED</span>
              </div>
            </div>

            <div className="space-y-1.5 pt-1">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Paid To:</span>
                <span className="font-bold text-white">
                  {receiptTx.merchant_name || receiptTx.merchant || 'Recipient'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Customer Name:</span>
                <span className="text-slate-200">{customerPersona.name}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Debited Account:</span>
                <span className="text-slate-200">
                  {receiptTx.debit_bank || 'HDFC Bank'} ({receiptTx.debit_account || '•••• 4821'})
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Payment Instrument:</span>
                <span className="text-cyan-300 uppercase">
                  {receiptTx.payment_method || 'UPI Transfer'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Date &amp; Timestamp:</span>
                <span className="text-slate-300">
                  {formatDateTime(receiptTx.timestamp || new Date())}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Bank UTR / Ref #:</span>
                <span className="text-purple-300 font-bold">
                  UTR-982149102482
                </span>
              </div>
              <div className="flex items-center justify-between pt-1 border-t border-slate-800">
                <span className="text-slate-400">AI Risk Assessment:</span>
                <span className="text-emerald-400 font-bold">
                  {receiptTx.risk_score !== undefined ? `${receiptTx.risk_score}/100` : '15/100'} (LOW FRAUD RISK)
                </span>
              </div>
            </div>
          </div>
        </GlobalCenterModal>
      )}

      {/* Mobile Smartphone Security Push Notification Modal */}
      <MobileSecurityApprovalModal
        isOpen={showPhoneModal}
        onClose={() => setShowPhoneModal(false)}
        transaction={phoneModalTx || formData}
        approvalId={phoneModalApprovalId || decisionResult?.approval_id}
        customerName={customerPersona?.name || 'Customer'}
        actionLoading={actionLoading}
        onApprove={async (appId, challengeResponse) => {
          const id = appId || phoneModalApprovalId || decisionResult?.approval_id
          if (id && id !== 'PEND_DEMO_01' && !id.startsWith('DEMO_')) {
            await handleApprovalAction(id, 'APPROVE', challengeResponse)
          } else {
            setActionSuccessMsg(
              `Transaction authorized via mobile SMS OTP (${challengeResponse})! Funds released.`
            )
            loadWallet(formData.customer_id)
            loadRecentTransactions(formData.customer_id)
          }
        }}
        onReject={async (appId) => {
          const id = appId || phoneModalApprovalId || decisionResult?.approval_id
          if (id) {
            await handleApprovalAction(id, 'REJECT')
          } else {
            setActionSuccessMsg('Transaction blocked and card frozen!')
          }
        }}
      />
    </div>
  )
}
