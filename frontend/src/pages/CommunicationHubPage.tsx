import { ChangeEvent, FormEvent, useEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { apiClient, tokenStorage } from '../api/client'
import { useAuth } from '../contexts/AuthContext'
import type {
  CareConversation,
  CareTeamOverview,
  ChatMessage,
  ChildProfile,
  ShareableItem,
} from '../types'
import '../styles/communication-hub.css'

const apiUrl = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1'
const wsBase = apiUrl.replace(/^http/, 'ws').replace(/\/api\/v1\/?$/, '')

const previewText = (conversation: CareConversation) => {
  const message = conversation.last_message
  if (!message) return conversation.kind === 'group' ? 'مجموعة فريق الرعاية' : 'ابدؤوا المحادثة'
  if (message.message_type === 'attachment') return `مرفق: ${message.attachments[0]?.original_filename || 'ملف'}`
  if (message.message_type === 'shared') return `تمت مشاركة: ${message.shared_item?.title || 'عنصر من الملف'}`
  return message.body
}

export default function CommunicationHubPage() {
  const { childId } = useParams()
  const { user } = useAuth()
  const [child, setChild] = useState<ChildProfile | null>(null)
  const [team, setTeam] = useState<CareTeamOverview | null>(null)
  const [conversations, setConversations] = useState<CareConversation[]>([])
  const [shareableItems, setShareableItems] = useState<ShareableItem[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [body, setBody] = useState('')
  const [newOpen, setNewOpen] = useState(false)
  const [shareOpen, setShareOpen] = useState(false)
  const [kind, setKind] = useState<'direct' | 'group'>('direct')
  const [title, setTitle] = useState('')
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const socketRef = useRef<WebSocket | null>(null)
  const bottomRef = useRef<HTMLDivElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  const selected = conversations.find((conversation) => conversation.id === selectedId) ?? null
  const currentUserId = user?.id
  const availableMembers = useMemo(
    () =>
      (team?.members ?? []).filter(
        (member) =>
          member.user_id !== currentUserId &&
          member.access_status === 'active' &&
          (member.is_primary_guardian || member.permissions.includes('message_team')),
      ),
    [team, currentUserId],
  )

  const loadConversations = async () => {
    if (!childId) return
    const response = await apiClient.get<CareConversation[]>(`/children/${childId}/conversations`)
    setConversations(response.data)
    if (!selectedId && response.data.length) setSelectedId(response.data[0].id)
  }

  const markRead = async (conversationId: string) => {
    try {
      await apiClient.post(`/conversations/${conversationId}/read`)
      setConversations((current) => current.map((item) => (
        item.id === conversationId ? { ...item, unread_count: 0 } : item
      )))
      window.dispatchEvent(new Event('weam:chat-changed'))
    } catch {
      // A temporary read-receipt failure must not block the conversation.
    }
  }

  useEffect(() => {
    if (!childId) return
    Promise.all([
      apiClient.get<ChildProfile>(`/children/${childId}`),
      apiClient.get<CareTeamOverview>(`/children/${childId}/care-team`),
      apiClient.get<ShareableItem[]>(`/children/${childId}/shareable-items`).catch(() => ({ data: [] as ShareableItem[] })),
    ])
      .then(([childResponse, teamResponse, shareResponse]) => {
        setChild(childResponse.data)
        setTeam(teamResponse.data)
        setShareableItems(shareResponse.data)
        return loadConversations()
      })
      .catch(() => setError('تعذر فتح التواصل أو لا توجد لديك صلاحية المراسلة.'))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [childId])

  useEffect(() => {
    if (!selectedId) {
      setMessages([])
      return
    }

    apiClient
      .get<ChatMessage[]>(`/conversations/${selectedId}/messages`)
      .then((response) => {
        setMessages(response.data)
        return markRead(selectedId)
      })
      .catch(() => setError('تعذر تحميل الرسائل.'))

    socketRef.current?.close()
    const socket = new WebSocket(`${wsBase}/api/v1/ws/conversations/${selectedId}`)
    socketRef.current = socket
    socket.onopen = () => socket.send(JSON.stringify({ type: 'auth', token: tokenStorage.getAccessToken() }))
    socket.onmessage = (event) => {
      const payload = JSON.parse(event.data)
      if (payload.type === 'refresh') {
        apiClient.get<ChatMessage[]>(`/conversations/${selectedId}/messages`)
          .then((response) => {
            setMessages(response.data)
            return markRead(selectedId)
          })
          .catch(() => undefined)
        void loadConversations()
      }
      if (payload.type === 'message') {
        const incoming = payload.message as ChatMessage
        setMessages((current) => current.some((item) => item.id === incoming.id) ? current : [...current, incoming])
        if (incoming.sender_user_id !== currentUserId) void markRead(selectedId)
        void loadConversations()
      }
      if (payload.type === 'read' && payload.user_id !== currentUserId) {
        apiClient.get<ChatMessage[]>(`/conversations/${selectedId}/messages`)
          .then((response) => setMessages(response.data))
          .catch(() => undefined)
      }
    }
    return () => socket.close()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedId, currentUserId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const addMessage = (message: ChatMessage) => {
    setMessages((current) => current.some((item) => item.id === message.id) ? current : [...current, message])
  }

  const send = async (event: FormEvent) => {
    event.preventDefault()
    if (!selectedId || !body.trim()) return
    const content = body.trim()
    setBody('')
    setBusy(true)
    try {
      const response = await apiClient.post<ChatMessage>(`/conversations/${selectedId}/messages`, { body: content })
      addMessage(response.data)
      await loadConversations()
    } catch {
      setBody(content)
      setError('تعذر إرسال الرسالة.')
    } finally {
      setBusy(false)
    }
  }

  const shareItem = async (item: ShareableItem) => {
    if (!selectedId) return
    setBusy(true)
    setError('')
    try {
      const response = await apiClient.post<ChatMessage>(`/conversations/${selectedId}/messages`, {
        shared_entity_type: item.entity_type,
        shared_entity_id: item.entity_id,
      })
      addMessage(response.data)
      setShareOpen(false)
      await loadConversations()
    } catch {
      setError('تعذرت مشاركة العنصر في المحادثة.')
    } finally {
      setBusy(false)
    }
  }

  const uploadAttachment = async (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    event.target.value = ''
    if (!file || !selectedId) return
    const form = new FormData()
    form.append('file', file)
    setBusy(true)
    setError('')
    try {
      const response = await apiClient.post<ChatMessage>(`/conversations/${selectedId}/attachments`, form)
      addMessage(response.data)
      await loadConversations()
    } catch {
      setError('تعذر رفع المرفق. استخدمي ملف PDF أو صورة بحجم مناسب.')
    } finally {
      setBusy(false)
    }
  }

  const downloadAttachment = async (url: string, filename: string) => {
    try {
      const response = await apiClient.get(url, { responseType: 'blob' })
      const blobUrl = URL.createObjectURL(response.data)
      const anchor = document.createElement('a')
      anchor.href = blobUrl
      anchor.download = filename
      anchor.click()
      URL.revokeObjectURL(blobUrl)
    } catch {
      setError('تعذر تنزيل المرفق.')
    }
  }

  const createConversation = async (event: FormEvent) => {
    event.preventDefault()
    if (!childId) return
    if (kind === 'direct' && selectedUsers.length !== 1) return setError('اختاري شخصًا واحدًا للمحادثة الفردية.')
    if (kind === 'group' && selectedUsers.length < 1) return setError('اختاري عضوًا واحدًا على الأقل للمجموعة.')
    setBusy(true)
    setError('')
    try {
      const response = await apiClient.post<CareConversation>(`/children/${childId}/conversations`, {
        kind,
        title: kind === 'group' ? title || null : null,
        participant_user_ids: selectedUsers,
      })
      setNewOpen(false)
      setSelectedUsers([])
      setTitle('')
      await loadConversations()
      setSelectedId(response.data.id)
    } catch (requestError: any) {
      setError(requestError?.response?.data?.detail || 'تعذر إنشاء المحادثة.')
    } finally {
      setBusy(false)
    }
  }

  const toggleUser = (userId: string) => {
    if (kind === 'direct') return setSelectedUsers([userId])
    setSelectedUsers((current) => current.includes(userId) ? current.filter((item) => item !== userId) : [...current, userId])
  }

  if (!child && !error) return <div className="loading-row"><div className="spinner" /> جاري فتح التواصل...</div>
  if (!child) return <div className="prototype-empty-card"><h2>تعذر فتح التواصل</h2><p>{error}</p><Link className="btn btn-primary" to="/dashboard">الرئيسية</Link></div>

  return (
    <section className="communication-page">
      <div className="communication-heading">
        <div>
          <Link className="communication-back" to={`/children/${child.id}`}>← العودة لملف الطفل</Link>
          <span className="soft-kicker">تواصل فريق الرعاية</span>
          <h1>فريق {child.preferred_name || child.first_name} في مكان واحد</h1>
          <p>رسائل ومرفقات وعناصر مشتركة بين أعضاء الفريق المصرح لهم فقط.</p>
        </div>
        <button className="btn btn-primary" onClick={() => setNewOpen(true)}>＋ محادثة جديدة</button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}
      {newOpen && (
        <form className="new-conversation-card" onSubmit={createConversation}>
          <div className="new-conversation-head"><div><span className="soft-kicker">محادثة جديدة</span><h2>من تريدين إضافته؟</h2></div><button type="button" className="text-action" onClick={() => setNewOpen(false)}>إغلاق</button></div>
          <div className="conversation-kind-switch">
            <button type="button" className={kind === 'direct' ? 'active' : ''} onClick={() => { setKind('direct'); setSelectedUsers([]) }}>فردية</button>
            <button type="button" className={kind === 'group' ? 'active' : ''} onClick={() => { setKind('group'); setSelectedUsers([]) }}>مجموعة</button>
          </div>
          {kind === 'group' && <label className="field"><span>اسم المجموعة</span><input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="مثال: فريق متابعة تاليا" /></label>}
          <div className="conversation-member-grid">
            {availableMembers.map((member) => (
              <label key={member.user_id} className={selectedUsers.includes(member.user_id) ? 'selected' : ''}>
                <input type={kind === 'direct' ? 'radio' : 'checkbox'} name="conversation-member" checked={selectedUsers.includes(member.user_id)} onChange={() => toggleUser(member.user_id)} />
                <span className="member-dot">{member.full_name.slice(0, 1)}</span>
                <span><strong>{member.full_name}</strong><small>{member.role_label || 'عضو فريق الرعاية'}</small></span>
              </label>
            ))}
          </div>
          <button className="btn btn-primary" disabled={busy || !availableMembers.length}>{busy ? 'جارٍ الإنشاء...' : 'إنشاء المحادثة'}</button>
        </form>
      )}

      <div className={`communication-shell ${selected ? 'chat-open' : ''}`}>
        <aside className="conversation-sidebar">
          <div className="conversation-sidebar-title"><span>المحادثات</span><strong>{conversations.length}</strong></div>
          {!conversations.length ? <div className="conversation-empty-small"><span>💬</span><p>لا توجد محادثات بعد.</p></div> : conversations.map((conversation) => (
            <button key={conversation.id} className={`conversation-list-item ${selectedId === conversation.id ? 'active' : ''}`} onClick={() => setSelectedId(conversation.id)}>
              <span className="conversation-avatar">{conversation.kind === 'group' ? '♧' : conversation.title.slice(0, 1)}</span>
              <span className="conversation-list-copy"><strong>{conversation.title}</strong><small>{previewText(conversation)}</small></span>
              <span className="conversation-list-meta">
                <time>{conversation.last_message ? new Date(conversation.last_message.created_at).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' }) : ''}</time>
                {conversation.unread_count > 0 && <b>{conversation.unread_count > 99 ? '99+' : conversation.unread_count}</b>}
              </span>
            </button>
          ))}
        </aside>

        <main className="conversation-main">
          {!selected ? <div className="conversation-empty-main"><span>💬</span><h2>اختاري محادثة</h2><p>أو أنشئي محادثة جديدة مع فريق الرعاية.</p></div> : (
            <>
              <header className="conversation-chat-head">
                <button className="mobile-conversation-back" type="button" onClick={() => setSelectedId(null)}>→</button>
                <div><h2>{selected.title}</h2><p>{selected.participants.map((participant) => participant.full_name).join(' · ')}</p></div>
                <span>{selected.kind === 'group' ? `${selected.participants.length} أعضاء` : 'محادثة فردية'}</span>
              </header>

              <div className="conversation-messages">
                {!messages.length && <div className="conversation-start"><span>✦</span><h3>ابدؤوا أول تحديث</h3><p>كل رسالة هنا مرتبطة بفريق رعاية الطفل وليست محادثة عامة.</p></div>}
                {messages.map((message) => {
                  const mine = message.sender_user_id === currentUserId
                  return (
                    <div className={`message-row ${mine ? 'mine' : ''}`} key={message.id}>
                      <div className="message-bubble">
                        {!mine && <strong>{message.sender_name}</strong>}
                        {message.body && <p dir="auto">{message.body}</p>}
                        {message.shared_item && <Link className="shared-message-card" to={message.shared_item.url}><small>عنصر من ملف الطفل</small><strong>{message.shared_item.title}</strong><span>فتح العنصر ←</span></Link>}
                        {message.attachments.map((attachment) => (
                          <button className="attachment-message-card" type="button" key={attachment.id} onClick={() => void downloadAttachment(attachment.download_url, attachment.original_filename)}>
                            <span>▤</span><span><strong>{attachment.original_filename}</strong><small>{Math.max(1, Math.round(attachment.size_bytes / 1024))} كيلوبايت</small></span><b>تنزيل</b>
                          </button>
                        ))}
                        <div className="message-meta"><time>{new Date(message.created_at).toLocaleTimeString('ar-SA', { hour: '2-digit', minute: '2-digit' })}</time>{mine && <small>{message.is_read_by_everyone ? 'تمت القراءة' : 'تم الإرسال'}</small>}</div>
                      </div>
                    </div>
                  )
                })}
                <div ref={bottomRef} />
              </div>

              {shareOpen && (
                <div className="conversation-share-panel">
                  <div><strong>مشاركة من ملف الطفل</strong><button type="button" onClick={() => setShareOpen(false)}>إغلاق</button></div>
                  {!shareableItems.length ? <p>لا توجد تقارير أو أهداف أو متابعات متاحة للمشاركة ضمن صلاحياتك.</p> : <div>{shareableItems.map((item) => <button type="button" key={`${item.entity_type}-${item.entity_id}`} onClick={() => void shareItem(item)} disabled={busy}><span>{item.subtitle}</span><strong>{item.title}</strong></button>)}</div>}
                </div>
              )}

              <form className="conversation-composer" onSubmit={send}>
                <div className="composer-actions">
                  <button type="button" onClick={() => fileInputRef.current?.click()} disabled={busy} aria-label="إرفاق ملف">＋</button>
                  <button type="button" onClick={() => setShareOpen((current) => !current)} disabled={busy} aria-label="مشاركة عنصر">↗</button>
                  <input ref={fileInputRef} type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" onChange={(event) => void uploadAttachment(event)} hidden />
                </div>
                <textarea rows={2} dir="auto" value={body} onChange={(event) => setBody(event.target.value)} placeholder="اكتبي تحديثًا للفريق..." onKeyDown={(event) => { if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit() } }} />
                <button className="btn btn-primary" disabled={busy || !body.trim()}>إرسال</button>
              </form>
            </>
          )}
        </main>
      </div>
    </section>
  )
}
