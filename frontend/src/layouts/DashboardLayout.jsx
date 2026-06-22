import { Link, useNavigate } from "react-router-dom";
import { LayoutDashboard, LogOut, User, Search, MessageCircle } from "lucide-react";
import { useState } from "react";
import { signOut } from "../services/auth.service";
import Button from "../components/ui/Button";
import ChatBubble from "../components/chat/ChatBubble";

export default function DashboardLayout({ children }) {
  const navigate = useNavigate();
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");

  async function handleLogout() {
    await signOut();
    navigate("/");
  }

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/dashboard?search=${encodeURIComponent(searchQuery.trim())}`);
      setSearchOpen(false);
      setSearchQuery("");
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white shadow-sm">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-3">
          <Link
            to="/dashboard"
            className="text-xl font-bold bg-gradient-to-r from-blue-600 to-blue-800 bg-clip-text text-transparent"
          >
            ScholarAI
          </Link>

          <div className="hidden md:flex items-center flex-1 max-w-md mx-6">
            <form onSubmit={handleSearch} className="relative w-full">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search schemes..."
                className="h-10 w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:bg-white focus:ring-2 focus:ring-blue-100 transition-all"
              />
            </form>
          </div>

          <nav className="flex items-center gap-3">
            <button
              onClick={() => setSearchOpen(!searchOpen)}
              className="flex md:hidden h-10 w-10 items-center justify-center rounded-xl text-slate-600 hover:bg-slate-100"
            >
              <Search size={18} />
            </button>

            <Link
              to="/dashboard"
              className="hidden sm:flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <LayoutDashboard size={18} />
              <span className="hidden lg:inline">Dashboard</span>
            </Link>

            <Link
              to="/comparison"
              className="hidden sm:flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <LayoutDashboard size={18} />
              <span className="hidden lg:inline">Compare</span>
            </Link>

            <Link
              to="/profile"
              className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-slate-600 hover:bg-slate-100 transition-colors"
            >
              <User size={18} />
              <span className="hidden lg:inline">Profile</span>
            </Link>

            <Button
              variant="secondary"
              onClick={handleLogout}
              className="!h-10 !px-3"
            >
              <LogOut size={18} />
              <span className="hidden lg:inline">Logout</span>
            </Button>
          </nav>
        </div>
        {searchOpen && (
          <div className="md:hidden border-t border-slate-200 px-4 py-2">
            <form onSubmit={handleSearch} className="relative">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search schemes..."
                autoFocus
                className="h-10 w-full rounded-xl border border-slate-300 bg-white pl-10 pr-4 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100"
              />
            </form>
          </div>
        )}
      </header>

      {children}
      <ChatBubble />
    </div>
  );
}
