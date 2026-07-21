import { createContext } from 'react'
import type { User } from '../api/client'

export type AuthStatus = 'loading' | 'authenticated' | 'unauthenticated'

export type AuthContextValue = {
  status: AuthStatus
  user: User | null
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  request: <T>(path: string, init?: RequestInit) => Promise<T>
  connectRealtime: (organisationId: string) => WebSocket | null
}

export const AuthContext = createContext<AuthContextValue | null>(null)
