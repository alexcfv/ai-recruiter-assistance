import { useState, useRef, useEffect } from "react";
import { Send, Search, BarChart3, Loader2, Bot, User } from "lucide-react";

type Role = "user" | "assistant";

interface Message {
  id: string;
  role: Role;
  text: string;
  timestamp: Date;
}

interface ChatPanelProps {
  id: "search" | "analytics";
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  accentColor: string;
  placeholderText: string;
  initialMessages: Message[];
  suggestedPrompts: string[];
}

const SEARCH_MESSAGES: Message[] = [
  {
    id: "s1",
    role: "assistant",
    text: "Hello! I'm your Recruiter Assistant. I can help you find top candidates, filter by skills, experience, location, or seniority. What kind of talent are you looking for today?",
    timestamp: new Date(Date.now() - 420000),
  },
  {
    id: "s2",
    role: "user",
    text: "Find me senior full-stack engineers with React and Node.js, based in Europe, with 5+ years experience.",
    timestamp: new Date(Date.now() - 360000),
  },
  {
    id: "s3",
    role: "assistant",
    text: "Found **47 candidates** matching your criteria. Here are the top matches:\n\n• **Alina Kovač** — 8 yrs · React, Node.js, TypeScript · Ljubljana, SI · Open to work\n• **Markus Heinz** — 6 yrs · React, Next.js, GraphQL · Berlin, DE · Actively looking\n• **Priya Nair** — 7 yrs · React, Node, AWS · Amsterdam, NL · Passive candidate\n• **Tomáš Novák** — 5 yrs · React, Express, PostgreSQL · Prague, CZ · Open to work\n\nShall I refine by salary range or company size preference?",
    timestamp: new Date(Date.now() - 300000),
  },
  {
    id: "s4",
    role: "user",
    text: "Show me only those with fintech experience and above €90k expectation.",
    timestamp: new Date(Date.now() - 180000),
  },
  {
    id: "s5",
    role: "assistant",
    text: "Narrowed to **12 candidates** with fintech background and €90k+ salary expectation.\n\n• **Alina Kovač** — Revolut alum · €105k expectation · Excellent match\n• **Markus Heinz** — N26, Commerzbank · €95k expectation · Strong match\n• **Priya Nair** — Adyen, ING · €110k expectation · Strong match\n\nWant me to draft outreach messages or schedule interview slots?",
    timestamp: new Date(Date.now() - 60000),
  },
];

const ANALYTICS_MESSAGES: Message[] = [
  {
    id: "a1",
    role: "assistant",
    text: "Hi! I'm your DB Analytics assistant. Ask me anything about your candidate database — pipeline stats, sourcing channels, time-to-hire metrics, or funnel conversion rates.",
    timestamp: new Date(Date.now() - 500000),
  },
  {
    id: "a2",
    role: "user",
    text: "What's our current pipeline conversion rate this quarter?",
    timestamp: new Date(Date.now() - 440000),
  },
  {
    id: "a3",
    role: "assistant",
    text: "**Q2 2026 Pipeline Conversion (Apr–Jun)**\n\n```\nApplied      →  Screened     64.2%  (1,847 → 1,186)\nScreened     →  Interview    38.1%  (1,186 → 452)\nInterview    →  Offer        22.6%  (452 → 102)\nOffer        →  Hired        81.4%  (102 → 83)\n```\n\nOverall funnel: **4.5%** applied-to-hired. Up **+1.2pp** vs Q1. The interview-to-offer drop at 22.6% is your biggest bottleneck — want a breakdown by role?",
    timestamp: new Date(Date.now() - 380000),
  },
  {
    id: "a4",
    role: "user",
    text: "Yes, and also show me which sourcing channels are performing best.",
    timestamp: new Date(Date.now() - 220000),
  },
  {
    id: "a5",
    role: "assistant",
    text: "**Top Sourcing Channels — Q2 2026**\n\n```\nChannel          Leads   Hired   Conv.   Cost/Hire\nLinkedIn         893     31      3.5%    €1,240\nReferrals        214     28      13.1%   €380\nDirect outreach  301     15      5.0%    €820\nJob boards       639      9      1.4%    €2,100\n```\n\nReferrals are 3.7× more efficient than LinkedIn at 13.1% conversion. Recommend increasing referral incentive budget by €5k to scale that channel.",
    timestamp: new Date(Date.now() - 90000),
  },
];

