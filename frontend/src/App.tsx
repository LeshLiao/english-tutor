import { NavLink, Outlet } from 'react-router-dom'

export default function App() {
  return (
    <>
      <header className="topbar">
        <NavLink to="/" className="brand">
          English Tutor
        </NavLink>
        <nav>
          <NavLink to="/" end>
            總覽
          </NavLink>
          <NavLink to="/sentences">句子列表</NavLink>
        </nav>
      </header>
      <main className="page">
        <Outlet />
      </main>
    </>
  )
}
