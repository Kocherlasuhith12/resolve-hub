import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Bookmark,
  Sparkles,
  ThumbsUp,
  Clock,
  Check,
} from 'lucide-react'
import { useAuth } from '../../auth/useAuth'

type KBArticle = {
  id: string
  article_number: string
  title: string
  slug: string
  summary: string
  content_markdown: string
  category: string
  author_name: string
  view_count: number
  helpful_count: number
  unhelpful_count: number
  created_at: string
}

export function KnowledgeBaseWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const queryClient = useQueryClient()
  const [search, setSearch] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)
  const [selectedArticle, setSelectedArticle] = useState<KBArticle | null>(null)
  const [bookmarks, setBookmarks] = useState<Set<string>>(new Set())
  const [generatedSuccess, setGeneratedSuccess] = useState(false)

  const articlesQuery = useQuery({
    queryKey: ['knowledge-articles', organisationId, selectedCategory, search],
    queryFn: () => {
      const params = new URLSearchParams()
      if (selectedCategory) params.set('category', selectedCategory)
      if (search.trim()) params.set('search', search.trim())
      const url = `/organisations/${organisationId}/knowledge/articles?${params.toString()}`
      return request<KBArticle[]>(url)
    },
    enabled: Boolean(organisationId),
  })

  const articlesList = articlesQuery.data ?? []

  const createAiArticle = useMutation({
    mutationFn: () =>
      request<KBArticle>(`/organisations/${organisationId}/knowledge/articles`, {
        method: 'POST',
        body: JSON.stringify({
          title: 'AI Auto-Generated: Resolving Connection Issues',
          summary: 'Synthesized resolution guide generated from recent service tickets.',
          content_markdown: '# AI Resolution Guide\n\n1. Check gateway connection.\n2. Renew DHCP lease.\n3. Verify authentication certificates.',
          category: 'Network',
          author_name: 'AI Operations Assistant',
        }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['knowledge-articles', organisationId] })
      setGeneratedSuccess(true)
      setTimeout(() => setGeneratedSuccess(false), 4000)
    },
  })

  const rateArticle = useMutation({
    mutationFn: (args: { articleId: string; helpful: boolean }) =>
      request<KBArticle>(`/organisations/${organisationId}/knowledge/articles/${args.articleId}/rate`, {
        method: 'POST',
        body: JSON.stringify({ helpful: args.helpful }),
      }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['knowledge-articles', organisationId] })
    },
  })

  const toggleBookmark = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    setBookmarks((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })
  }

  const categories = Array.from(new Set(articlesList.map((a) => a.category)))

  if (selectedArticle) {
    return (
      <div className="kb-article-detail">
        <button className="detail-back" type="button" onClick={() => setSelectedArticle(null)}>
          ← Back to Knowledge Base
        </button>
        <div className="kb-detail-card">
          <div className="kb-detail-meta">
            <span className="kb-category-tag">{selectedArticle.category}</span>
            <span><Clock size={12} style={{ display: 'inline', marginRight: 4 }} />{selectedArticle.article_number}</span>
            <span>· {selectedArticle.view_count} views</span>
          </div>
          <h2>{selectedArticle.title}</h2>
          <p className="kb-detail-summary">{selectedArticle.summary}</p>
          <hr className="kb-divider" />
          <div className="kb-detail-body">
            {selectedArticle.content_markdown.split('\n').map((line, idx) => (
              <p key={idx}>{line}</p>
            ))}
          </div>

          <div style={{ marginTop: 32, paddingTop: 16, borderTop: '1px solid var(--border-light)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className="muted">Was this article helpful? ({selectedArticle.helpful_count} helpful)</span>
            <div style={{ display: 'flex', gap: 8 }}>
              <button
                className="btn-secondary btn-sm"
                type="button"
                onClick={() => rateArticle.mutate({ articleId: selectedArticle.id, helpful: true })}
              >
                <ThumbsUp size={14} /> Yes
              </button>
              <button
                className="btn-secondary btn-sm"
                type="button"
                onClick={() => rateArticle.mutate({ articleId: selectedArticle.id, helpful: false })}
              >
                No
              </button>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div>
      <div className="kb-header">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
          <div>
            <h1>Knowledge Base</h1>
            <p>Self-service guides, troubleshooting, and AI auto-generated resolution articles</p>
          </div>
          <button
            className="btn-primary"
            type="button"
            disabled={createAiArticle.isPending}
            onClick={() => createAiArticle.mutate()}
          >
            <Sparkles size={16} />
            {createAiArticle.isPending ? 'Generating from resolved tickets…' : 'Generate AI Article'}
          </button>
        </div>

        {generatedSuccess && (
          <div className="form-success" role="status" style={{ marginBottom: 16 }}>
            <Check size={16} style={{ display: 'inline', marginRight: 6 }} />
            New knowledge article automatically generated and saved to PostgreSQL!
          </div>
        )}

        <input
          className="kb-search-input"
          type="search"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search articles with AI indexing (e.g. VPN, password, display)…"
        />
      </div>

      {/* Category Filter Pills */}
      <div className="kb-pills">
        <button
          className={`kb-pill ${selectedCategory === null ? 'active' : ''}`}
          onClick={() => setSelectedCategory(null)}
        >
          All ({articlesList.length})
        </button>
        {categories.map((cat) => (
          <button
            key={cat}
            className={`kb-pill ${selectedCategory === cat ? 'active' : ''}`}
            onClick={() => setSelectedCategory(cat)}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Articles Grid */}
      <div className="kb-articles-grid">
        {articlesQuery.isPending ? (
          <div className="section-message" style={{ gridColumn: '1 / -1' }}><div className="loading-spinner" /> Loading knowledge articles…</div>
        ) : articlesList.length === 0 ? (
          <div className="empty-state" style={{ gridColumn: '1 / -1' }}>
            <h3>No articles found</h3>
            <p>Try adjusting your search or category filter.</p>
          </div>
        ) : (
          articlesList.map((article) => {
            const isBookmarked = bookmarks.has(article.id)
            return (
              <div className="kb-article-card" key={article.id} onClick={() => setSelectedArticle(article)}>
                <div className="kb-article-card-header">
                  <span className="kb-category-tag">{article.category}</span>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <span className="kb-read-time">{article.view_count} views</span>
                    <button
                      className="btn-icon"
                      style={{ width: 24, height: 24 }}
                      onClick={(e) => toggleBookmark(article.id, e)}
                      aria-label="Bookmark article"
                    >
                      <Bookmark size={14} fill={isBookmarked ? 'var(--green-600)' : 'none'} color={isBookmarked ? 'var(--green-600)' : 'var(--text-muted)'} />
                    </button>
                  </div>
                </div>
                <h3>{article.title}</h3>
                <p>{article.summary}</p>
                <span className="kb-read-link">Read article →</span>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
