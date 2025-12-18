import { useState, useRef, useEffect } from 'react';
import { Send, Bot, User, Sparkles, ChevronDown, ChevronUp, Brain, Zap, Stethoscope, Pill, Shield, Search } from 'lucide-react';
import { Button } from './ui/button';
import { useAuth } from './AuthContext';

// XAI Explainability Component
const XAISection = ({ xai }) => {
  const [expanded, setExpanded] = useState(false);
  
  if (!xai || !xai.reasoning_steps) return null;
  
  const confidenceColor = xai.confidence_level === 'high' ? 'text-green-600 bg-green-100' 
    : xai.confidence_level === 'medium' ? 'text-yellow-600 bg-yellow-100' 
    : 'text-red-600 bg-red-100';
  
  return (
    <div className="mt-3 p-3 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-100">
      <button 
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-xs text-purple-700 hover:text-purple-900 transition-colors w-full"
      >
        <Brain className="w-4 h-4" />
        <span className="font-medium">🧠 Why this answer?</span>
        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${confidenceColor}`}>
          {Math.round((xai.final_confidence || 0) * 100)}% confident
        </span>
        <span className="ml-auto flex items-center gap-1 text-purple-500">
          {expanded ? 'Hide' : 'Show'} details
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </span>
      </button>
      
      {/* Always show summary preview */}
      {!expanded && xai.summary && (
        <div className="mt-2 text-xs text-purple-600 pl-6">
          {xai.summary}
        </div>
      )}
      
      {expanded && (
        <div className="mt-3 space-y-3 text-xs animate-in fade-in slide-in-from-top-2">
          {/* Summary */}
          {xai.summary && (
            <div className="p-2 bg-blue-50 rounded-lg text-blue-800">
              <span className="font-medium">Summary:</span> {xai.summary}
            </div>
          )}
          
          {/* Reasoning Steps */}
          <div className="space-y-2">
            <span className="font-medium text-muted-foreground">Reasoning Chain:</span>
            {xai.reasoning_steps?.map((step, i) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-muted/50 rounded-lg">
                <span className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold flex-shrink-0">
                  {step.step}
                </span>
                <div className="flex-1">
                  <div className="font-medium text-foreground">{step.action}</div>
                  <div className="text-muted-foreground">{step.reasoning}</div>
                </div>
                <span className={`px-1.5 py-0.5 rounded text-xs ${
                  step.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                  step.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-700' :
                  'bg-red-100 text-red-700'
                }`}>
                  {Math.round(step.confidence * 100)}%
                </span>
              </div>
            ))}
          </div>
          
          {/* Tools Used */}
          {xai.tool_decisions?.length > 0 && (
            <div className="space-y-1">
              <span className="font-medium text-muted-foreground">Tools Used:</span>
              <div className="flex flex-wrap gap-1">
                {xai.tool_decisions.filter(t => t.selected).map((tool, i) => (
                  <span key={i} className="inline-flex items-center gap-1 px-2 py-1 bg-purple-100 text-purple-800 rounded-full">
                    <Zap className="w-3 h-3" />
                    {tool.display_name || tool.tool}
                  </span>
                ))}
              </div>
            </div>
          )}
          
          {/* Duration */}
          {xai.duration_ms && (
            <div className="text-muted-foreground">
              ⏱️ Response time: {Math.round(xai.duration_ms)}ms
            </div>
          )}
        </div>
      )}
    </div>
  );
};

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
      // Use streaming endpoint
      const response = await fetch(`http://localhost:8000/agent/query/stream?query=${encodeURIComponent(userMessage)}`);
      
      if (!response.ok) {
        throw new Error('Stream failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      let streamedContent = '';
      let confidence = null;
      let xaiData = null;
      
      // Add empty agent message that we'll update
      setMessages(prev => [...prev, { type: 'agent', content: '', isStreaming: true }]);
      setIsTyping(false);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.type === 'metadata') {
                confidence = data.confidence;
                xaiData = data.xai;
              } else if (data.type === 'content') {
                streamedContent += data.content;
                // Update the last message with streamed content
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastIdx = newMessages.length - 1;
                  if (lastIdx >= 0 && newMessages[lastIdx].type === 'agent') {
                    newMessages[lastIdx] = {
                      ...newMessages[lastIdx],
                      content: streamedContent,
                      isStreaming: true
                    };
                  }
                  return newMessages;
                });
              } else if (data.type === 'done') {
                // Finalize the message
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastIdx = newMessages.length - 1;
                  if (lastIdx >= 0 && newMessages[lastIdx].type === 'agent') {
                    newMessages[lastIdx] = {
                      ...newMessages[lastIdx],
                      content: streamedContent,
                      confidence: confidence,
                      xai: xaiData,
                      isStreaming: false
                    };
                  }
                  return newMessages;
                });
              }
            } catch (e) {
              // Skip invalid JSON
            }
          }
        }
      }

      // Save to conversation history
      if (convId && streamedContent) {
        saveMessages(convId, userMessage, streamedContent);
      }
    } catch (error) {
      console.error('Streaming error:', error);
      // Fallback to non-streaming
      try {
        const res = await fetch(`http://localhost:8000/agent/query?query=${encodeURIComponent(userMessage)}`);
        const data = await res.json();
        
        setMessages(prev => {
          // Remove the streaming placeholder if exists
          const filtered = prev.filter(m => !m.isStreaming);
          return [...filtered, {
            type: 'agent',
            content: data.answer || 'Sorry, I couldn\'t process your request.',
            confidence: data.confidence,
          }];
        });
        
        if (convId) {
          saveMessages(convId, userMessage, data.answer);
        }
      } catch (fallbackError) {
        setMessages(prev => {
          const filtered = prev.filter(m => !m.isStreaming);
          return [...filtered, {
            type: 'agent',
            content: 'Sorry, I\'m having trouble connecting to the server.'
          }];
        });
      }
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
          <div className="p-8 flex flex-col items-center justify-center min-h-[400px]">
            {/* Professional Medical Icon - using platform primary color */}
            <div className="relative mb-6">
              <div className="w-16 h-16 rounded-2xl bg-primary flex items-center justify-center shadow-lg">
                <Stethoscope className="w-8 h-8 text-primary-foreground" />
              </div>
            </div>
            
            <h3 className="text-xl font-semibold mb-2 text-foreground">
              Medication Assistant
            </h3>
            <p className="text-muted-foreground text-sm mb-6 max-w-md mx-auto text-center">
              Get reliable information about medications, drug interactions, dosages, and safety guidelines.
            </p>
            
            {/* Feature Cards - all using primary color */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8 w-full max-w-xl">
              <div className="flex flex-col items-center p-3 bg-primary/5 rounded-lg border border-primary/10">
                <Pill className="w-5 h-5 text-primary mb-1" />
                <span className="text-xs text-muted-foreground">Drug Info</span>
              </div>
              <div className="flex flex-col items-center p-3 bg-primary/5 rounded-lg border border-primary/10">
                <Shield className="w-5 h-5 text-primary mb-1" />
                <span className="text-xs text-muted-foreground">Interactions</span>
              </div>
              <div className="flex flex-col items-center p-3 bg-primary/5 rounded-lg border border-primary/10">
                <Brain className="w-5 h-5 text-primary mb-1" />
                <span className="text-xs text-muted-foreground">AI Analysis</span>
              </div>
              <div className="flex flex-col items-center p-3 bg-primary/5 rounded-lg border border-primary/10">
                <Search className="w-5 h-5 text-primary mb-1" />
                <span className="text-xs text-muted-foreground">Search</span>
              </div>
            </div>
            
            {/* Quick Questions */}
            <div className="w-full max-w-lg">
              <p className="text-xs text-muted-foreground mb-3 text-center font-medium">Suggested questions</p>
              <div className="space-y-2">
                {quickQuestions.map((q, i) => (
                  <button
                    key={i}
                    onClick={() => setInput(q)}
                    className="w-full px-4 py-3 bg-muted/30 hover:bg-primary/5 border border-border hover:border-primary/30 rounded-lg text-sm text-left transition-all duration-200"
                  >
                    <span className="text-muted-foreground">{q}</span>
                  </button>
                ))}
              </div>
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
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  message.type === 'agent' 
                    ? 'bg-primary' 
                    : 'bg-muted'
                }`}>
                  {message.type === 'agent' ? (
                    <Stethoscope className="w-4 h-4 text-primary-foreground" />
                  ) : (
                    <User className="w-4 h-4 text-muted-foreground" />
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
                  >
                    <span dangerouslySetInnerHTML={{ __html: formatMessage(message.content) }} />
                    {message.isStreaming && (
                      <span className="inline-block w-2 h-4 bg-blue-500 ml-1 animate-pulse" />
                    )}
                  </div>
                  
                  {/* XAI Explainability Section */}
                  {message.type === 'agent' && message.xai && !message.isStreaming && (
                    <XAISection xai={message.xai} />
                  )}
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
