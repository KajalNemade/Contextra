import { Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import UploadPage from './pages/UploadPage'
import DashboardPage from './pages/DashboardPage'
import RepoView from './pages/RepoView'
import GraphView from './pages/GraphView'
import AskPage from './pages/AskPage'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/repo/:id" element={<RepoView />} />
        <Route path="/repo/:id/dashboard" element={<DashboardPage />} />
        <Route path="/repo/:id/graph" element={<GraphView />} />
        <Route path="/repo/:id/ask" element={<AskPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
