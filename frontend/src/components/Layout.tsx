import { Outlet, NavLink, useParams, useNavigate } from 'react-router-dom'

const Logo = () => (
  <div className="flex items-center gap-2 px-4 py-5 border-b border-gray-800 flex-shrink-0">
    <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center font-bold text-white text-sm select-none">D</div>
    <div>
      <div className="font-semibold text-white text-sm leading-none">DCRS</div>
      <div className="text-gray-500 text-xs mt-0.5">Context Recovery</div>
    </div>
  </div>
)

function NavItem({ to, label, icon }: { to: string; label: string; icon: string }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
          isActive
            ? 'bg-brand-500/15 text-brand-400 font-medium'
            : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`
      }
    >
      <span>{icon}</span>
      {label}
    </NavLink>
  )
}

export default function Layout() {
  const { id } = useParams()
  const navigate = useNavigate()

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950">
      {/* Sidebar */}
      <aside className="w-56 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col">
        <button onClick={() => navigate('/')} className="text-left">
          <Logo />
        </button>

        <nav className="flex-1 overflow-y-auto p-3 space-y-1">
          <NavItem to="/" label="All Repos" icon="📁" />
          <NavItem to="/upload" label="Add Repo" icon="➕" />

          {id && (
            <>
              <div className="pt-4 pb-1 px-3 text-xs font-medium text-gray-600 uppercase tracking-wider">
                This Repo
              </div>
              <NavItem to={`/repo/${id}`}           label="Overview"    icon="🏠" />
              <NavItem to={`/repo/${id}/dashboard`} label="Dashboard"   icon="📊" />
              <NavItem to={`/repo/${id}/graph`}     label="Dep. Graph"  icon="🕸" />
              <NavItem to={`/repo/${id}/ask`}       label="Ask AI"      icon="💬" />
            </>
          )}
        </nav>

        <div className="p-3 border-t border-gray-800 text-xs text-gray-600">
          V1 · Local · No cloud required
        </div>
      </aside>

      {/* Page content */}
      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
