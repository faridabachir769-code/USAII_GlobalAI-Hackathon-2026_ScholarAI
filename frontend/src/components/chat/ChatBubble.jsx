import { useState, useRef, useEffect } from "react";
import { MessageCircle, X, Send, Bot, User, Loader2, Maximize2, Minimize2 } from "lucide-react";
import { sendChatMessage } from "../../services/chat.service";

export default function ChatBubble() {
  const [open, setOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", content: "Hi! I'm your ScholarAI assistant. Ask me about scholarships, schemes, or eligibility criteria!" }
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || loading) return;
    const userMsg = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: userMsg }]);
    setLoading(true);
    try {
      const res = await sendChatMessage(userMsg);
      setMessages((prev) => [...prev, { role: "assistant", content: res.response || "I couldn't process that. Please try again." }]);
      if (res.matched_schemes?.length > 0) {
        const schemes = res.matched_schemes.slice(0, 5);
        setMessages((prev) => [
          ...prev,
          {
            role: "assistant",
            content: `**Found ${res.matched_schemes.length} matching schemes:**\n${schemes.map((s, i) => `${i + 1}. **${s.name}** — ${s.ministry || ""} ${s.match_reasons?.length ? `(✓ ${s.match_reasons.join(", ")})` : ""}`).join("\n")}`,
          },
        ]);
      }
    } catch {
      setMessages((prev) => [...prev, { role: "assistant", content: "Sorry, I'm having trouble connecting. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const containerClass = expanded
    ? "fixed inset-4 z-50 flex flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl"
    : "fixed bottom-4 right-4 z-50 flex w-[380px] flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl max-h-[600px]";

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 z-50 flex h-14 w-14 items-center justify-center rounded-full bg-blue-600 text-white shadow-lg hover:bg-blue-700 transition-all duration-200 hover:scale-105"
      >
        <MessageCircle size={26} />
      </button>
    );
  }

  return (
    <div className={containerClass}>
      <div className="flex items-center justify-between rounded-t-2xl border-b border-slate-200 bg-gradient-to-r from-blue-600 to-blue-700 px-4 py-3 text-white">
        <div className="flex items-center gap-2">
          <Bot size={22} />
          <span className="font-semibold">ScholarAI Assistant</span>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => setExpanded(!expanded)}
            className="rounded-lg p-1.5 hover:bg-white/20 transition-colors"
          >
            {expanded ? <Minimize2 size={18} /> : <Maximize2 size={18} />}
          </button>
          <button
            onClick={() => setOpen(false)}
            className="rounded-lg p-1.5 hover:bg-white/20 transition-colors"
          >
            <X size={18} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-3 bg-slate-50/50">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`flex gap-2 max-w-[85%] ${
                msg.role === "user" ? "flex-row-reverse" : "flex-row"
              }`}
            >
              <div
                className={`mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full ${
                  msg.role === "user" ? "bg-blue-100" : "bg-slate-200"
                }`}
              >
                {msg.role === "user" ? <User size={14} className="text-blue-600" /> : <Bot size={14} className="text-slate-600" />}
              </div>
              <div
                className={`rounded-2xl px-4 py-2 text-sm leading-relaxed whitespace-pre-wrap ${
                  msg.role === "user"
                    ? "bg-blue-600 text-white rounded-tr-sm"
                    : "bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm"
                }`}
              >
                {msg.content}
              </div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="flex gap-2 max-w-[85%]">
              <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-200">
                <Bot size={14} className="text-slate-600" />
              </div>
              <div className="rounded-2xl rounded-tl-sm bg-white border border-slate-200 px-4 py-3 shadow-sm">
                <Loader2 size={18} className="animate-spin text-blue-600" />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="border-t border-slate-200 p-3">
        <div className="flex gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about scholarships..."
            disabled={loading}
            className="h-11 flex-1 rounded-xl border border-slate-300 bg-white px-4 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-100 disabled:opacity-50"
          />
          <button
            onClick={handleSend}
            disabled={loading || !input.trim()}
            className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
          </button>
        </div>
      </div>
    </div>
  );
}
