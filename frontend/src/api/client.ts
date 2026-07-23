export type User = {
  id: string
  email: string
  display_name: string
  is_email_verified: boolean
  is_active: boolean
}

export type BrowserTokenResponse = {
  access_token: string
  csrf_token: string
  token_type: 'bearer'
  expires_in: number
}

export type RegisterResponse = {
  message: string
  requires_email_verification: boolean
  verification_token: string | null
}

type ErrorEnvelope = {
  error?: {
    code?: string
    message?: string
  }
  detail?: string
  message?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly code: string

  constructor(message: string, status: number, code: string) {
    super(message)
    this.status = status
    this.code = code
  }
}

async function parseError(response: Response): Promise<ApiError> {
  let body: ErrorEnvelope = {}
  try {
    body = (await response.json()) as ErrorEnvelope
  } catch {
    // A proxy or network edge can return a non-JSON error response.
  }
  const message =
    body.error?.message ||
    (typeof body.detail === 'string' ? body.detail : null) ||
    body.message ||
    'ResolveHub could not complete the request.'
  const code = body.error?.code || 'REQUEST_FAILED'
  return new ApiError(message, response.status, code)
}

export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), 15000)
  try {
    const response = await fetch(`/api/v1${path}`, {
      ...init,
      signal: controller.signal,
      credentials: 'include',
      headers: {
        'Content-Type': 'application/json',
        ...init.headers,
      },
    })
    if (!response.ok) throw await parseError(response)
    if (response.status === 204) return undefined as T
    return (await response.json()) as T
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw new ApiError('The server did not respond in time. Check your connection and try again.', 504, 'TIMEOUT')
    }
    throw error
  } finally {
    clearTimeout(timer)
  }
}

export function readCookie(name: string): string | null {
  const prefix = `${encodeURIComponent(name)}=`
  const value = document.cookie
    .split('; ')
    .find((item) => item.startsWith(prefix))
    ?.slice(prefix.length)
  return value ? decodeURIComponent(value) : null
}
