import { useCallback, useEffect, useRef, useState } from 'react'
import {
  ArrowRight, ArrowUpRight, Check,
  CircleHelp, Clock3, LoaderCircle, LockKeyhole, LogOut, MessageCircle,
  MoreHorizontal, Package, Plus, Send, ShieldCheck, Sparkles, UtensilsCrossed,
  X,
} from 'lucide-react'

const API = (import.meta.env.VITE_API_URL || (import.meta.env.DEV ? '/api' : 'http://localhost:8000')).replace(/\/$/, '')
const SESSION_KEY = 'freshly_support_session'
const CUSTOMER_KEY = 'freshly_support_customer'

async function request(path, options = {}) {
  let response
  try {
    response = await fetch(`${API}${path}`, {
      ...options,
      headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    })
  } catch {
    throw new Error(`Can’t reach the support server at ${API}. Start the backend, then try again.`)
  }
  const data = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = data.detail
    const message = typeof detail === 'string'
      ? detail
      : Array.isArray(detail)
        ? detail.map((issue) => issue.msg).filter(Boolean).join(' ')
        : ''
    throw new Error(message || `Request failed (${response.status})`)
  }
  return data
}

const localId = () => `local-${globalThis.crypto?.randomUUID?.() || Date.now()}`
const greetingTime = () => new Intl.DateTimeFormat('en', { hour: 'numeric', minute: '2-digit' }).format(new Date())
const isHumanOption = (option) => /human|agent/i.test(option.label || option.id || '')
const firstContactOptions = (items = []) => items.filter((option) => !isHumanOption(option))
const ORDER_ISSUES = [
  { id: 'late_delivery', label: 'Late delivery' },
  { id: 'missing_item', label: 'Missing item' },
  { id: 'wrong_item', label: 'Wrong item' },
  { id: 'quality_issue', label: 'Food quality or packaging' },
  { id: 'cancellation', label: 'Cancel this order' },
  { id: 'general_support', label: 'Something else' },
]
const PAYMENT_ISSUES = [
  { id: 'payment_failed', label: 'Payment failed, but I was charged' },
  { id: 'duplicate_charge', label: 'I was charged more than once' },
  { id: 'refund_query', label: 'I have a refund question' },
  { id: 'general_support', label: 'Something else about payment' },
]

