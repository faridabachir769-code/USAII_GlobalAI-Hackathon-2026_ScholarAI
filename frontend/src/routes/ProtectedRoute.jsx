import { Navigate } from "react-router-dom";

import { useAuth } from "../context/AuthContext";

import Loader from "../components/ui/Loader";

export default function ProtectedRoute({
  children,
}) {
  const { user, loading } =
    useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Loader text="Loading..." />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  return children;
}