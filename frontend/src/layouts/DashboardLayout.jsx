import { Link, useNavigate } from "react-router-dom";
import { LayoutDashboard, LogOut, User } from "lucide-react";

import { signOut } from "../services/auth.service";
import Button from "../components/ui/Button";

export default function DashboardLayout({ children }) {
  const navigate = useNavigate();

  async function handleLogout() {
    await signOut();
    navigate("/");
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <Link
            to="/dashboard"
            className="text-xl font-bold text-slate-900"
          >
            ScholaAI
          </Link>

          <nav className="flex items-center gap-4">
            <Link
              to="/dashboard"
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
            >
              <LayoutDashboard size={18} />
              Dashboard
            </Link>

            <Link
              to="/profile"
              className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900"
            >
              <User size={18} />
              Profile
            </Link>

            <Button
              variant="secondary"
              onClick={handleLogout}
            >
              <LogOut size={18} />
              Logout
            </Button>
          </nav>
        </div>
      </header>

      {children}
    </div>
  );
}