function App() {
  const [customer, setCustomer] = useState(() => JSON.parse(localStorage.getItem(CUSTOMER_KEY) || 'null'))
  const [sessionId, setSessionId] = useState(() => localStorage.getItem(SESSION_KEY) || '')
  const [options, setOptions] = useState([])
  const [messages, setMessages] = useState([])
  const [orders, setOrders] = useState([])
  const [caseContext, setCaseContext] = useState(null)
  const [lastUserMessage, setLastUserMessage] = useState('')
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(false)
  const [booting, setBooting] = useState(true)
  const [error, setError] = useState('')
  const [ticket, setTicket] = useState(null)
  const [showAuth, setShowAuth] = useState(false)
  const [authMode, setAuthMode] = useState('login')
  const [authEmail, setAuthEmail] = useState('')
  const [authPassword, setAuthPassword] = useState('')
  const [authBusy, setAuthBusy] = useState(false)
  const [ordersOpen, setOrdersOpen] = useState(false)
  const endRef = useRef(null)
  const inputRef = useRef(null)

  const persistSession = useCallback((next) => {
    setSessionId(next)
    localStorage.setItem(SESSION_KEY, next)
  }, [])

  const loadConversation = useCallback(async (customerId, currentSession) => {
    const [welcome, recentOrders] = await Promise.all([
      request('/chat/options'),
      request(`/orders/recent?customer_id=${customerId}&limit=100`).catch(() => []),
    ])
    setOptions(welcome.options || [])
    setOrders(recentOrders)
    // A login must still succeed when connecting to an older backend version
    // that does not yet expose latest-session; in that case show the welcome
    // message and let the customer start a fresh chat.
    const latestSession = currentSession || (await request(`/chat/latest-session?customer_id=${customerId}`).catch(() => ({ session_id: null }))).session_id
    if (latestSession) {
      const history = await request(`/chat/${encodeURIComponent(latestSession)}/history?customer_id=${customerId}`)
      if (history.length) {
        setSessionId(latestSession)
        localStorage.setItem(`${SESSION_KEY}_${customerId}`, latestSession)
        const restoredMessages = history.map((item) => ({
          id: item.id,
          role: item.role === 'assistant' ? 'assistant' : 'user',
          text: item.message,
          time: new Date(item.created_at).toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' }),
        }))
        restoredMessages.push({
          id: `support-options-${latestSession}`,
          role: 'assistant',
          text: 'What would you like help with next?',
          time: greetingTime(),
          options: welcome.options || [],
        })
        setMessages(restoredMessages)
        return
      }
    }
    setMessages([{ id: 'welcome', role: 'assistant', text: welcome.welcome_message || 'Hi! How can I help you today?', time: greetingTime(), options: firstContactOptions(welcome.options) }])
  }, [])

  useEffect(() => {
    let active = true
    const initialize = customer?.id
      ? loadConversation(customer.id, sessionId)
      : request('/chat/options').then((welcome) => {
        setOptions(welcome.options || [])
        setMessages([{ id: 'welcome', role: 'assistant', text: welcome.welcome_message || 'Hi! How can I help you today?', time: greetingTime(), options: firstContactOptions(welcome.options) }])
      })
    initialize.catch((e) => {
      if (active) setError(e.message || 'Could not connect to support.')
    }).finally(() => { if (active) setBooting(false) })
    return () => { active = false }
  }, [customer?.id, loadConversation, sessionId])

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }) }, [messages, loading])

  const authenticate = async (mode, email, password) => {
    setAuthBusy(true); setError('')
    try {
      const data = await request(`/auth/${mode}`, { method: 'POST', body: JSON.stringify({ email, password }) })
      const nextCustomer = { id: data.customer_id, email }
      setCustomer(nextCustomer); setSessionId(''); setTicket(null); setMessages([]); setCaseContext(null); setLastUserMessage('')
      localStorage.setItem(CUSTOMER_KEY, JSON.stringify(nextCustomer))
      localStorage.removeItem(SESSION_KEY)
      setShowAuth(false); setBooting(true)
      await loadConversation(data.customer_id, '')
    } catch (e) { setError(e.message || `Could not ${mode === 'register' ? 'create account' : 'sign in'}.`) }
    finally { setAuthBusy(false); setBooting(false) }
  }

  const pushUserMessage = (text) => {
    setMessages((current) => [...current, { id: localId(), role: 'user', text, time: greetingTime() }])
  }

  const followUpOptions = (context) => {
    const helpOption = {
      id: `human-${localId()}`,
      label: 'Still need help? Talk to a human',
      kind: 'handoff',
      context,
    }
    if (context?.type === 'track_order') {
      return [
        { id: 'track-another', label: 'Track another order', kind: 'track_another' },
        helpOption,
      ]
    }
    if (context) return [
      { id: 'resolved', label: 'That solved it', kind: 'resolved' },
      helpOption,
    ]
    return [
      { id: 'resolved', label: 'That solved it', kind: 'resolved' },
      { id: 'new-topic', label: 'Choose another help topic', kind: 'new_topic' },
      helpOption,
    ]
  }

  const appendAssistant = (text, nextOptions = []) => {
    setMessages((current) => [...current, {
      id: localId(), role: 'assistant', text, time: greetingTime(), options: nextOptions,
    }])
  }

  const beginOrderSelection = async (flowType, extra = {}) => {
    if (!customer?.id) {
      setAuthMode('login'); setShowAuth(true)
      setError('Sign in to see orders linked to your account.')
      return
    }
    const currentOrders = await request(`/orders/recent?customer_id=${customer.id}&limit=5`).catch(() => orders.slice(0, 5))
    setOrders(currentOrders)
    const recent = currentOrders.slice(0, 5)
    if (!recent.length) {
      const type = flowType === 'payment_order' ? 'payment_issue' : flowType
      const defaultCategory = {
        track_order: 'order_status',
        order_issue: 'general_support',
        missing_item: 'missing_item',
        cancel_order: 'cancellation',
        payment_issue: 'general_support',
      }[type] || 'general_support'
      setCaseContext({
        type,
        category: extra.category || defaultCategory,
        ...extra,
        summary: extra.summary || `Customer needs help with ${type.replaceAll('_', ' ')}; no recent order was available to select.`,
        agentPrompt: extra.agentPrompt || `The customer needs help with ${type.replaceAll('_', ' ')}. No recent order was available to select.`,
      })
      appendAssistant('I couldn’t find recent orders on this account. Enter the order number and briefly describe what you need help with.')
      inputRef.current?.focus()
      return
    }
    const orderOptions = recent.map((order) => ({
      id: `order-${flowType}-${order.id}`,
      label: `Order #${order.id} · ${String(order.status).replaceAll('_', ' ')} · ₹${Number(order.total_amount).toFixed(2)}`,
      kind: 'select_order',
      flowType,
      orderId: order.id,
      ...extra,
    }))
    if (flowType === 'payment_order') {
      orderOptions.push({
        id: 'payment-no-order', label: 'This payment is not linked to an order',
        kind: 'payment_no_order', ...extra,
      })
    }
    const prompts = {
      track_order: 'Which order would you like me to check?',
      order_issue: 'Which order has the issue?',
      missing_item: 'Which order is missing or has an incorrect item?',
      cancel_order: 'Which order would you like help cancelling?',
      payment_order: 'If this payment is linked to an order, choose it here. Otherwise choose “not linked”.',
    }
    appendAssistant(prompts[flowType] || 'Choose the order you need help with.', orderOptions)
  }

  const sendMessage = async (raw = draft, contextOverride = null) => {
    const rawText = raw.trim()
    if (!rawText || loading) return
    if (!customer?.id) { setShowAuth(true); setError('Sign in to start a support conversation.'); return }
    const context = contextOverride || caseContext
    const message = context?.agentPrompt
      ? `${context.agentPrompt}${rawText ? ` Customer details: ${rawText}` : ''}`
      : rawText
    const displayText = context?.displayPrompt
      ? `${context.displayPrompt}${rawText ? ` ${rawText}` : ''}`
      : rawText
    setError(''); setDraft(''); pushUserMessage(displayText); setLoading(true)
    setLastUserMessage(displayText)
    setCaseContext(null)
    try {
      const data = await request('/chat', { method: 'POST', body: JSON.stringify({ customer_id: customer.id, message, session_id: sessionId || null }) })
      if (data.session_id) {
        persistSession(data.session_id)
        localStorage.setItem(`${SESSION_KEY}_${customer.id}`, data.session_id)
      }
      const resolvedContext = context ? { ...context, description: rawText || context.description || '' } : null
      setMessages((current) => [...current, {
        id: localId(), role: 'assistant', text: data.reply, time: greetingTime(),
        options: data.handoff_required ? [] : followUpOptions(resolvedContext),
      }])
      if (data.handoff_required) {
        setTicket(data.ticket_id ? { id: data.ticket_id } : { pending: true })
      }
    } catch (e) {
      setError(e.message || 'Your message could not be sent. Please try again.')
    } finally { setLoading(false); inputRef.current?.focus() }
  }

  const requestHuman = async (context = caseContext) => {
    if (!customer?.id) { setShowAuth(true); setError('Sign in to contact support.'); return }
    if (loading) return
    const summary = context?.summary || lastUserMessage || 'Customer requested help with an issue that was not resolved by the chatbot.'
    setError(''); pushUserMessage('I’d like a human to help with this issue.'); setLoading(true)
    try {
      const created = await request('/support/tickets', {
        method: 'POST',
        body: JSON.stringify({
          customer_id: customer.id,
          category: context?.category || 'general_support',
          order_id: context?.orderId || null,
          description: `Human follow-up requested. ${summary}${context?.description ? ` Customer details: ${context.description}` : ''}`.slice(0, 3000),
          priority: 'high',
        }),
      })
      setTicket(created)
      appendAssistant(`I’ve created a high-priority support request (ticket #${created.id}) with the details from this conversation. A support team member can follow up; this chat does not connect to a live agent.`)
    } catch (e) { setError(e.message || 'Could not create your support request.') }
    finally { setLoading(false) }
  }

  const handleOption = (option) => {
    setMessages((current) => current.map((message) => message.options?.some((item) => item.id === option.id) ? { ...message, options: [] } : message))

    if (option.kind === 'handoff' || isHumanOption(option)) return requestHuman(option.context)
    if (option.kind === 'main' || (!option.kind && option.id)) {
      setCaseContext(null)
      switch (option.id) {
        case 'track_order': return beginOrderSelection('track_order')
        case 'order_issue': return beginOrderSelection('order_issue')
        case 'missing_item': return beginOrderSelection('missing_item')
        case 'cancel_order': return beginOrderSelection('cancel_order')
        case 'payment_issue':
          return appendAssistant('What happened with your payment?', PAYMENT_ISSUES.map((issue) => ({ ...issue, kind: 'payment_type' })))
        default: return
      }
    }
    if (option.kind === 'select_order') {
      const order = orders.find((item) => item.id === option.orderId)
      const orderSummary = order ? `Order #${order.id} (${String(order.status).replaceAll('_', ' ')})` : `Order #${option.orderId}`
      if (option.flowType === 'track_order') {
        return sendMessage(`Please check the current status and details for ${orderSummary}.`, {
          type: 'track_order', orderId: option.orderId, category: 'order_status',
          displayPrompt: `Track ${orderSummary}.`,
        })
      }
      if (option.flowType === 'order_issue') {
        return appendAssistant(`What kind of problem are you having with ${orderSummary}?`, ORDER_ISSUES.map((issue) => ({
          ...issue, kind: 'issue_type', orderId: option.orderId,
        })))
      }
      if (option.flowType === 'missing_item') {
        const context = {
          type: 'missing_item', orderId: option.orderId, category: 'missing_item',
          summary: `Missing or incorrect item for ${orderSummary}.`,
          displayPrompt: `${orderSummary} · Missing or incorrect item:`,
          question: `About ${orderSummary}, what item is missing or incorrect?`,
          agentPrompt: `The customer reports a missing or incorrect item in ${orderSummary}.`,
        }
        setCaseContext(context)
        appendAssistant(context.question)
        inputRef.current?.focus()
        return
      }
      if (option.flowType === 'cancel_order') {
        return sendMessage(`Please help me cancel ${orderSummary}.`, {
          type: 'cancellation', orderId: option.orderId, category: 'cancellation',
          summary: `Cancellation requested for ${orderSummary}.`,
          displayPrompt: `I need help cancelling ${orderSummary}.`,
        })
      }
      if (option.flowType === 'payment_order') {
        const context = {
          type: 'payment_issue', orderId: option.orderId, category: option.category || 'refund_query',
          summary: `${option.issueLabel || 'Payment issue'}${option.orderId ? ` for order #${option.orderId}` : ''}.`,
          displayPrompt: `${option.issueLabel || 'Payment issue'}${option.orderId ? ` · Order #${option.orderId}` : ''}:`,
          question: `Please describe what happened with this payment${option.orderId ? ` for order #${option.orderId}` : ''}.`,
          agentPrompt: `Payment issue (${option.issueLabel || 'general'}).${option.orderId ? ` Related order: #${option.orderId}.` : ''}`,
        }
        setCaseContext(context)
        appendAssistant(context.question)
        inputRef.current?.focus()
        return
      }
    }
    if (option.kind === 'issue_type') {
      const order = orders.find((item) => item.id === option.orderId)
      const orderSummary = order ? `order #${order.id}` : `order #${option.orderId}`
      const context = {
        type: option.id === 'cancellation' ? 'cancellation' : 'order_issue',
        orderId: option.orderId,
        category: option.id,
        summary: `${option.label} reported for ${orderSummary}.`,
        displayPrompt: `${orderSummary} · ${option.label}:`,
        question: `Tell me a little more about the ${option.label.toLowerCase()} on ${orderSummary}.`,
        agentPrompt: `The customer selected “${option.label}” for ${orderSummary}.`,
      }
      setCaseContext(context)
      appendAssistant(context.question)
      inputRef.current?.focus()
      return
    }
    if (option.kind === 'payment_type') {
      const extra = { category: option.id === 'payment_failed' || option.id === 'duplicate_charge' ? 'general_support' : option.id, issueLabel: option.label }
      return beginOrderSelection('payment_order', extra)
    }
    if (option.kind === 'payment_no_order') {
      const context = {
        type: 'payment_issue', category: option.category || 'general_support',
        summary: `${option.issueLabel || 'Payment issue'} not linked to an order.`,
        displayPrompt: `${option.issueLabel || 'Payment issue'}:`,
        question: 'Please describe the payment issue. Do not include full card numbers, passwords, or one-time codes.',
        agentPrompt: `Payment issue (${option.issueLabel || 'general'}), not linked to an order.`,
      }
      setCaseContext(context)
      appendAssistant(context.question)
      inputRef.current?.focus()
      return
    }
    if (option.kind === 'track_another') return beginOrderSelection('track_order')
    if (option.kind === 'resolved') {
      setCaseContext(null)
      return appendAssistant('Glad I could help. If you have another question, you can type it below.')
    }
    if (option.kind === 'new_topic') {
      setCaseContext(null)
      return appendAssistant('Choose a topic to get started:', firstContactOptions(options))
    }
  }

  const startNewChat = async () => {
    setSessionId(''); localStorage.removeItem(SESSION_KEY); setTicket(null); setError(''); setCaseContext(null); setLastUserMessage('')
    try {
      const welcome = await request('/chat/options')
      setOptions(welcome.options || [])
      setMessages([{ id: localId(), role: 'assistant', text: welcome.welcome_message || 'Hi! How can I help?', time: greetingTime(), options: firstContactOptions(welcome.options) }])
    } catch (e) { setError(e.message) }
  }

  const logout = () => {
    setCustomer(null); setMessages([]); setOrders([]); setTicket(null); setCaseContext(null); setLastUserMessage(''); setShowAuth(false)
    localStorage.removeItem(CUSTOMER_KEY); localStorage.removeItem(SESSION_KEY); setSessionId('')
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#home" aria-label="Freshly home"><span className="brand-mark"><UtensilsCrossed size={19} strokeWidth={2.4} /></span><span>freshly<span className="brand-period">.</span></span></a>
        <nav className="top-nav" aria-label="Main navigation"><a href="#orders" onClick={(e) => { e.preventDefault(); setOrdersOpen(true) }}>My orders</a><a className="nav-active" href="#help">Help center</a></nav>
        <div className="top-actions"><span className="secure-note"><ShieldCheck size={15} /> Secure support</span>{customer ? <button className="profile-button" onClick={logout} title={`Sign out ${customer.email}`}><span>{customer.email?.[0]?.toUpperCase() || 'G'}</span><LogOut size={14} /></button> : <><button className="signin-button" onClick={() => { setAuthMode('login'); setError(''); setShowAuth(true) }}>Sign in</button><button className="register-nav-button" onClick={() => { setAuthMode('register'); setError(''); setShowAuth(true) }}>Create account</button></>}</div>
      </header>

      <main className="page">
        <section className="support-layout" aria-label="Customer support chat">
          <aside className="help-sidebar">
            <div className="sidebar-heading">YOUR SUPPORT</div>
            <button className="sidebar-link active"><MessageCircle size={17} /><span>Chat with us</span><span className="online-dot" /></button>
            <button className="sidebar-link" onClick={() => setOrdersOpen(true)}><Package size={17} /><span>Recent orders</span><ArrowUpRight className="side-arrow" size={14} /></button>
            <div className="sidebar-rule" />
            <div className="sidebar-heading">NEED A QUICK ANSWER?</div>
            <div className="faq-links">{(options.length ? options.filter((option) => !isHumanOption(option)).slice(0, 4) : []).map((option) => <button key={option.id} onClick={() => handleOption(option)}>{option.label}<ArrowUpRight size={13} /></button>)}</div>
            <div className="sidebar-spacer" />
            <div className="sidebar-card"><div className="card-icon"><Clock3 size={17} /></div><div><strong>We’re here for you</strong><p>Chat with us anytime.<br />We’ll get back to you soon.</p><span className="response-time"><i /> Usually replies in minutes</span></div></div>
          </aside>

          <section className="chat-card">
            <div className="chat-header"><div className="agent-avatar"><Sparkles size={20} /></div><div className="agent-info"><strong>Freshly support</strong><div><span className="status-dot" /> Online <span className="status-separator">·</span> Here to help</div></div><button className="icon-button" aria-label="Start a new chat" onClick={startNewChat}><Plus size={18} /></button><button className="icon-button more-button" aria-label="More options" onClick={() => setOrdersOpen(true)}><MoreHorizontal size={19} /></button></div>

            <div className="message-list" aria-live="polite">
              <div className="date-divider"><span />TODAY<span /></div>
              {booting ? <div className="loading-state"><span className="loader-mark"><UtensilsCrossed size={19} /></span><span>Getting things ready...</span></div> : messages.map((message) => <Message key={message.id} message={message} onOption={handleOption} />)}
              {loading && <div className="message-row assistant-row"><div className="mini-avatar"><Sparkles size={13} /></div><div className="typing-bubble"><i /><i /><i /></div></div>}
              {ticket && <div className="ticket-status"><span><Check size={14} /></span><div><strong>Support request {ticket.id ? `#${ticket.id}` : 'submitted'}</strong><small>Our team can follow up on your ticket</small></div></div>}
              <div ref={endRef} />
            </div>

            {error && <div className="error-banner" role="alert"><CircleHelp size={15} />{error}<button onClick={() => setError('')} aria-label="Dismiss error"><X size={14} /></button></div>}
            <div className="composer-wrap"><form className="composer" onSubmit={(e) => { e.preventDefault(); sendMessage() }}><input ref={inputRef} value={draft} onChange={(e) => setDraft(e.target.value)} placeholder={customer ? 'Ask us anything about your order...' : 'Sign in to start a conversation...'} maxLength={4000} disabled={!customer || loading} aria-label="Type your message" /><button className={`send-button ${draft.trim() ? 'ready' : ''}`} disabled={!draft.trim() || loading} aria-label="Send message">{loading ? <LoaderCircle className="spin" size={18} /> : <Send size={17} />}</button></form><div className="composer-foot"><span><LockKeyhole size={12} /> Your conversation is private</span><span>Powered by <b>freshly<span className="brand-period">.</span></b></span></div></div>
          </section>
        </section>

        <footer className="page-footer"><span>Good food. Good people. We’ve got you.</span><span>© 2026 Freshly Support</span></footer>
      </main>

      {showAuth && <AuthModal mode={authMode} setMode={(mode) => { setError(''); setAuthMode(mode) }} email={authEmail} setEmail={setAuthEmail} password={authPassword} setPassword={setAuthPassword} busy={authBusy} error={error} onClose={() => setShowAuth(false)} onSubmit={() => authenticate(authMode, authEmail, authPassword)} />}
      {ordersOpen && <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) setOrdersOpen(false) }}><section className="orders-modal" role="dialog" aria-modal="true" aria-labelledby="orders-title"><div className="modal-head"><div><div className="modal-kicker">YOUR FRESHLY ACCOUNT</div><h2 id="orders-title">Recent orders</h2></div><button className="icon-button" onClick={() => setOrdersOpen(false)} aria-label="Close"><X size={18} /></button></div>{!customer ? <div className="empty-orders"><Package size={27} /><p>Sign in to see your recent orders.</p><button onClick={() => { setOrdersOpen(false); setShowAuth(true) }}>Sign in <ArrowRight size={14} /></button></div> : orders.length ? <div className="order-list">{orders.map((order) => <div className="order-row" key={order.id}><div className="order-icon"><Package size={17} /></div><div className="order-main"><strong>Order #{order.id}</strong><span><i className={`order-dot ${String(order.status).toLowerCase()}`} />{String(order.status).replaceAll('_', ' ')}</span></div><strong className="order-total">₹{Number(order.total_amount).toFixed(2)}</strong></div>)}</div> : <div className="empty-orders"><Package size={27} /><p>No recent orders to show just yet.</p></div>}<div className="modal-foot"><ShieldCheck size={14} /> Your order information is only visible to you.</div></section></div>}
    </div>
  )
}

function Message({ message, onOption }) {
  const assistant = message.role === 'assistant'
  return <div className={`message-row ${assistant ? 'assistant-row' : 'user-row'}`}>{assistant && <div className="mini-avatar"><Sparkles size={13} /></div>}<div className="message-content"><div className={`bubble ${assistant ? 'assistant-bubble' : 'user-bubble'}`}>{message.text}</div>{message.options?.length > 0 && <div className="quick-replies">{message.options.map((option) => <button key={option.id} onClick={() => onOption(option)}>{option.label}<ArrowRight size={13} /></button>)}</div>}<div className={`message-time ${assistant ? '' : 'user-time'}`}>{assistant ? 'FRESHLY SUPPORT' : 'YOU'}<span>·</span>{message.time}</div></div></div>
}

function AuthModal({ mode, setMode, email, setEmail, password, setPassword, busy, error, onClose, onSubmit }) {
  return <div className="modal-backdrop" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose() }}><section className="auth-modal" role="dialog" aria-modal="true" aria-labelledby="auth-title"><button className="modal-close icon-button" onClick={onClose} aria-label="Close"><X size={18} /></button><span className="modal-brand"><UtensilsCrossed size={19} /></span><div className="modal-kicker">PERSONALIZED SUPPORT</div><h2 id="auth-title">{mode === 'login' ? 'Welcome back.' : 'Let’s get started.'}</h2><p className="auth-subtitle">{mode === 'login' ? 'Sign in to get help with your orders.' : 'Create an account to chat with our team.'}</p>{error && <div className="auth-error" role="alert">{error}</div>}<form onSubmit={(e) => { e.preventDefault(); onSubmit() }} className="auth-form"><label>Email address<input type="email" autoComplete="email" placeholder="you@example.com" value={email} onChange={(e) => setEmail(e.target.value)} required /></label><label>Password<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} placeholder="At least 8 characters" minLength={mode === 'register' ? 8 : 1} value={password} onChange={(e) => setPassword(e.target.value)} required /></label><button className="auth-submit" disabled={busy}>{busy ? <LoaderCircle size={17} className="spin" /> : mode === 'login' ? 'Sign in' : 'Create account'}<ArrowRight size={16} /></button></form><div className="auth-switch">{mode === 'login' ? 'New to Freshly?' : 'Already have an account?'} <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>{mode === 'login' ? 'Create account' : 'Sign in'}</button></div><div className="demo-hint"><ShieldCheck size={14} /> Demo accounts are available in the project seed data.</div></section></div>
}

export default App
