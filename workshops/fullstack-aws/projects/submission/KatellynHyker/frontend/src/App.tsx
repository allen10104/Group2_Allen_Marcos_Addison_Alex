import { Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { LoginPage } from './pages/Login'
import { RegisterPage } from './pages/Register'
import { BoardPage } from './pages/Board'
import { PeoplePage } from './pages/People'
import './App.css'

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route
        path="/board"
        element={
          <ProtectedRoute>
            <BoardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/people"
        element={
          <ProtectedRoute>
            <PeoplePage />
          </ProtectedRoute>
        }
      />
      <Route path="/" element={<Navigate to="/board" replace />} />
      <Route path="*" element={<Navigate to="/board" replace />} />
    </Routes>
  )
}

export default App