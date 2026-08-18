// This file defines the main App component, which sets up the routing and authentication context for the application.

import { BrowserRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { Navbar } from "./components/Navbar";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { LoginPage } from "./pages/LoginPage";
import { RegisterPage } from "./pages/RegisterPage";
import { VerifyManagerPage } from "./pages/VerifyManagerPage";
import { FeedPage } from "./pages/FeedPage";
import { SubmitNoticePage } from "./pages/SubmitNoticePage";
import { ApprovalQueuePage } from "./pages/ApprovalQueuePage";
import { CreateEmployeePage } from "./pages/CreateEmployeePage";
import { InviteCodesPage } from "./pages/InviteCodesPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Navbar />
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/verify-manager" element={<VerifyManagerPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <FeedPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/submit"
            element={
              <ProtectedRoute>
                <SubmitNoticePage />
              </ProtectedRoute>
            }
          />

          <Route
            path="/approvals"
            element={
              <ProtectedRoute role="MANAGER">
                <ApprovalQueuePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/employees"
            element={
              <ProtectedRoute role="MANAGER">
                <CreateEmployeePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/invite-codes"
            element={
              <ProtectedRoute role="MANAGER">
                <InviteCodesPage />
              </ProtectedRoute>
            }
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
