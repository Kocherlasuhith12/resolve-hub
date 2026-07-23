import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuth } from '../../auth/useAuth'

type ApiKey = {
  id: string
  name: string
  key_prefix: string
  scopes: string
  created_at: string
  expires_at: string | null
  revoked_at: string | null
  raw_key?: string
}

type Webhook = {
  id: string
  url: string
  events: string
  is_active: boolean
  created_at: string
  raw_secret?: string
}

type WebhookDelivery = {
  id: string
  event_type: string
  status_code: number | null
  delivered_at: string | null
}

export function DeveloperTab({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const queryClient = useQueryClient()

  const [createdKeySecret, setCreatedKeySecret] = useState<string | null>(null)
  const [createdWebhookSecret, setCreatedWebhookSecret] = useState<string | null>(null)
  const [testResult, setTestResult] = useState<string | null>(null)

  const apiKeys = useQuery({
    queryKey: ['api-keys', organisationId],
    queryFn: () => request<ApiKey[]>(`/organisations/${organisationId}/api-keys`),
  })

  const webhooks = useQuery({
    queryKey: ['webhooks', organisationId],
    queryFn: () => request<Webhook[]>(`/organisations/${organisationId}/webhooks`),
  })

  const createApiKey = useMutation({
    mutationFn: (payload: { name: string; scopes: string }) =>
      request<ApiKey>(`/organisations/${organisationId}/api-keys`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: (data) => {
      if (data.raw_key) setCreatedKeySecret(data.raw_key)
      void queryClient.invalidateQueries({ queryKey: ['api-keys', organisationId] })
    },
  })

  const revokeApiKey = useMutation({
    mutationFn: (keyId: string) =>
      request<ApiKey>(`/organisations/${organisationId}/api-keys/${keyId}`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['api-keys', organisationId] })
    },
  })

  const createWebhook = useMutation({
    mutationFn: (payload: { url: string; events: string }) =>
      request<Webhook>(`/organisations/${organisationId}/webhooks`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    onSuccess: (data) => {
      if (data.raw_secret) setCreatedWebhookSecret(data.raw_secret)
      void queryClient.invalidateQueries({ queryKey: ['webhooks', organisationId] })
    },
  })

  const deleteWebhook = useMutation({
    mutationFn: (webhookId: string) =>
      request<void>(`/organisations/${organisationId}/webhooks/${webhookId}`, {
        method: 'DELETE',
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['webhooks', organisationId] })
    },
  })

  const testWebhook = useMutation({
    mutationFn: (webhookId: string) =>
      request<WebhookDelivery>(`/organisations/${organisationId}/webhooks/${webhookId}/test`, {
        method: 'POST',
      }),
    onSuccess: (data) => {
      setTestResult(`Ping test sent successfully! Delivery ID: ${data.id} (Status ${data.status_code})`)
    },
  })

  function handleCreateApiKey(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    createApiKey.mutate({
      name: String(fd.get('key_name')),
      scopes: String(fd.get('key_scopes') || '*'),
    })
  }

  function handleCreateWebhook(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    const fd = new FormData(e.currentTarget)
    createWebhook.mutate({
      url: String(fd.get('url')),
      events: String(fd.get('events') || '*'),
    })
  }

  return (
    <div className="admin-panel developer-panel">
      <div className="developer-section">
        <h3>API Keys</h3>
        <p>Managed developer API access keys with hashed token storage.</p>

        {createdKeySecret && (
          <div className="form-success" role="status">
            API Key Created! Copy key now (it won't be shown again):
            <br />
            <code>{createdKeySecret}</code>
            <button className="text-button" onClick={() => setCreatedKeySecret(null)}>Dismiss</button>
          </div>
        )}

        <form className="compact-form" onSubmit={handleCreateApiKey}>
          <label>
            <span>Key Description / Name</span>
            <input name="key_name" placeholder="e.g. CI Integration" required />
          </label>
          <label>
            <span>Scopes</span>
            <input name="key_scopes" defaultValue="*" placeholder="* or ticket:read,ticket:create" />
          </label>
          <button className="primary-button" type="submit" disabled={createApiKey.isPending}>
            {createApiKey.isPending ? 'Generating…' : 'Generate API Key'}
          </button>
        </form>

        <ul className="admin-list">
          {(apiKeys.data ?? []).map((key) => (
            <li key={key.id}>
              <span>
                <strong>{key.name}</strong> ({key.key_prefix}…)
              </span>
              <span>
                {key.revoked_at ? (
                  <span className="danger-text">Revoked</span>
                ) : (
                  <button
                    className="text-button danger-text"
                    type="button"
                    onClick={() => revokeApiKey.mutate(key.id)}
                    disabled={revokeApiKey.isPending}
                  >
                    Revoke Key
                  </button>
                )}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <div className="developer-section">
        <h3>Webhook Subscriptions</h3>
        <p>HMAC-SHA256 signed event delivery to external HTTP endpoints.</p>

        {createdWebhookSecret && (
          <div className="form-success" role="status">
            Webhook Secret:
            <br />
            <code>{createdWebhookSecret}</code>
            <button className="text-button" onClick={() => setCreatedWebhookSecret(null)}>Dismiss</button>
          </div>
        )}

        {testResult && (
          <div className="form-success" role="status">
            {testResult}
            <button className="text-button" onClick={() => setTestResult(null)}>Dismiss</button>
          </div>
        )}

        <form className="compact-form" onSubmit={handleCreateWebhook}>
          <label>
            <span>Target Endpoint URL</span>
            <input name="url" type="url" placeholder="https://example.com/webhooks" required />
          </label>
          <label>
            <span>Events Filter</span>
            <input name="events" defaultValue="*" placeholder="* or ticket.created,ticket.updated" />
          </label>
          <button className="primary-button" type="submit" disabled={createWebhook.isPending}>
            {createWebhook.isPending ? 'Adding…' : 'Add Webhook'}
          </button>
        </form>

        <ul className="admin-list">
          {(webhooks.data ?? []).map((wh) => (
            <li key={wh.id}>
              <span>
                <strong>{wh.url}</strong> ({wh.events})
              </span>
              <span>
                <button
                  className="text-button"
                  type="button"
                  onClick={() => testWebhook.mutate(wh.id)}
                  disabled={testWebhook.isPending}
                >
                  Test Ping
                </button>
                <button
                  className="text-button danger-text"
                  type="button"
                  onClick={() => deleteWebhook.mutate(wh.id)}
                  disabled={deleteWebhook.isPending}
                >
                  Delete
                </button>
              </span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
