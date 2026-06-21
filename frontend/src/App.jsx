import { Routes, Route } from "react-router-dom";

import Login from "./pages/Login";
import Register from "./pages/Register";
import ProfileSetup from "./pages/ProfileSetup";
import Dashboard from "./pages/Dashboard";
import Comparison from "./pages/Comparison";
import DecisionReport from "./pages/DecisionReport";
import WhatIfSimulator from "./pages/WhatIfSimulator";

import ProtectedRoute from "./routes/ProtectedRoute";

export default function App() {
  return (
    <Routes>
      <Route
        path="/"
        element={<Login />}
      />

      <Route
        path="/register"
        element={<Register />}
      />

      <Route
        path="/profile"
        element={
          <ProtectedRoute>
            <ProfileSetup />
          </ProtectedRoute>
        }
      />

      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/comparison"
        element={
          <ProtectedRoute>
            <Comparison />
          </ProtectedRoute>
        }
      />

      <Route
        path="/decision-report"
        element={
          <ProtectedRoute>
            <DecisionReport />
          </ProtectedRoute>
        }
      />

      <Route
        path="/what-if"
        element={
          <ProtectedRoute>
            <WhatIfSimulator />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}