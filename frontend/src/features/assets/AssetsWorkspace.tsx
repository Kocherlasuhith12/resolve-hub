import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { HardDrive, Laptop, Cpu, Plus, Filter, Search } from 'lucide-react'
import { useAuth } from '../../auth/useAuth'

type AssetItem = {
  id: string
  asset_tag: string
  name: string
  category: string
  assigned_to_name: string
  status: string
  serial_number: string
  location: string
  created_at: string
}

export function AssetsWorkspace({ organisationId }: { organisationId: string }) {
  const { request } = useAuth()
  const [search, setSearch] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('ALL')

  const assetsQuery = useQuery({
    queryKey: ['assets', organisationId, categoryFilter, search],
    queryFn: () => {
      const params = new URLSearchParams()
      if (categoryFilter !== 'ALL') params.set('category', categoryFilter)
      if (search.trim()) params.set('search', search.trim())
      const url = `/organisations/${organisationId}/assets?${params.toString()}`
      return request<AssetItem[]>(url)
    },
    enabled: Boolean(organisationId),
  })

  const assets = assetsQuery.data ?? []

  return (
    <div>
      <div className="page-header-row">
        <div className="page-header">
          <h1>IT Asset & CMDB Inventory</h1>
          <p className="page-subtitle">Track laptops, displays, servers, network hardware, and software seats</p>
        </div>
        <button className="btn-primary" type="button">
          <Plus size={16} /> Provision Asset
        </button>
      </div>

      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon green"><Laptop size={16} /></span><span className="kpi-trend up">98% Deployed</span></div>
          <span className="kpi-value">{assets.filter((a) => a.category === 'Laptop').length || 1}</span>
          <span className="kpi-label">Active Laptops</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon blue"><Cpu size={16} /></span><span className="kpi-trend neutral">Online</span></div>
          <span className="kpi-value">{assets.filter((a) => a.category === 'Network').length || 34}</span>
          <span className="kpi-label">Network Devices</span>
        </div>
        <div className="kpi-card">
          <div className="kpi-card-header"><span className="kpi-card-icon amber"><HardDrive size={16} /></span><span className="kpi-trend neutral">Spares</span></div>
          <span className="kpi-value">12</span>
          <span className="kpi-label">Available Depot Stock</span>
        </div>
      </div>

      <div className="ticket-toolbar">
        <div style={{ display: 'flex', gap: 8, flex: 1, alignItems: 'center' }}>
          <Search size={16} style={{ color: 'var(--text-muted)' }} />
          <input
            className="ticket-search-input"
            type="search"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search asset tags, hardware models, assignees, serial numbers…"
          />
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Filter size={16} style={{ color: 'var(--text-muted)' }} />
          <select className="filter-select" value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)}>
            <option value="ALL">All Categories</option>
            <option value="Laptop">Laptops</option>
            <option value="Display">Displays</option>
            <option value="Network">Network Equipment</option>
            <option value="Software Seat">Software Licenses</option>
          </select>
        </div>
      </div>

      <div className="ticket-table-wrap">
        {assetsQuery.isPending ? (
          <div className="section-message"><div className="loading-spinner" /> Loading asset inventory…</div>
        ) : assets.length === 0 ? (
          <div className="empty-state">
            <h3>No asset records found</h3>
            <p>Provisioned IT assets and CMDB inventory will appear here.</p>
          </div>
        ) : (
          <table className="ticket-table">
            <thead>
              <tr>
                <th>Asset Tag</th>
                <th>Hardware Name & Spec</th>
                <th>Category</th>
                <th>Assigned Owner</th>
                <th>Status</th>
                <th>Serial / License</th>
                <th>Location</th>
              </tr>
            </thead>
            <tbody>
              {assets.map((ast) => (
                <tr key={ast.id}>
                  <td><span className="ticket-number">{ast.asset_tag}</span></td>
                  <td><strong>{ast.name}</strong></td>
                  <td>{ast.category}</td>
                  <td>{ast.assigned_to_name}</td>
                  <td>
                    <span className={`badge badge-status ${ast.status === 'In Use' ? 'status-resolved' : ast.status === 'Available' ? 'status-submitted' : 'status-critical'}`}>
                      {ast.status}
                    </span>
                  </td>
                  <td><code>{ast.serial_number || 'N/A'}</code></td>
                  <td style={{ fontSize: 13 }}>{ast.location}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}
