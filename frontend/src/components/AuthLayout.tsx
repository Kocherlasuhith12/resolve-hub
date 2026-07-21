import type { ReactNode } from 'react'
import { Brand } from './Brand'

export function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <main className="login-layout">
      <section className="login-story" aria-labelledby="welcome-title">
        <Brand />
        <div className="story-copy">
          <p className="eyebrow">One place. Clear ownership.</p>
          <h1 id="welcome-title">Turn every request into visible progress.</h1>
          <p>
            Bring service requests, conversations, and response commitments together—without
            losing sight of the people waiting for help.
          </p>
        </div>
        <p className="story-footnote">Secure, tenant-isolated operations for every team.</p>
      </section>

      <section className="login-panel">
        <div className="mobile-brand"><Brand /></div>
        {children}
      </section>
    </main>
  )
}
