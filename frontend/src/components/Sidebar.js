import { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { Plus, MessageSquare, Trash2, LogOut, Image, Search, Menu, X, FileText, Stethoscope, Bot } from 'lucide-react';
import { Button } from './ui/button';

export default function Sidebar({ activeTab, onTabChange, currentConversation, onSelectConversation, refreshTrigger }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, token, logout } = useAuth();

  useEffect(() => {
    if (token) fetchConversations();
  }, [token, refreshTrigger]);

  const fetchConversations = async () => {
    try {
      const res = await fetch('http://localhost:8000/conversations', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (e) { console.error('Error:', e); }
    finally { setLoading(false); }
  };

  const handleDelete = async (e, id) => {
    e.stopPropagation();
    if (!window.confirm('Delete this conversation?')) return;
    try {
      const res = await fetch(`http://localhost:8000/conversations/${id}`, {
        method: 'DELETE', headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        setConversations(c => c.filter(x => x.id !== id));
        if (currentConversation?.id === id) onSelectConversation(null);
      }
    } catch (e) { console.error(e); }
  };

  const handleNavClick = (tab) => {
    onTabChange(tab);
    setMobileOpen(false);
  };

  const handleConvClick = (conv) => {
    onSelectConversation(conv);
    onTabChange('chat');
    setMobileOpen(false);
  };

  const navItems = [
    { id: 'chat', icon: Bot, label: 'AI Assistant', color: 'text-blue-600' },
    { id: 'medibot', icon: Stethoscope, label: 'Dr. MediBot', color: 'text-emerald-600' },
    { id: 'scan-prescription', icon: FileText, label: 'Scan Prescription', color: 'text-indigo-600' },
    { id: 'identify', icon: Image, label: 'Identify Medication', color: 'text-violet-600' },
    { id: 'search', icon: Search, label: 'Search Database', color: 'text-teal-600' }
  ];

  const sidebarContent = (
    <>
      {/* Header */}
      <div className="flex items-center justify-between gap-3 p-4 border-b bg-muted/30">
        <div className="flex items-center gap-3">
          <img 
            src="/logo.png" 
            alt="SanteConnect Logo" 
            className="w-10 h-10 object-contain dark:brightness-0 dark:invert"
          />
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-bold">SanteConnect</span>
            <span className="text-xs text-muted-foreground">Medical AI Platform</span>
          </div>
        </div>
        <button onClick={() => setMobileOpen(false)} className="lg:hidden p-1.5 hover:bg-muted rounded-lg">
          <X size={20} />
        </button>
      </div>

      {/* New Chat Button */}
      <div className="p-3">
        <Button 
          onClick={() => { onSelectConversation(null); onTabChange('chat'); setMobileOpen(false); }} 
          className="w-full btn-glow"
        >
          <Plus size={18} className="mr-2" />
          New Chat
        </Button>
      </div>

      {/* Navigation */}
      <div className="px-3 pb-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2 mb-2">Features</p>
        <div className="space-y-1">
          {navItems.map(({ id, icon: Icon, label, color }) => (
            <button
              key={id}
              onClick={() => handleNavClick(id)}
              className={`w-full flex items-center gap-3 text-sm p-2.5 rounded-lg transition-all ${
                activeTab === id 
                  ? 'bg-primary text-primary-foreground shadow-sm' 
                  : 'hover:bg-muted text-muted-foreground hover:text-foreground'
              }`}
            >
              <Icon size={18} className={activeTab === id ? '' : color} />
              <span className="font-medium">{label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Divider */}
      <div className="border-t mx-3" />

      {/* Recent Chats */}
      <div className="flex-1 overflow-y-auto p-3">
        <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wider px-2 mb-2">Recent Chats</p>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
          </div>
        ) : conversations.length === 0 ? (
          <div className="text-center py-8 px-4">
            <MessageSquare className="w-8 h-8 mx-auto text-muted-foreground/30 mb-2" />
            <p className="text-sm text-muted-foreground">No conversations yet</p>
            <p className="text-xs text-muted-foreground/70 mt-1">Start a new chat above</p>
          </div>
        ) : (
          <div className="space-y-1">
            {conversations.map(conv => (
              <div
                key={conv.id}
                onClick={() => handleConvClick(conv)}
                className={`group flex items-center gap-2 p-2.5 rounded-lg cursor-pointer transition-all ${
                  currentConversation?.id === conv.id 
                    ? 'bg-primary/10 border border-primary/20' 
                    : 'hover:bg-muted'
                }`}
              >
                <MessageSquare size={16} className={`flex-shrink-0 ${
                  currentConversation?.id === conv.id ? 'text-primary' : 'text-muted-foreground'
                }`} />
                <span className={`flex-1 truncate text-sm ${
                  currentConversation?.id === conv.id ? 'text-primary font-medium' : ''
                }`}>
                  {conv.title || 'New conversation'}
                </span>
                <button 
                  onClick={e => handleDelete(e, conv.id)} 
                  className="opacity-0 group-hover:opacity-100 p-1 hover:bg-destructive/10 rounded transition-all"
                >
                  <Trash2 size={14} className="text-muted-foreground hover:text-destructive" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* User Section */}
      <div className="p-4 border-t bg-muted/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="w-9 h-9 bg-gradient-to-br from-primary to-blue-600 rounded-full flex items-center justify-center text-primary-foreground text-sm font-semibold flex-shrink-0 shadow-sm">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="text-sm min-w-0">
              <div className="font-medium truncate">{user?.name}</div>
              <div className="text-muted-foreground text-xs truncate">{user?.email}</div>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Logout" className="flex-shrink-0 hover:bg-destructive/10 hover:text-destructive">
            <LogOut size={18} />
          </Button>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile overlay */}
      {mobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar - hidden on mobile by default */}
      <aside className={`
        fixed left-0 top-0 h-screen w-64 bg-card border-r flex flex-col z-50
        transition-transform duration-300 ease-out
        lg:translate-x-0
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {sidebarContent}
      </aside>

      {/* Export mobile toggle function via window for external access */}
      {typeof window !== 'undefined' && (window.openMobileSidebar = () => setMobileOpen(true))}
    </>
  );
}
