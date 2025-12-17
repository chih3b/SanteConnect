import { useState, useEffect, useRef, useCallback } from "react";
import { useAuth } from "./AuthContext";
import { Button } from "./ui/button";
import DocumentAnalysis from "./DocumentAnalysis";
import ThemeToggle from "./ThemeToggle";
import {
  Upload,
  Send,
  Calendar,
  Loader,
  ExternalLink,
  Clock,
  LogOut,
  Mail,
  Plus,
  Bot,
  Stethoscope,
  RefreshCw,
  X,
  Check,
  Brain,
  Menu,
  History,
  Trash2,
  Edit3,
  Target,
  GitBranch,
  Cpu,
  Activity,
  Layers,
  Sparkles,
  BarChart3,
  FileText,
} from "lucide-react";

const API_BASE = "http://localhost:8003/api/assistant";

// Confidence Badge Component
const ConfidenceBadge = ({ level, score }) => {
  const config = {
    high: { bg: "bg-green-100", text: "text-green-700" },
    medium: { bg: "bg-amber-100", text: "text-amber-700" },
    low: { bg: "bg-red-100", text: "text-red-700" },
  };
  const style = config[level] || config.medium;

  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${style.bg} ${style.text}`}>
      {(score * 100).toFixed(0)}%
    </span>
  );
};

// Email Preview Component with Edit
const EmailPreviewCard = ({ content, onSend, onCancel }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editedMessage, setEditedMessage] = useState("");

  const parseEmailContent = (text) => {
    const toMatch = text.match(/\*\*To:\*\*\s*([^\n*]+)/);
    const subjectMatch = text.match(/\*\*Subject:\*\*\s*([^\n*]+)/);
    const messageMatch = text.match(/\*\*Message:\*\*\s*([\s\S]*?)(?=\n\n---|\n---)/);
    return {
      to: toMatch ? toMatch[1].trim() : "",
      subject: subjectMatch ? subjectMatch[1].trim() : "",
      message: messageMatch ? messageMatch[1].trim() : "",
    };
  };

  const emailData = parseEmailContent(content);

  const handleStartEdit = () => {
    setEditedMessage(emailData.message);
    setIsEditing(true);
  };

  return (
    <div className="w-full">
      <div className="flex items-center gap-2 mb-3 text-amber-700 font-semibold border-b border-amber-200 pb-2">
        <Mail className="w-5 h-5" />
        Email Preview - Review Before Sending
      </div>

      <div className="bg-card rounded-lg p-3 mb-3 border border-amber-200">
        <div className="flex items-center gap-2 text-sm mb-2">
          <span className="font-medium text-muted-foreground w-16">To:</span>
          <span className="text-foreground font-medium">{emailData.to}</span>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <span className="font-medium text-muted-foreground w-16">Subject:</span>
          <span className="text-foreground">{emailData.subject}</span>
        </div>
      </div>

      <div className="bg-card rounded-lg p-4 border border-amber-200 mb-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs font-medium text-muted-foreground uppercase tracking-wide">Message</span>
          {!isEditing && (
            <button onClick={handleStartEdit} className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-700 font-medium">
              <Edit3 className="w-3 h-3" />
              Edit
            </button>
          )}
        </div>
        {isEditing ? (
          <div>
            <textarea
              value={editedMessage}
              onChange={(e) => setEditedMessage(e.target.value)}
              className="w-full h-48 p-3 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 resize-none"
            />
            <div className="flex gap-2 mt-2">
              <button onClick={() => setIsEditing(false)} className="px-3 py-1.5 bg-blue-600 text-white text-xs rounded-lg">
                Done
              </button>
              <button onClick={() => setIsEditing(false)} className="px-3 py-1.5 bg-gray-200 text-foreground text-xs rounded-lg">
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="whitespace-pre-wrap text-sm text-foreground leading-relaxed mt-2 max-h-64 overflow-y-auto">
            {editedMessage || emailData.message}
          </div>
        )}
      </div>

      <div className="flex gap-3">
        <button onClick={onSend} disabled={isEditing} className="flex-1 px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all font-medium flex items-center justify-center gap-2 disabled:opacity-50">
          <Send className="w-4 h-4" />
          Send Email
        </button>
        <button onClick={handleStartEdit} className="px-4 py-3 bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-all font-medium flex items-center justify-center gap-2">
          <Edit3 className="w-4 h-4" />
          Edit
        </button>
        <button onClick={onCancel} className="px-4 py-3 bg-muted text-foreground rounded-lg hover:bg-muted transition-all font-medium flex items-center justify-center gap-2">
          <X className="w-4 h-4" />
          Discard
        </button>
      </div>
    </div>
  );
};

// Email Sent Confirmation
const EmailSentConfirmation = ({ content }) => {
  const openGmailSent = () => window.open("https://mail.google.com/mail/u/0/#sent", "_blank");

  return (
    <div className="w-full">
      <div className="flex items-center gap-3 mb-4 p-4 bg-green-100 rounded-lg border border-green-200">
        <div className="w-12 h-12 bg-green-500 rounded-full flex items-center justify-center">
          <Check className="w-6 h-6 text-white" />
        </div>
        <div className="flex-1">
          <h4 className="font-semibold text-green-800">Email Sent Successfully</h4>
          <p className="text-sm text-green-600">Delivered via Gmail</p>
        </div>
      </div>
      <button onClick={openGmailSent} className="w-full px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-all font-medium flex items-center justify-center gap-2">
        <Mail className="w-4 h-4" />
        View in Gmail
        <ExternalLink className="w-3 h-3" />
      </button>
    </div>
  );
};


// Enhanced XAI Panel Component
const XAIPanel = ({ trace, isVisible, onClose }) => {
  const [activeTab, setActiveTab] = useState("overview");

  if (!isVisible) return null;

  const hasTrace = trace && trace.trace_id;
  const tabs = [
    { id: "overview", label: "Overview", icon: BarChart3 },
    { id: "reasoning", label: "Reasoning", icon: GitBranch },
    { id: "tools", label: "Tools", icon: Cpu },
  ];

  return (
    <div className="w-80 bg-card border-l border-border flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-border bg-gradient-to-r from-purple-50 to-blue-50">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-purple-600" />
            <span className="font-semibold text-purple-800">Explainable AI</span>
          </div>
          <button onClick={onClose} className="p-1 hover:bg-purple-100 rounded">
            <X className="w-4 h-4 text-purple-600" />
          </button>
        </div>
        {hasTrace && (
          <div className="grid grid-cols-3 gap-2 mt-3">
            <div className="bg-card rounded-lg p-2 text-center border">
              <div className="text-lg font-bold text-foreground">{trace.reasoning_chain?.length || 0}</div>
              <div className="text-xs text-muted-foreground">Steps</div>
            </div>
            <div className="bg-card rounded-lg p-2 text-center border">
              <div className="text-lg font-bold text-foreground">{trace.tool_decisions?.length || 0}</div>
              <div className="text-xs text-muted-foreground">Tools</div>
            </div>
            <div className="bg-card rounded-lg p-2 text-center border">
              <div className="text-lg font-bold text-foreground">{trace.duration_ms?.toFixed(0) || 0}ms</div>
              <div className="text-xs text-muted-foreground">Time</div>
            </div>
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-border">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-3 py-2.5 text-xs font-medium flex items-center justify-center gap-1.5 transition-colors ${
                activeTab === tab.id ? "text-blue-600 border-b-2 border-blue-600 bg-blue-50" : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {!hasTrace ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-4">
            <Brain className="w-12 h-12 text-purple-200 mb-4" />
            <h4 className="font-semibold text-foreground mb-2">No AI Trace Yet</h4>
            <p className="text-sm text-muted-foreground">Send a message to see AI reasoning</p>
          </div>
        ) : activeTab === "overview" ? (
          <div className="space-y-4">
            <div className="bg-gradient-to-br from-blue-50 to-purple-50 rounded-xl p-4 border border-blue-100">
              <div className="flex items-center gap-2 mb-3">
                <Target className="w-4 h-4 text-blue-600" />
                <span className="font-medium text-foreground text-sm">Detected Intent</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-blue-700 font-semibold capitalize">{trace.intent?.replace(/_/g, " ") || "Unknown"}</span>
                <ConfidenceBadge level={trace.confidence?.level || "medium"} score={trace.confidence?.score || 0} />
              </div>
            </div>

            {trace.entities && Object.keys(trace.entities).length > 0 && (
              <div className="bg-card rounded-xl p-4 border border-border">
                <div className="flex items-center gap-2 mb-3">
                  <Layers className="w-4 h-4 text-purple-600" />
                  <span className="font-medium text-foreground text-sm">Extracted Entities</span>
                </div>
                <div className="space-y-2">
                  {Object.entries(trace.entities).map(([key, value]) => (
                    <div key={key} className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground capitalize">{key.replace(/_/g, " ")}</span>
                      <span className="font-medium text-foreground bg-muted px-2 py-0.5 rounded">
                        {typeof value === "object" ? JSON.stringify(value) : value}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {trace.summary && (
              <div className="bg-amber-50 rounded-xl p-4 border border-amber-200">
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="w-4 h-4 text-amber-600" />
                  <span className="font-medium text-foreground text-sm">AI Explanation</span>
                </div>
                <p className="text-sm text-foreground leading-relaxed">{trace.summary}</p>
              </div>
            )}
          </div>
        ) : activeTab === "reasoning" ? (
          <div className="space-y-3">
            {trace.reasoning_chain?.length > 0 ? (
              trace.reasoning_chain.map((step, index) => (
                <div key={index} className="bg-card rounded-lg border p-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-foreground text-sm">{step.action}</span>
                    <ConfidenceBadge level={step.confidence > 0.85 ? "high" : step.confidence > 0.6 ? "medium" : "low"} score={step.confidence} />
                  </div>
                  <p className="text-xs text-muted-foreground">{step.reasoning}</p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No reasoning steps recorded</p>
              </div>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            {trace.tool_decisions?.length > 0 ? (
              trace.tool_decisions.map((decision, index) => (
                <div key={index} className="bg-card rounded-lg border p-3">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`w-2 h-2 rounded-full ${decision.selected ? "bg-green-500" : "bg-gray-300"}`} />
                      <span className="font-medium text-foreground text-sm">{decision.tool}</span>
                    </div>
                    <ConfidenceBadge level={decision.confidence > 0.85 ? "high" : "medium"} score={decision.confidence} />
                  </div>
                  <p className="text-xs text-muted-foreground">{decision.reasoning}</p>
                </div>
              ))
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                <Cpu className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p className="text-sm">No tools were used</p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};


// Main Dashboard Component
export default function DoctorDashboard() {
  const { user, token, logout } = useAuth();
  const [activeTab, setActiveTab] = useState("chat"); // "chat" or "documents"
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [serverStatus, setServerStatus] = useState("checking");
  const [showXAI, setShowXAI] = useState(false);
  const [currentXAITrace, setCurrentXAITrace] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showHistory] = useState(true);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    checkServerStatus();
    loadChatHistory();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Save session when messages change
  useEffect(() => {
    if (messages.length > 0 && currentSessionId) {
      saveCurrentSession();
    }
  }, [messages, currentSessionId]);

  const loadChatHistory = () => {
    try {
      const saved = localStorage.getItem("doctorChatHistory");
      if (saved) {
        const parsed = JSON.parse(saved);
        setChatHistory(parsed);
        if (parsed.length > 0 && !currentSessionId) {
          const mostRecent = parsed[0];
          setMessages(mostRecent.messages || []);
          setCurrentSessionId(mostRecent.id);
        }
      } else {
        startNewChat();
      }
    } catch (e) {
      startNewChat();
    }
  };

  const saveCurrentSession = useCallback(() => {
    if (messages.length === 0) return;
    const session = {
      id: currentSessionId || Date.now().toString(),
      timestamp: new Date().toISOString(),
      messages: messages,
      title: generateSessionTitle(messages),
      messageCount: messages.length,
    };

    setChatHistory((prev) => {
      const updated = [...prev];
      const existingIndex = updated.findIndex((s) => s.id === session.id);
      if (existingIndex >= 0) {
        updated[existingIndex] = session;
      } else {
        updated.unshift(session);
      }
      const trimmed = updated.slice(0, 50);
      localStorage.setItem("doctorChatHistory", JSON.stringify(trimmed));
      return trimmed;
    });
  }, [messages, currentSessionId]);

  const generateSessionTitle = (msgs) => {
    if (msgs.length === 0) return "New Conversation";
    const firstUserMsg = msgs.find((m) => m.role === "user");
    if (firstUserMsg) {
      const content = firstUserMsg.content;
      return content.length > 40 ? content.substring(0, 40) + "..." : content;
    }
    return "Conversation";
  };

  const loadSession = (session) => {
    setMessages(session.messages || []);
    setCurrentSessionId(session.id);
  };

  const startNewChat = () => {
    const newId = Date.now().toString();
    setMessages([]);
    setCurrentSessionId(newId);
  };

  const deleteSession = (sessionId, e) => {
    e.stopPropagation();
    setChatHistory((prev) => {
      const updated = prev.filter((s) => s.id !== sessionId);
      localStorage.setItem("doctorChatHistory", JSON.stringify(updated));
      return updated;
    });
    if (currentSessionId === sessionId) {
      startNewChat();
    }
  };

  const checkServerStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setServerStatus(data.assistant_ready ? "connected" : "error");
      } else {
        setServerStatus("error");
      }
    } catch {
      setServerStatus("disconnected");
    }
  };

  const detectMessageType = (text) => {
    return {
      isEmailPreview: text.includes("📧 **Email Preview") || text.includes("Email Preview - Awaiting"),
      isEmailSent: text.includes("Email successfully sent") || text.includes("✅ Email sent"),
      isScheduleRelated: text.includes("📅") || text.includes("Schedule") || text.includes("appointment"),
      isSuccess: text.includes("✅"),
      isError: text.includes("❌"),
    };
  };

  const sendMessage = async (customMessage = null) => {
    const messageToSend = customMessage || input.trim();
    if (!messageToSend || loading) return;

    setInput("");
    const userMessage = { role: "user", content: messageToSend, timestamp: new Date().toISOString() };
    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ message: messageToSend }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || "Failed to send message");
      }

      const data = await response.json();
      const messageType = detectMessageType(data.response);

      if (data.xai_trace) setCurrentXAITrace(data.xai_trace);

      const assistantMessage = {
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
        ...messageType,
        xaiTrace: data.xai_trace,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: `❌ Error: ${error.message}`, timestamp: new Date().toISOString(), isError: true }]);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    setMessages((prev) => [...prev, { role: "user", content: `📎 Uploading: ${file.name}`, timestamp: new Date().toISOString(), isUpload: true }]);

    try {
      const response = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      });

      if (!response.ok) throw new Error("Upload failed");

      const data = await response.json();
      setMessages((prev) => [...prev, { role: "assistant", content: data.response || `✅ Document "${file.name}" processed.`, timestamp: new Date().toISOString(), isSuccess: true }]);
    } catch (error) {
      setMessages((prev) => [...prev, { role: "assistant", content: `❌ Upload failed: ${error.message}`, timestamp: new Date().toISOString(), isError: true }]);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const openGoogleCalendar = () => window.open("https://calendar.google.com/calendar/u/0/r", "_blank");

  const formatTime = (timestamp) => (timestamp ? new Date(timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "");

  const formatDate = (timestamp) => {
    if (!timestamp) return "";
    const date = new Date(timestamp);
    const today = new Date();
    if (date.toDateString() === today.toDateString()) return "Today";
    return date.toLocaleDateString([], { month: "short", day: "numeric" });
  };


  const renderMessage = (msg, index) => {
    const isUser = msg.role === "user";

    return (
      <div key={index} className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""} mb-4`}>
        <div className={`flex-shrink-0 w-9 h-9 rounded-full flex items-center justify-center ${isUser ? "bg-primary" : "bg-gradient-to-br from-teal-500 to-blue-600"}`}>
          {isUser ? <Stethoscope className="w-4 h-4 text-white" /> : <Bot className="w-4 h-4 text-white" />}
        </div>

        <div className={`flex-1 max-w-[80%] ${isUser ? "text-right" : ""}`}>
          <div
            className={`inline-block rounded-2xl px-4 py-3 ${
              isUser
                ? "bg-primary text-white rounded-tr-sm"
                : msg.isEmailPreview
                ? "bg-amber-50 border-2 border-amber-300 text-foreground rounded-tl-sm"
                : msg.isError
                ? "bg-red-50 border border-red-200 text-foreground rounded-tl-sm"
                : msg.isSuccess
                ? "bg-green-50 border border-green-200 text-foreground rounded-tl-sm"
                : "bg-card border border-border text-foreground rounded-tl-sm shadow-sm"
            }`}
          >
            {msg.isEmailPreview ? (
              <EmailPreviewCard content={msg.content} onSend={() => sendMessage("send")} onCancel={() => sendMessage("cancel")} />
            ) : msg.isEmailSent ? (
              <EmailSentConfirmation content={msg.content} />
            ) : (
              <div className="whitespace-pre-wrap text-sm leading-relaxed">{msg.content}</div>
            )}

            {!isUser && msg.isScheduleRelated && (
              <div className="mt-3 pt-3 border-t border-border">
                <button onClick={openGoogleCalendar} className="flex items-center gap-2 text-sm text-primary hover:text-primary/80 font-medium">
                  <Calendar className="w-4 h-4" />
                  Open Google Calendar
                  <ExternalLink className="w-3 h-3" />
                </button>
              </div>
            )}

            {!isUser && msg.xaiTrace && (
              <div className="mt-2 pt-2 border-t border-border">
                <button
                  onClick={() => {
                    setCurrentXAITrace(msg.xaiTrace);
                    setShowXAI(true);
                  }}
                  className="flex items-center gap-1.5 text-xs text-purple-600 hover:text-purple-700 font-medium"
                >
                  <Brain className="w-3 h-3" />
                  View AI reasoning
                </button>
              </div>
            )}
          </div>
          <div className={`text-xs text-muted-foreground mt-1 ${isUser ? "text-right" : ""}`}>{formatTime(msg.timestamp)}</div>
        </div>
      </div>
    );
  };

  const quickActions = [
    { label: "Today's Schedule", query: "What's my schedule for today?", icon: Calendar },
    { label: "This Week", query: "Am I free this week?", icon: Clock },
    { label: "Add Appointment", query: "Add an appointment", icon: Plus },
  ];

  return (
    <div className="flex h-screen bg-muted">
      {/* Mobile Overlay */}
      {mobileMenuOpen && <div className="lg:hidden fixed inset-0 bg-black/50 z-40" onClick={() => setMobileMenuOpen(false)} />}

      {/* Chat History Sidebar - hidden on mobile by default */}
      <aside className={`fixed lg:static left-0 top-0 h-screen w-64 bg-card border-r flex flex-col z-50 transition-transform duration-300 ${mobileMenuOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"}`}>
        <div className="flex items-center justify-between gap-3 p-4 border-b">
          <div className="flex items-center gap-3">
            <img src="/logo.png" alt="Logo" className="w-10 h-10 object-contain dark:brightness-0 dark:invert" />
            <div className="flex flex-col">
              <span className="text-sm font-semibold">SanteConnect</span>
              <span className="text-xs text-muted-foreground">Doctor Portal</span>
            </div>
          </div>
          <button onClick={() => setMobileMenuOpen(false)} className="lg:hidden p-1 hover:bg-muted rounded">
            <X size={20} />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="p-3 border-b space-y-2">
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab("chat")}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === "chat" ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-muted"
              }`}
            >
              <Bot size={16} />
              Assistant
            </button>
            <button
              onClick={() => setActiveTab("documents")}
              className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-all ${
                activeTab === "documents" ? "bg-primary text-white" : "bg-muted text-muted-foreground hover:bg-muted"
              }`}
            >
              <FileText size={16} />
              Documents
            </button>
          </div>
          {activeTab === "chat" && (
            <Button onClick={startNewChat} className="w-full btn-glow">
              <Plus size={18} className="mr-2" />
              New Chat
            </Button>
          )}
        </div>

        {/* Chat History List */}
        <div className="flex-1 overflow-y-auto p-2">
          <p className="text-xs text-muted-foreground px-2 mb-2 flex items-center gap-1">
            <History size={12} />
            Recent Conversations
          </p>
          {chatHistory.length === 0 ? (
            <div className="text-center py-8 px-4">
              <History className="w-8 h-8 mx-auto text-gray-200 mb-2" />
              <p className="text-xs text-muted-foreground">No conversations yet</p>
            </div>
          ) : (
            chatHistory.map((session) => (
              <div
                key={session.id}
                onClick={() => loadSession(session)}
                className={`group mb-2 p-3 rounded-lg cursor-pointer transition-all ${currentSessionId === session.id ? "bg-blue-50 border-2 border-blue-200" : "bg-muted hover:bg-muted border-2 border-transparent"}`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-medium text-foreground truncate">{session.title}</div>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">{formatDate(session.timestamp)}</span>
                      <span className="text-xs text-gray-300">•</span>
                      <span className="text-xs text-muted-foreground">{session.messageCount || 0} msgs</span>
                    </div>
                  </div>
                  <button onClick={(e) => deleteSession(session.id, e)} className="opacity-0 group-hover:opacity-100 p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-50 rounded transition-all">
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        <div className="p-4 border-t">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 min-w-0">
              <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-white text-sm font-medium">{user?.name?.charAt(0).toUpperCase() || "D"}</div>
              <div className="text-sm min-w-0">
                <div className="font-medium truncate">{user?.name}</div>
                <div className="text-muted-foreground text-xs truncate">{user?.specialization || "Doctor"}</div>
              </div>
            </div>
            <Button variant="ghost" size="icon" onClick={logout} title="Logout">
              <LogOut size={18} className="text-muted-foreground" />
            </Button>
          </div>
        </div>
      </aside>


      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile Header with Logo and Menu Button */}
        <div className="lg:hidden bg-card border-b px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 hover:bg-muted rounded-lg"
            >
              <Menu size={22} />
            </button>
            <img src="/logo.png" alt="SanteConnect" className="w-8 h-8 object-contain dark:brightness-0 dark:invert" />
            <div className="flex flex-col">
              <span className="font-bold text-sm">SanteConnect</span>
              <span className="text-xs text-muted-foreground">Doctor Portal</span>
            </div>
          </div>
          <ThemeToggle />
        </div>
        
        {/* Header - Desktop only */}
        <header className="bg-card border-b px-4 sm:px-6 py-4 hidden lg:block">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-semibold flex items-center gap-2 text-foreground">
                {activeTab === "chat" ? (
                  <>
                    <Bot className="w-5 h-5 text-primary" />
                    AI Medical Assistant
                  </>
                ) : (
                  <>
                    <FileText className="w-5 h-5 text-purple-600" />
                    Document Analysis
                  </>
                )}
              </h1>
              <p className="text-xs text-muted-foreground">
                {activeTab === "chat" ? "Powered by Groq • Google Calendar Connected" : "OCR + AI Risk Assessment"}
              </p>
            </div>

            <div className="flex items-center gap-3">
              <ThemeToggle />
              {activeTab === "chat" && (
                <>
                  <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium ${serverStatus === "connected" ? "bg-green-500/10 text-green-600 dark:text-green-400" : serverStatus === "checking" ? "bg-muted text-muted-foreground" : "bg-red-500/10 text-red-600 dark:text-red-400"}`}>
                    <div className={`w-2 h-2 rounded-full ${serverStatus === "connected" ? "bg-green-500 animate-pulse" : serverStatus === "checking" ? "bg-muted-foreground" : "bg-red-500"}`} />
                    {serverStatus === "connected" ? "Online" : serverStatus === "checking" ? "Connecting..." : "Offline"}
                  </div>

                  <button onClick={openGoogleCalendar} className="p-2 hover:bg-muted rounded-lg transition-colors" title="Open Google Calendar">
                    <Calendar className="w-5 h-5 text-muted-foreground" />
                  </button>

                  <button onClick={checkServerStatus} className="p-2 hover:bg-muted rounded-lg transition-colors" title="Refresh">
                    <RefreshCw className="w-5 h-5 text-muted-foreground" />
                  </button>

                  <button onClick={() => setShowXAI(!showXAI)} className={`p-2 rounded-lg transition-colors flex items-center gap-1.5 ${showXAI ? "bg-purple-500/10 text-purple-600 dark:text-purple-400" : "hover:bg-muted text-muted-foreground"}`} title="Toggle XAI Panel">
                    <Brain className="w-5 h-5" />
                  </button>
                </>
              )}
            </div>
          </div>
        </header>

        {/* Document Analysis Tab */}
        {activeTab === "documents" && <DocumentAnalysis />}

        {/* Chat Area - Only show when chat tab is active */}
        {activeTab === "chat" && (
        <div className="flex-1 flex overflow-hidden">
          <div className="flex-1 flex flex-col min-w-0">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 sm:px-6 py-4">
              {messages.length === 0 ? (
                <div className="h-full flex flex-col items-center justify-center text-center">
                  <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-teal-500 rounded-2xl flex items-center justify-center mb-6 shadow-lg">
                    <Stethoscope className="w-10 h-10 text-white" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-2">Welcome, Dr. {user?.name?.split(" ")[0] || "Doctor"}</h3>
                  <p className="text-muted-foreground mb-8 max-w-md">I'm your AI assistant. I can help you manage appointments, process documents, and communicate with patients.</p>

                  <div className="flex flex-wrap gap-3 justify-center">
                    {quickActions.map((action, i) => {
                      const Icon = action.icon;
                      return (
                        <button key={i} onClick={() => setInput(action.query)} className="flex items-center gap-2 px-4 py-2.5 bg-card border border-border rounded-lg hover:border-primary/30 hover:bg-primary/5 transition-all text-sm text-foreground">
                          <Icon className="w-4 h-4 text-primary" />
                          {action.label}
                        </button>
                      );
                    })}
                  </div>
                </div>
              ) : (
                <>
                  {messages.map(renderMessage)}
                  {loading && (
                    <div className="flex gap-3 mb-4">
                      <div className="w-9 h-9 rounded-full bg-gradient-to-br from-teal-500 to-blue-600 flex items-center justify-center">
                        <Bot className="w-4 h-4 text-white" />
                      </div>
                      <div className="bg-card border border-border rounded-2xl rounded-tl-sm px-4 py-3 shadow-sm">
                        <div className="flex items-center gap-2 text-muted-foreground">
                          <Loader className="w-4 h-4 animate-spin" />
                          <span className="text-sm">Thinking...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} />
                </>
              )}
            </div>

            {/* Input Area */}
            <div className="bg-card border-t p-4">
              {messages.length > 0 && (
                <div className="flex gap-2 mb-3 overflow-x-auto pb-2">
                  {quickActions.map((action, i) => {
                    const Icon = action.icon;
                    return (
                      <button key={i} onClick={() => setInput(action.query)} className="flex-shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-muted border border-border rounded-full hover:border-primary/30 hover:bg-primary/5 transition-all text-xs text-muted-foreground">
                        <Icon className="w-3 h-3 text-primary" />
                        {action.label}
                      </button>
                    );
                  })}
                </div>
              )}

              <div className="flex gap-3">
                <input type="file" ref={fileInputRef} onChange={handleFileUpload} className="hidden" accept=".pdf,.jpg,.jpeg,.png,.txt,.doc,.docx" />

                <button onClick={() => fileInputRef.current?.click()} disabled={uploading} className="p-3 bg-muted hover:bg-muted rounded-xl transition-colors disabled:opacity-50" title="Upload document">
                  {uploading ? <Loader className="w-5 h-5 animate-spin text-muted-foreground" /> : <Upload className="w-5 h-5 text-muted-foreground" />}
                </button>

                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={(e) => e.key === "Enter" && !e.shiftKey && sendMessage()}
                  placeholder="Ask about schedules, appointments, or upload documents..."
                  className="flex-1 px-4 py-3 bg-muted border border-border rounded-xl focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all"
                  disabled={loading}
                />

                <button onClick={() => sendMessage()} disabled={loading || !input.trim()} className="px-5 py-3 bg-primary text-white rounded-xl hover:bg-primary/90 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-sm">
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* XAI Panel */}
          <XAIPanel trace={currentXAITrace} isVisible={showXAI} onClose={() => setShowXAI(false)} />
        </div>
        )}
      </div>
    </div>
  );
}
