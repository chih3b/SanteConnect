import React, { useState, useRef, useEffect } from 'react';
import { Send } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from './AuthContext';

const ChatInterface = ({ conversation, onConversationCreated }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [currentConvId, setCurrentConvId] = useState(null);
  const messagesEndRef = useRef(null);
  const { token } = useAuth();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (conversation?.id) {
      setCurrentConvId(conversation.id);
      loadConversationMessages();
    } else {
      setCurrentConvId(null);
      setMessages([{
        type: 'agent',
        content: 'Hello! I\'m your medication assistant. Ask me about medications, interactions, side effects, or pregnancy safety.'
      }]);
    }
  }, [conversation?.id]);

  const loadConversationMessages = async () => {
    try {
      const res = await fetch(`http://localhost:8000/conversations/${conversation.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        const formatted = data.messages.map(msg => ({
          type: msg.role === 'user' ? 'user' : 'agent',
          content: msg.content,
          ...(msg.metadata || {})
        }));
        setMessages(formatted.length > 0 ? formatted : [{
          type: 'agent', content: 'Hello! How can I help you today?'
        }]);
      }
    } catch (e) { console.error('Error loading messages:', e); }
  };

  const createConversation = async (firstMessage) => {
    try {
      const res = await fetch('http://localhost:8000/conversations', {
        method: 'POST',
        headers: { 
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: firstMessage.substring(0, 50) })
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentConvId(data.id);
        if (onConversationCreated) onConversationCreated(data);
        return data.id;
      }
    } catch (e) { console.error('Error creating conversation:', e); }
    return null;
  };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput('');
    setMessages(prev => [...prev, { type: 'user', content: userMessage }]);
    setLoading(true);
    setIsTyping(true);

    // Create conversation if needed
    let convId = currentConvId;
    if (!convId) {
      convId = await createConversation(userMessage);
    }

    try {
      // Try fast path first
      const fastRes = await fetch(`http://localhost:8000/fast/${encodeURIComponent(userMessage)}`);
      const fastData = await fastRes.json();
      
      if (fastData.success && fastData.method?.includes('fast_path')) {
        const toolNames = fastData.tool_calls?.map(tc => tc.tool) || [];
        const localTools = ['get_drug_details', 'search_medication', 'check_pregnancy_safety'];
        const hasLocal = toolNames.some(t => localTools.some(lt => t.includes(lt)));
        
        const agentMsg = {
          type: 'agent',
          content: fastData.answer || 'Sorry, I couldn\'t process your request.',
          confidence: fastData.confidence,
          tools_used: toolNames,
          method: '⚡ Fast Path',
          data_sources: { local: hasLocal, mcp: false }
        };
        setMessages(prev => [...prev, agentMsg]);
        
        // Save to conversation if we have one
        if (convId) {
          saveMessages(convId, userMessage, agentMsg.content);
        }
        return;
      }

      // Fall back to full agent
      const res = await fetch(`http://localhost:8000/agent/query?query=${encodeURIComponent(userMessage)}`);
      const data = await res.json();
      
      const toolNames = data.tool_calls?.map(tc => tc.tool) || [];
      const localTools = ['get_drug_details', 'search_medication', 'check_pregnancy_safety'];
      const mcpTools = ['check_fda_drug_info', 'search_medical_literature', 'check_drug_recalls'];
      const webTools = ['search_web_drug_info'];
      
      const agentMsg = {
        type: 'agent',
        content: data.answer || 'Sorry, I couldn\'t process your request.',
        confidence: data.confidence,
        tools_used: toolNames,
        method: '🤖 AI Agent',
        data_sources: {
          local: toolNames.some(t => localTools.some(lt => t.includes(lt))),
          mcp: toolNames.some(t => mcpTools.some(mt => t.includes(mt))),
          web: toolNames.some(t => webTools.some(wt => t.includes(wt)))
        }
      };
      setMessages(prev => [...prev, agentMsg]);
      
      if (convId) {
        saveMessages(convId, userMessage, agentMsg.content);
      }
    } catch (error) {
      setMessages(prev => [...prev, {
        type: 'agent',
        content: 'Sorry, I\'m having trouble connecting to the server.'
      }]);
    } finally {
      setLoading(false);
      setIsTyping(false);
    }
  };

  const saveMessages = async (convId, userMsg, agentMsg) => {
    try {
      // Save user message
      await fetch(`http://localhost:8000/conversations/${convId}/messages`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'user', content: userMsg })
      });
      // Save agent message
      await fetch(`http://localhost:8000/conversations/${convId}/messages`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'assistant', content: agentMsg })
      });
    } catch (e) { console.error('Error saving messages:', e); }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const formatMessage = (content) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>')
      .replace(/• /g, '• ');
  };

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] sm:h-[calc(100vh-12rem)] bg-background">
      <div className="flex-1 overflow-y-auto">
        {messages.map((message, index) => (
          <div key={index} className={`border-b py-4 sm:py-6 ${message.type === 'user' ? 'bg-muted/30' : 'bg-background'}`}>
            <div className="max-w-3xl mx-auto px-3 sm:px-4">
              <div className="flex gap-2 sm:gap-3 items-start">
                {message.type === 'agent' && (
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-blue-600 flex items-center justify-center shadow-md flex-shrink-0 mt-1">
                    <div className="w-2 h-2 rounded-full bg-white"></div>
                  </div>
                )}
                {message.type === 'user' && (
                  <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-gray-600 flex items-center justify-center shadow-md flex-shrink-0 mt-1">
                    <svg className="w-4 h-4 sm:w-5 sm:h-5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>
                    </svg>
                  </div>
                )}
                <div className="flex-1 min-w-0">
                  <div className="prose prose-sm max-w-none text-sm sm:text-base" style={{ lineHeight: message.type === 'agent' ? '1.7' : '1.5' }}
                    dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} />
                </div>
              </div>
              {message.confidence && (
                <div className="text-[10px] sm:text-xs text-muted-foreground mt-2 sm:mt-3 flex items-center gap-1 sm:gap-2 flex-wrap ml-9 sm:ml-11">
                  {message.method && <span className="font-medium">{message.method}</span>}
                  {message.method && <span className="hidden sm:inline">•</span>}
                  <span className="hidden sm:inline">Confidence: {message.confidence}</span>
                  {message.data_sources?.local && <span className="text-blue-600">🗄️</span>}
                  {message.data_sources?.mcp && <span className="text-green-600">🌐</span>}
                  {message.data_sources?.web && <span className="text-purple-600">🔍</span>}
                </div>
              )}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="border-b py-4 sm:py-6 bg-background">
            <div className="max-w-3xl mx-auto px-3 sm:px-4 flex gap-2 sm:gap-3">
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-full bg-blue-600 flex items-center justify-center shadow-md">
                <div className="w-2 h-2 rounded-full bg-white animate-pulse"></div>
              </div>
              <div className="flex items-center gap-1 mt-2">
                <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce"></div>
                <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" style={{animationDelay:'150ms'}}></div>
                <div className="w-2 h-2 rounded-full bg-blue-600 animate-bounce" style={{animationDelay:'300ms'}}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t bg-background p-3 sm:p-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <textarea
            className="flex-1 min-h-[40px] sm:min-h-[44px] max-h-[150px] sm:max-h-[200px] px-3 py-2 text-sm rounded-md border border-input bg-background resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder="Ask about medications..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            rows={1}
            disabled={loading}
          />
          <Button onClick={sendMessage} disabled={!input.trim() || loading} size="icon" className="h-10 w-10 sm:h-11 sm:w-11 btn-glow flex-shrink-0">
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
