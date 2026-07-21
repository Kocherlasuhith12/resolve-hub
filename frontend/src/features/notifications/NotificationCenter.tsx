import { useEffect, useRef, useState } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/useAuth'

type MembershipContext = {
  permissions: string[]
}

type Notification = {
  id: string
  kind: string
  title: string
  body: string
  resource_type: string
  resource_id: string
  read_at: string | null
  created_at: string
}

type NotificationPage = {
  items: Notification[]
  next_cursor: string | null
}

type RealtimeState = 'connecting' | 'live' | 'polling'

function formatKind(kind: string) {
  return kind.toLowerCase().replaceAll('_', ' ')
}

export function NotificationCenter({ organisationId }: { organisationId: string }) {
  const { request, connectRealtime } = useAuth()
  const queryClient = useQueryClient()
  const [realtimeState, setRealtimeState] = useState<RealtimeState>('connecting')
  const reconnectAttempt = useRef(0)
  const membership = useQuery({
    queryKey: ['membership', organisationId],
    queryFn: () =>
      request<MembershipContext>(`/organisations/${organisationId}/membership/me`),
  })
  const canRead = membership.data?.permissions.includes('notification:read') ?? false
  const notifications = useInfiniteQuery({
    queryKey: ['notifications', organisationId],
    initialPageParam: null as string | null,
    queryFn: ({ pageParam }) => {
      const query = new URLSearchParams({ limit: '20' })
      if (pageParam) query.set('cursor', pageParam)
      return request<NotificationPage>(
        `/organisations/${organisationId}/notifications?${query}`,
      )
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    enabled: canRead,
    refetchInterval: realtimeState === 'live' ? false : 10_000,
  })
  const markRead = useMutation({
    mutationFn: (notificationId: string) =>
      request<Notification>(
        `/organisations/${organisationId}/notifications/${notificationId}/read`,
        { method: 'POST' },
      ),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['notifications', organisationId] })
    },
  })

  useEffect(() => {
    if (!canRead) return
    let socket: WebSocket | null = null
    let reconnectTimer: number | undefined
    let stopped = false

    const connect = () => {
      if (stopped) return
      setRealtimeState('connecting')
      try {
        socket = connectRealtime(organisationId)
      } catch {
        socket = null
      }
      if (!socket) {
        setRealtimeState('polling')
        return
      }
      socket.onopen = () => {
        reconnectAttempt.current = 0
        setRealtimeState('live')
      }
      socket.onmessage = () => {
        void queryClient.invalidateQueries({ queryKey: ['notifications', organisationId] })
        void queryClient.invalidateQueries({ queryKey: ['tickets', organisationId] })
        void queryClient.invalidateQueries({ queryKey: ['ticket', organisationId] })
        void queryClient.invalidateQueries({ queryKey: ['ticket-comments', organisationId] })
        void queryClient.invalidateQueries({ queryKey: ['ticket-timeline', organisationId] })
      }
      socket.onerror = () => setRealtimeState('polling')
      socket.onclose = () => {
        if (stopped) return
        setRealtimeState('polling')
        const delay = Math.min(30_000, 1_000 * 2 ** reconnectAttempt.current)
        reconnectAttempt.current += 1
        reconnectTimer = window.setTimeout(connect, delay)
      }
    }

    connect()
    return () => {
      stopped = true
      if (reconnectTimer !== undefined) window.clearTimeout(reconnectTimer)
      socket?.close()
    }
  }, [canRead, connectRealtime, organisationId, queryClient])

  if (membership.isPending || !canRead) return null

  const items = notifications.data?.pages.flatMap((page) => page.items) ?? []
  const unreadCount = items.filter((item) => !item.read_at).length

  return (
    <section className="notification-center" aria-labelledby="notifications-title">
      <div className="notification-heading">
        <div>
          <p className="card-label">Personal updates</p>
          <h2 id="notifications-title">Notifications</h2>
        </div>
        <div className="notification-summary">
          <strong>{unreadCount} unread</strong>
          <span className={`connection-state connection-${realtimeState}`}>
            {realtimeState === 'live' ? 'Live updates' : realtimeState === 'connecting' ? 'Connecting…' : 'Polling updates'}
          </span>
        </div>
      </div>

      {notifications.isPending && <p className="section-message" role="status">Loading notifications…</p>}
      {notifications.isError && (
        <div className="form-error" role="alert">Notifications could not be loaded.</div>
      )}
      {!notifications.isPending && !notifications.isError && items.length === 0 && (
        <div className="empty-notifications">
          <h3>You are all caught up</h3>
          <p>Personal ticket and SLA updates will appear here.</p>
        </div>
      )}
      {items.length > 0 && (
        <ol className="notification-list">
          {items.map((item) => (
            <li key={item.id} className={item.read_at ? 'notification-read' : 'notification-unread'}>
              <div>
                <span className="notification-kind">{formatKind(item.kind)}</span>
                <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleString()}</time>
              </div>
              <h3>{item.title}</h3>
              <p>{item.body}</p>
              {!item.read_at && (
                <button
                  className="text-button"
                  type="button"
                  disabled={markRead.isPending}
                  onClick={() => markRead.mutate(item.id)}
                >
                  Mark as read
                </button>
              )}
            </li>
          ))}
        </ol>
      )}
      {notifications.hasNextPage && (
        <button
          className="quiet-button load-more"
          type="button"
          disabled={notifications.isFetchingNextPage}
          onClick={() => void notifications.fetchNextPage()}
        >
          {notifications.isFetchingNextPage ? 'Loading…' : 'Load older notifications'}
        </button>
      )}
    </section>
  )
}
