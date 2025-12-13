import { useState, useEffect } from 'react';
import { useAuth } from './AuthContext';
import { Plus, MessageSquare, Trash2, LogOut, Image, Search, Menu, X } from 'lucide-react';
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
    if (!window.confirm('Delete?')) return;
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
    onTabChange('chat'); // Switch to chat tab when selecting a conversation
    setMobileOpen(false);
  };

  const sidebarContent = (
    <>
      <div className="flex items-center justify-between gap-3 p-4 border-b">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-primary rounded-lg flex items-center justify-center text-primary-foreground">
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
            </svg>
          </div>
          <div className="flex flex-col min-w-0">
            <span className="text-sm font-semibold">SanteConnect</span>
            <span className="text-xs text-muted-foreground">Medical AI</span>
          </div>
        </div>
        <button onClick={() => setMobileOpen(false)} className="lg:hidden p-1 hover:bg-muted rounded">
          <X size={20} />
        </button>
      </div>

      <div className="p-3 border-b">
        <Button onClick={() => { onSelectConversation(null); onTabChange('chat'); setMobileOpen(false); }} className="w-full btn-glow">
          <Plus size={18} className="mr-2" />New Chat
        </Button>
      </div>

      <div className="p-2 border-b">
        <p className="text-xs text-muted-foreground px-2 mb-2">Navigation</p>
        {[
          { id: 'chat', icon: MessageSquare, label: 'AI Assistant' },
          { id: 'identify', icon: Image, label: 'Identify Medication' },
          { id: 'search', icon: Search, label: 'Search Database' }
        ].map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            onClick={() => handleNavClick(id)}
            className={`w-full flex items-center text-sm p-2 rounded-md transition-colors ${
              activeTab === id ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'
            }`}
          >
            <Icon size={16} className="mr-2" />{label}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-2">
        <p className="text-xs text-muted-foreground px-2 mb-2">Recent Chats</p>
        {loading ? (
          <p className="text-center text-muted-foreground py-4 text-sm">Loading...</p>
        ) : conversations.length === 0 ? (
          <p className="text-center text-muted-foreground py-4 text-sm">No conversations yet</p>
        ) : conversations.map(conv => (
          <div
            key={conv.id}
            onClick={() => handleConvClick(conv)}
            className={`group flex items-center gap-2 p-3 rounded-lg cursor-pointer mb-1 ${
              currentConversation?.id === conv.id ? 'bg-primary/10 text-primary' : 'hover:bg-muted'
            }`}
          >
            <MessageSquare size={16} className="text-muted-foreground flex-shrink-0" />
            <span className="flex-1 truncate text-sm">{conv.title || 'New conversation'}</span>
            <button onClick={e => handleDelete(e, conv.id)} className="opacity-0 group-hover:opacity-100 p-1">
              <Trash2 size={14} className="text-muted-foreground hover:text-destructive" />
            </button>
          </div>
        ))}
      </div>

      <div className="p-4 border-t">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 min-w-0">
            <div className="w-8 h-8 bg-primary rounded-full flex items-center justify-center text-primary-foreground text-sm font-medium flex-shrink-0">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </div>
            <div className="text-sm min-w-0">
              <div className="font-medium truncate">{user?.name}</div>
              <div className="text-muted-foreground text-xs truncate">{user?.email}</div>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={logout} title="Logout" className="flex-shrink-0">
            <LogOut size={18} className="text-muted-foreground" />
          </Button>
        </div>
      </div>
    </>
  );

  return (
    <>
      {/* Mobile menu button */}
      <button
        onClick={() => setMobileOpen(true)}
        className="lg:hidden fixed top-4 left-4 z-50 p-2 bg-card border rounded-lg shadow-md"
      >
        <Menu size={24} />
      </button>

      {/* Mobile overlay */}
      {mobileOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setMobileOpen(false)}
        />
      )}

      {/* Sidebar - desktop always visible, mobile slide-in */}
      <aside className={`
        fixed left-0 top-0 h-screen w-64 bg-card border-r flex flex-col z-50
        transition-transform duration-300
        lg:translate-x-0
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        {sidebarContent}
      </aside>
    </>
  );
}