function formatTime(date: Date): string {
  return date.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

function formatMessage(text: string): React.ReactNode {
  const parts = text.split(/(```[\s\S]*?```|\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("```") && part.endsWith("```")) {
      const code = part.slice(3, -3).trim();
      return (
        <pre key={i} className="mt-2 mb-1 rounded bg-[#0a1221] border border-[rgba(45,212,191,0.15)] px-3 py-2 text-xs font-mono text-[#a8bdd4] overflow-x-auto whitespace-pre">
          {code}
        </pre>
      );
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i} className="text-white font-semibold">{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

function MessageBubble({ message, accentColor }: { message: Message; accentColor: string }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex gap-2.5 ${isUser ? "flex-row-reverse" : "flex-row"} group`}>
      <div
        className={`w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5 ${
          isUser ? "bg-[#1a2d4a]" : ""
        }`}
        style={!isUser ? { background: `${accentColor}22`, border: `1px solid ${accentColor}44` } : {}}
      >
        {isUser
          ? <User size={13} className="text-[#6b8aaa]" />
          : <Bot size={13} style={{ color: accentColor }} />
        }
      </div>

      <div className={`max-w-[78%] flex flex-col gap-0.5 ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-[#1a2d4a] text-[#c8dcea] rounded-tr-sm"
              : "bg-[#162238] text-[#d4e4f0] rounded-tl-sm border border-[rgba(45,212,191,0.08)]"
          }`}
        >
          {formatMessage(message.text)}
        </div>
        <span className="text-[10px] text-[#3d5a78] px-1 opacity-0 group-hover:opacity-100 transition-opacity">
          {formatTime(message.timestamp)}
        </span>
      </div>
    </div>
  );
}

function TypingIndicator({ accentColor }: { accentColor: string }) {
  return (
    <div className="flex gap-2.5 flex-row">
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center flex-shrink-0"
        style={{ background: `${accentColor}22`, border: `1px solid ${accentColor}44` }}
      >
        <Bot size={13} style={{ color: accentColor }} />
      </div>
      <div className="bg-[#162238] border border-[rgba(45,212,191,0.08)] rounded-2xl rounded-tl-sm px-4 py-3 flex items-center gap-1">
        {[0, 1, 2].map((i) => (
          <span
            key={i}
            className="w-1.5 h-1.5 rounded-full animate-bounce"
            style={{ background: accentColor, animationDelay: `${i * 150}ms`, opacity: 0.7 }}
          />
        ))}
      </div>
    </div>
  );
}

function ChatPanel({ id, title, subtitle, icon, accentColor, placeholderText, initialMessages, suggestedPrompts }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [input, setInput] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (listRef.current) {
      listRef.current.scrollTop = listRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  function sendMessage(text: string) {
    if (!text.trim()) return;
    const userMsg: Message = {
      id: `${id}-${Date.now()}`,
      role: "user",
      text: text.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsTyping(true);

    setTimeout(() => {
      const replies: Record<string, string> = {
        search: "Searching the candidate database for your query... I found several strong matches. Would you like me to filter by availability or add any additional criteria?",
        analytics: "Running the query against your database... Here are the latest statistics. The data shows clear trends worth discussing with your hiring team.",
      };
      const assistantMsg: Message = {
        id: `${id}-reply-${Date.now()}`,
        role: "assistant",
        text: replies[id],
        timestamp: new Date(),
      };
      setIsTyping(false);
      setMessages((prev) => [...prev, assistantMsg]);
    }, 1400 + Math.random() * 600);
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  return (
    <div
      id={id === "search" ? "SearchChat" : "AnalyticsChat"}
      className="flex flex-col h-full bg-card rounded-xl border overflow-hidden"
      style={{ borderColor: `${accentColor}20` }}
    >
      {/* Panel header */}
      <div
        className="flex items-center gap-3 px-4 py-3.5 border-b flex-shrink-0"
        style={{
          borderColor: `${accentColor}18`,
          background: `linear-gradient(135deg, #0f1c30 0%, #111e32 100%)`,
        }}
      >
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0"
          style={{ background: `${accentColor}18`, border: `1px solid ${accentColor}30` }}
        >
          <span style={{ color: accentColor }}>{icon}</span>
        </div>
        <div className="min-w-0">
          <h2 className="text-sm font-semibold text-white leading-tight">{title}</h2>
          <p className="text-[11px] text-[#4d7090] leading-tight mt-0.5">{subtitle}</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <span
            className="w-1.5 h-1.5 rounded-full animate-pulse"
            style={{ background: accentColor }}
          />
          <span className="text-[10px] font-medium" style={{ color: accentColor }}>Live</span>
        </div>
      </div>

      {/* MessageList */}
      <div
        id="MessageList"
        ref={listRef}
        className="flex-1 overflow-y-auto px-4 py-4 flex flex-col gap-4 scroll-smooth"
        style={{ scrollbarWidth: "none" }}
      >
        {messages.map((msg) => (
          <MessageBubble key={msg.id} message={msg} accentColor={accentColor} />
        ))}
        {isTyping && <TypingIndicator accentColor={accentColor} />}
      </div>

      {/* ChatInput */}
      <div
        id="ChatInput"
        className="px-4 pb-4 flex-shrink-0"
      >
        <div
          className="flex items-center gap-3 rounded-xl px-4 py-3 border transition-all"
          style={{
            background: "#0f1c2e",
            borderColor: input ? `${accentColor}40` : "rgba(45,212,191,0.12)",
          }}
        >
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholderText}
            className="flex-1 bg-transparent text-sm text-[#c8dcea] placeholder-[#3a5570] outline-none"
            style={{ fontFamily: "Inter, sans-serif" }}
          />
          <button
            onClick={() => sendMessage(input)}
            disabled={!input.trim() || isTyping}
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-all disabled:opacity-30"
            style={{
              background: input.trim() && !isTyping ? accentColor : "transparent",
              border: `1px solid ${accentColor}50`,
            }}
          >
            {isTyping
              ? <Loader2 size={14} className="animate-spin" style={{ color: accentColor }} />
              : <Send size={13} style={{ color: input.trim() ? "#0a1628" : accentColor }} />
            }
          </button>
        </div>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <div
      className="size-full grid grid-cols-2 gap-px overflow-hidden"
      style={{ fontFamily: "Inter, sans-serif", background: "#0d1626" }}
    >
      <ChatPanel
        id="search"
        title="Recruiter Assistant"
        subtitle="Candidate search & matching"
        icon={<Search size={16} />}
        accentColor="#2dd4bf"
        placeholderText="Search candidates by skill, role, location…"
        initialMessages={SEARCH_MESSAGES}
        suggestedPrompts={[]}
      />
      <ChatPanel
        id="analytics"
        title="DB Analytics"
        subtitle="Database queries & pipeline stats"
        icon={<BarChart3 size={16} />}
        accentColor="#0ea5e9"
        placeholderText="Query your database or ask for a report…"
        initialMessages={ANALYTICS_MESSAGES}
        suggestedPrompts={[]}
      />
    </div>
  );
}
