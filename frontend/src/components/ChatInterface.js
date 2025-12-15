import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles } from 'lucide-react';
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

    let convId = currentConvId;
    if (!convId) {
      convId = await createConversation(userMessage);
    }

    try {
      const fastRes = await fetch(`http://localhost:8000/fast/${encodeURIComponent(userMessage)}`);
      const fastData = await fastRes.json();
      
      if (fastData.success && fastData.method?.includes('fast_path')) {
        const agentMsg = {
          type: 'agent',
          content: fastData.answer || 'Sorry, I couldn\'t process your request.',
          confidence: fastData.confidence,
        };
        setMessages(prev => [...prev, agentMsg]);
        
        if (convId) {
          saveMessages(convId, userMessage, agentMsg.content);
        }
        return;
      }

      const res = await fetch(`http://localhost:8000/agent/query?query=${encodeURIComponent(userMessage)}`);
      const data = await res.json();
      
      const agentMsg = {
        type: 'agent',
        content: data.answer || 'Sorry, I couldn\'t process your request.',
        confidence: data.confidence,
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
      await fetch(`http://localhost:8000/conversations/${convId}/messages`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ role: 'user', content: userMsg })
      });
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

  const quickQuestions = [
    "What is Paracetamol used for?",
    "Is Ibuprofen safe during pregnancy?",
    "What are common side effects of Aspirin?"
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-10rem)] sm:h-[calc(100vh-12rem)] bg-background rounded-xl border overflow-hidden">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 1 && messages[0].type === 'agent' && (
          <div className="p-6 text-center">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg">
              <Bot className="w-8 h-8 text-white" />
            </div>
            <h3 className="text-lg font-semibold mb-2">Medication Assistant</h3>
            <p className="text-muted-foreground text-sm mb-6 max-w-md mx-auto">
              Ask me anything about medications, drug interactions, side effects, or safety information.
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {quickQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => setInput(q)}
                  className="px-3 py-2 bg-muted hover:bg-primary/10 hover:text-primary rounded-lg text-sm transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div 
            key={index} 
            className={`py-4 px-4 sm:px-6 ${message.type === 'user' ? 'bg-muted/30' : 'bg-background'}`}
          >
            <div className="max-w-3xl mx-auto">
              <div className="flex gap-3 items-start">
                {/* Avatar */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                  message.type === 'agent' 
                    ? 'bg-gradient-to-br from-blue-500 to-indigo-600' 
                    : 'bg-gray-600'
                }`}>
                  {message.type === 'agent' ? (
                    <Bot className="w-4 h-4 text-white" />
                  ) : (
                    <User className="w-4 h-4 text-white" />
                  )}
                </div>
                
                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-medium">
                      {message.type === 'agent' ? 'Assistant' : 'You'}
                    </span>
                    {message.confidence && (
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Sparkles className="w-3 h-3" />
                        {message.confidence}
                      </span>
                    )}
                  </div>
                  <div 
                    className="prose prose-sm max-w-none text-muted-foreground leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} 
                  />
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Typing Indicator */}
        {isTyping && (
          <div className="py-4 px-4 sm:px-6 bg-background">
            <div className="max-w-3xl mx-auto flex gap-3">
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center">
                <Bot className="w-4 h-4 text-white" />
              </div>
              <div className="flex items-center gap-1.5 py-2">
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{animationDelay:'150ms'}} />
                <div className="w-2 h-2 rounded-full bg-blue-500 animate-bounce" style={{animationDelay:'300ms'}} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="border-t bg-background p-4">
        <div className="max-w-3xl mx-auto flex gap-2">
          <textarea
            className="flex-1 min-h-[44px] max-h-[150px] px-4 py-3 text-sm rounded-xl border border-input bg-muted/30 resize-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:border-transparent transition-all"
            placeholder="Ask about medications..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            rows={1}
            disabled={loading}
          />
          <Button 
            onClick={sendMessage} 
            disabled={!input.trim() || loading} 
            size="icon" 
            className="h-11 w-11 rounded-xl btn-glow flex-shrink-0"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ChatInterface;
