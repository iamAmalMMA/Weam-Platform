import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { apiClient } from '../api/client'
import type { CareConversation, ChildProfile } from '../types'
import '../styles/communication-hub.css'

interface ChildInbox {
  child: ChildProfile
  conversations: CareConversation[]
}

export default function MessagesInboxPage() {
  const [items, setItems] = useState<ChildInbox[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    apiClient.get<ChildProfile[]>('/children')
      .then(async (response) => {
        const rows = await Promise.all(response.data.map(async (child) => {
          try {
            const conversations = await apiClient.get<CareConversation[]>(`/children/${child.id}/conversations`)
            return { child, conversations: conversations.data }
          } catch {
            return { child, conversations: [] }
          }
        }))
        setItems(rows.filter((row) => row.conversations.length > 0))
      })
      .catch(() => setError('تعذر تحميل الرسائل.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <div className="loading-row"><div className="spinner" /> جاري تحميل الرسائل...</div>

  return (
    <section className="messages-inbox-page">
      <div className="communication-heading">
        <div><span className="soft-kicker">الرسائل</span><h1>تواصل فرق الرعاية</h1><p>كل محادثات الأطفال المصرح لك بالوصول إليهم في مكان واحد.</p></div>
      </div>
      {error && <div className="alert alert-error">{error}</div>}
      {!items.length ? (
        <div className="prototype-empty-card"><span>💬</span><h2>لا توجد محادثات بعد</h2><p>تظهر المحادثات هنا بعد بدء التواصل من ملف الطفل.</p><Link className="btn btn-primary" to="/dashboard">العودة للرئيسية</Link></div>
      ) : (
        <div className="messages-inbox-grid">
          {items.map(({ child, conversations }) => {
            const unread = conversations.reduce((sum, item) => sum + item.unread_count, 0)
            return (
              <Link className="messages-inbox-card" key={child.id} to={`/children/${child.id}/communication`}>
                <span className="messages-inbox-avatar">{child.first_name.slice(0, 1)}</span>
                <div><small>فريق {child.preferred_name || child.first_name}</small><h2>{conversations.length} محادثات</h2><p>{unread ? `${unread} رسائل غير مقروءة` : 'جميع الرسائل مقروءة'}</p></div>
                {unread > 0 && <b>{unread > 99 ? '99+' : unread}</b>}
              </Link>
            )
          })}
        </div>
      )}
    </section>
  )
}
