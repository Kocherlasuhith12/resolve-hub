import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react'
import { useQueryClient } from '@tanstack/react-query'
import {
  apiRequest,
  ApiError,
  readCookie,
  type BrowserTokenResponse,
  type User,
} from '../api/client'
import { AuthContext, type AuthStatus } from './context'

async function loadUser(accessToken: string): Promise<User> {
  return apiRequest<User>('/auth/me', {
    headers: { Authorization: `Bearer ${accessToken}` },
  })
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()
  const [status, setStatus] = useState<AuthStatus>('loading')
  const [accessToken, setAccessToken] = useState<string | null>(null)
  const accessTokenRef = useRef<string | null>(null)
  const refreshPromiseRef = useRef<Promise<string> | null>(null)
  const [user, setUser] = useState<User | null>(null)

  const clearSession = useCallback(() => {
    accessTokenRef.current = null
    refreshPromiseRef.current = null
    setAccessToken(null)
    setUser(null)
    setStatus('unauthenticated')
    queryClient.clear()
  }, [queryClient])

  const acceptSession = useCallback(async (tokens: BrowserTokenResponse) => {
    const currentUser = await loadUser(tokens.access_token)
    accessTokenRef.current = tokens.access_token
    setAccessToken(tokens.access_token)
    setUser(currentUser)
    setStatus('authenticated')
  }, [])

  const refreshAccessToken = useCallback((): Promise<string> => {
    if (refreshPromiseRef.current) return refreshPromiseRef.current
    const csrfToken = readCookie('resolvehub_csrf')
    if (!csrfToken) {
      clearSession()
      return Promise.reject(new ApiError('Your session has expired.', 401, 'SESSION_EXPIRED'))
    }
    const refreshPromise = apiRequest<BrowserTokenResponse>('/auth/browser/refresh', {
      method: 'POST',
      headers: {
        'X-CSRF-Token': csrfToken,
        'X-ResolveHub-Client': 'browser',
      },
    })
      .then((tokens) => {
        accessTokenRef.current = tokens.access_token
        setAccessToken(tokens.access_token)
        return tokens.access_token
      })
      .catch((error: unknown) => {
        clearSession()
        throw error
      })
      .finally(() => {
        refreshPromiseRef.current = null
      })
    refreshPromiseRef.current = refreshPromise
    return refreshPromise
  }, [clearSession])

  useEffect(() => {
    if (!readCookie('resolvehub_csrf')) {
      setStatus('unauthenticated')
      return
    }
    refreshAccessToken()
      .then(loadUser)
      .then((currentUser) => {
        setUser(currentUser)
        setStatus('authenticated')
      })
      .catch(clearSession)
  }, [clearSession, refreshAccessToken])

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await apiRequest<BrowserTokenResponse>('/auth/browser/login', {
        method: 'POST',
        headers: { 'X-ResolveHub-Client': 'browser' },
        body: JSON.stringify({ email, password }),
      })
      await acceptSession(tokens)
    },
    [acceptSession],
  )

  const logout = useCallback(async () => {
    try {
      if (accessToken) {
        await apiRequest<void>('/auth/browser/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${accessToken}` },
        })
      }
    } finally {
      clearSession()
    }
  }, [accessToken, clearSession])

  const request = useCallback(
    async <T,>(path: string, init: RequestInit = {}) => {
      const requestWithToken = (token: string) => {
        const headers = Object.fromEntries(new Headers(init.headers).entries())
        return apiRequest<T>(path, {
          ...init,
          headers: { ...headers, Authorization: `Bearer ${token}` },
        })
      }
      const attemptedToken = accessTokenRef.current
      if (!attemptedToken) {
        throw new ApiError('Authentication is required.', 401, 'AUTH_REQUIRED')
      }
      try {
        return await requestWithToken(attemptedToken)
      } catch (error) {
        if (!(error instanceof ApiError) || error.status !== 401) throw error
        const currentToken = accessTokenRef.current
        const retryToken = currentToken && currentToken !== attemptedToken
          ? currentToken
          : await refreshAccessToken()
        try {
          return await requestWithToken(retryToken)
        } catch (retryError) {
          if (retryError instanceof ApiError && retryError.status === 401) clearSession()
          throw retryError
        }
      }
    },
    [clearSession, refreshAccessToken],
  )

  const connectRealtime = useCallback(
    (organisationId: string) => {
      if (!accessToken || typeof WebSocket === 'undefined') return null
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const url = `${protocol}//${window.location.host}/api/v1/organisations/${encodeURIComponent(organisationId)}/ws`
      return new WebSocket(url, ['bearer', accessToken])
    },
    [accessToken],
  )

  const value = useMemo(
    () => ({ status, user, login, logout, request, connectRealtime }),
    [status, user, login, logout, request, connectRealtime],
  )
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
