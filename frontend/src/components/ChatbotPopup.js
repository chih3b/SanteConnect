import { useState, useRef, useEffect } from 'react';
import {
  MessageCircle,
  X,
  Send,
  Minimize2,
  Maximize2,
  Bot,
  User,
  Loader2,
  AlertCircle,
  Stethoscope,
  Activity,
  Heart,
  Pill,
  FileText,
  ChevronDown,
  ChevronUp,
  RefreshCw,
} from 'lucide-react';

const RAIF_API = 'http://localhost:8002';

const ChatbotPopup = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  
  // Medical data states
  const [detectedSymptoms, setDetectedSymptoms] = useState([]);
  const [possibleDiseases, setPossibleDiseases] = useState([]);
  const [identifiedDisease, setIdentifiedDisease] = useState(null);
  const [treatments, setTreatments] = useState([]);
  const [urgencyLevel, setUrgencyLevel] = useState('');
  const [phase, setPhase] = useState('initial');
  const [shouldEnd, setShouldEnd] = useState(false);
  const [showInfoPanel, setShowInfoPanel] = useState(false);
  
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    if (isOpen && !isMinimized && inputRef.current) {
      inputRef.current.focus();
    }
  }, [isOpen, isMinimized]);

  const initSession = async () => {
    if (sessionId) return;
    
    try {
      const response = await fetch(`${RAIF_API}/api/session/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ patient_name: 'Patient' }),
      });
      
      if (response.ok) {
        const data = await response.json();
        setSessionId(data.session_id);
        
        setMessages([{
          type: 'bot',
          content: "Bonjour! Je suis Dr. Raif, votre assistant médical IA. 👋\n\nJe suis là pour analyser vos symptômes et vous aider à comprendre votre état de santé.\n\n💡 Décrivez vos symptômes le plus précisément possible (localisation, intensité, durée).",
          timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        }]);
      }
    } catch (error) {
      console.error('Session init error:', error);
      setMessages([{
        type: 'bot',
        content: "Bonjour! Je suis Dr. Raif. Le serveur n'est pas disponible. Veuillez réessayer plus tard.",
        timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      }]);
    }
  };

  const openChat = () => {
    setIsOpen(true);
    setIsMinimized(false);
    initSession();
  };

  const sendMessage = async () => {
    if (!input.trim() || loading || !sessionId) return;

    const userMessage = input.trim();
    setInput('');
    
    setMessages(prev => [...prev, {
      type: 'user',
      content: userMessage,
      timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
    }]);
    
    setLoading(true);

    try {
      const response = await fetch(`${RAIF_API}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          message: userMessage,
        }),
      });

      const data = await response.json();
      
      setMessages(prev => [...prev, {
        type: 'bot',
        content: data.response,
        formatted: data.formatted_response,
        timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        symptoms: data.new_symptoms,
        disease: data.identified_disease,
        urgency: data.urgency_level,
      }]);

      // Update medical data
      if (data.detected_symptoms?.length > 0) {
        setDetectedSymptoms(data.detected_symptoms);
        setShowInfoPanel(true);
      }
      if (data.possible_diseases?.length > 0) {
        setPossibleDiseases(data.possible_diseases);
      }
      if (data.identified_disease) {
        setIdentifiedDisease(data.identified_disease);
        setTreatments(data.identified_disease.treatments || []);
      }
      if (data.urgency_level) {
        setUrgencyLevel(data.urgency_level);
      }
      setPhase(data.phase);
      setShouldEnd(data.should_end);

    } catch (error) {
      console.error('Chat error:', error);
      setMessages(prev => [...prev, {
        type: 'bot',
        content: "Désolé, je rencontre des difficultés. Veuillez réessayer.",
        timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        isError: true,
      }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const resetChat = async () => {
    if (sessionId) {
      try {
        await fetch(`${RAIF_API}/api/session/${sessionId}`, { method: 'DELETE' });
      } catch (e) {}
    }
    setSessionId(null);
    setMessages([]);
    setDetectedSymptoms([]);
    setPossibleDiseases([]);
    setIdentifiedDisease(null);
    setTreatments([]);
    setUrgencyLevel('');
    setPhase('initial');
    setShouldEnd(false);
    setShowInfoPanel(false);
    initSession();
  };

  const getUrgencyColor = (urgency) => {
    if (!urgency) return 'bg-muted text-foreground';
    const u = urgency.toLowerCase();
    if (u.includes('critique')) return 'bg-red-500 text-white animate-pulse';
    if (u.includes('élevé') || u.includes('eleve')) return 'bg-orange-500 text-white';
    if (u.includes('modéré') || u.includes('modere')) return 'bg-yellow-500 text-foreground';
    return 'bg-green-500 text-white';
  };

  const getPhaseLabel = (p) => {
    const phases = {
      initial: 'Écoute',
      gathering: 'Collecte',
      analyzing: 'Analyse',
      diagnosis: 'Diagnostic',
      treatment: 'Traitement',
      completed: 'Terminé'
    };
    return phases[p] || p;
  };

  const formatMessage = (content) => {
    return content
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br />');
  };

  return (
    <>
      {/* Chat Button */}
      {!isOpen && (
        <button
          onClick={openChat}
          className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 w-12 h-12 sm:w-14 sm:h-14 bg-primary rounded-full shadow-lg hover:shadow-xl transition-all duration-300 flex items-center justify-center text-white z-50 hover:scale-110"
          title="Parler avec Dr. Raif"
        >
          <MessageCircle className="w-5 h-5 sm:w-6 sm:h-6" />
          <span className="absolute -top-1 -right-1 w-3 h-3 sm:w-4 sm:h-4 bg-green-500 rounded-full border-2 border-white animate-pulse" />
        </button>
      )}

      {/* Chat Window */}
      {isOpen && (
        <div
          className={`fixed bg-card dark:bg-gray-900 shadow-2xl z-50 flex flex-col transition-all duration-300 border border-border dark:border-gray-700 ${
            isMinimized 
              ? 'bottom-4 right-4 w-64 sm:w-72 h-14 rounded-2xl' 
              : isExpanded 
                ? 'inset-2 sm:bottom-4 sm:right-4 sm:left-auto sm:top-auto sm:w-[800px] sm:h-[600px] rounded-xl sm:rounded-2xl' 
                : 'inset-2 sm:inset-auto sm:bottom-4 sm:right-4 sm:w-96 sm:h-[550px] rounded-xl sm:rounded-2xl'
          }`}
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 bg-primary rounded-t-2xl">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-full bg-card/20 flex items-center justify-center">
                <Stethoscope size={18} className="text-white" />
              </div>
              <div>
                <h3 className="text-white font-semibold text-sm">Dr. Raif</h3>
                <p className="text-white/70 text-xs">Assistant Médical IA</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {/* Expand button - hidden on mobile */}
              {!isMinimized && (
                <button
                  onClick={() => setIsExpanded(!isExpanded)}
                  className="hidden sm:block p-1.5 hover:bg-card/20 rounded-lg transition-colors"
                  title={isExpanded ? "Réduire" : "Agrandir"}
                >
                  {isExpanded ? <ChevronDown size={16} className="text-white" /> : <ChevronUp size={16} className="text-white" />}
                </button>
              )}
              {/* Minimize button - hidden on mobile */}
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="hidden sm:block p-1.5 hover:bg-card/20 rounded-lg transition-colors"
              >
                {isMinimized ? <Maximize2 size={16} className="text-white" /> : <Minimize2 size={16} className="text-white" />}
              </button>
              <button
                onClick={() => setIsOpen(false)}
                className="p-1.5 hover:bg-card/20 rounded-lg transition-colors"
              >
                <X size={16} className="text-white" />
              </button>
            </div>
          </div>

          {/* Chat Content */}
          {!isMinimized && (
            <div className={`flex min-h-0 ${isExpanded ? 'flex-row flex-1' : 'flex-col flex-1'}`}>
              {/* Messages Panel */}
              <div className={`flex flex-col min-h-0 ${isExpanded ? 'flex-1' : 'flex-1'}`}>
                {/* Phase Progress Bar */}
                <div className="flex-shrink-0 px-3 py-2 bg-muted dark:bg-gray-800 border-b border-border dark:border-gray-700">
                  <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1">
                      <Activity size={12} className="text-primary" />
                      <span className="text-muted-foreground dark:text-muted-foreground">Phase: {getPhaseLabel(phase)}</span>
                    </div>
                    {urgencyLevel && (
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${getUrgencyColor(urgencyLevel)}`}>
                        {urgencyLevel}
                      </span>
                    )}
                  </div>
                  {/* Progress dots */}
                  <div className="flex items-center gap-1 mt-2">
                    {['initial', 'gathering', 'analyzing', 'diagnosis', 'treatment', 'completed'].map((p, i) => (
                      <div key={p} className="flex items-center">
                        <div className={`w-2 h-2 rounded-full ${
                          phase === p ? 'bg-primary' : 
                          ['initial', 'gathering', 'analyzing', 'diagnosis', 'treatment', 'completed'].indexOf(phase) > i 
                            ? 'bg-green-500' : 'bg-gray-300'
                        }`} />
                        {i < 5 && <div className={`w-4 h-0.5 ${
                          ['initial', 'gathering', 'analyzing', 'diagnosis', 'treatment', 'completed'].indexOf(phase) > i 
                            ? 'bg-green-500' : 'bg-gray-300'
                        }`} />}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Messages - scrollable area */}
                <div className="flex-1 min-h-0 overflow-y-auto p-3 space-y-3">
                  {messages.map((msg, index) => (
                    <div
                      key={index}
                      className={`flex ${msg.type === 'user' ? 'justify-end' : 'justify-start'}`}
                    >
                      <div
                        className={`max-w-[85%] rounded-2xl px-3 py-2 ${
                          msg.type === 'user'
                            ? 'bg-primary text-white rounded-br-md'
                            : msg.isError
                            ? 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 rounded-bl-md'
                            : 'bg-muted dark:bg-gray-800 text-foreground dark:text-gray-200 rounded-bl-md'
                        }`}
                      >
                        <div className="flex items-start gap-2">
                          {msg.type === 'bot' && (
                            <Bot size={14} className={`mt-0.5 flex-shrink-0 ${msg.isError ? 'text-red-500' : 'text-primary'}`} />
                          )}
                          <div className="flex-1">
                            {msg.formatted ? (
                              <p className="text-sm whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: msg.formatted }} />
                            ) : (
                              <p className="text-sm whitespace-pre-wrap" dangerouslySetInnerHTML={{ __html: formatMessage(msg.content) }} />
                            )}
                            
                            {msg.urgency && (
                              <div className={`flex items-center gap-1 mt-2 text-xs px-2 py-1 rounded ${getUrgencyColor(msg.urgency)}`}>
                                <AlertCircle size={12} />
                                <span>Urgence: {msg.urgency}</span>
                              </div>
                            )}
                          </div>
                          {msg.type === 'user' && (
                            <User size={14} className="mt-0.5 flex-shrink-0 text-white/70" />
                          )}
                        </div>
                        <p className={`text-xs mt-1 ${msg.type === 'user' ? 'text-white/60' : 'text-muted-foreground'}`}>
                          {msg.timestamp}
                        </p>
                      </div>
                    </div>
                  ))}
                  
                  {loading && (
                    <div className="flex justify-start">
                      <div className="bg-muted dark:bg-gray-800 rounded-2xl rounded-bl-md px-4 py-3">
                        <div className="flex items-center gap-2">
                          <Loader2 size={16} className="animate-spin text-primary" />
                          <span className="text-sm text-muted-foreground">Dr. Raif analyse...</span>
                        </div>
                      </div>
                    </div>
                  )}
                  
                  <div ref={messagesEndRef} />
                </div>

                {/* Consultation ended banner */}
                {shouldEnd && (
                  <div className="flex-shrink-0 px-3 py-2 bg-green-50 dark:bg-green-900/20 border-t border-green-200 dark:border-green-800">
                    <div className="flex items-center gap-2 text-green-700 dark:text-green-300">
                      <FileText size={16} />
                      <div>
                        <p className="text-sm font-medium">Consultation terminée</p>
                        <p className="text-xs">Un rapport a été généré et envoyé.</p>
                      </div>
                    </div>
                  </div>
                )}

                {/* Input */}
                <div className="flex-shrink-0 p-3 border-t border-border dark:border-gray-700">
                  <div className="flex items-center gap-2">
                    <input
                      ref={inputRef}
                      type="text"
                      value={input}
                      onChange={(e) => setInput(e.target.value)}
                      onKeyDown={handleKeyDown}
                      placeholder={shouldEnd ? "Consultation terminée" : "Décrivez vos symptômes..."}
                      disabled={loading || shouldEnd}
                      className="flex-1 px-3 py-2 text-sm border border-border dark:border-gray-600 rounded-xl focus:outline-none focus:ring-2 focus:ring-primary dark:bg-gray-800 dark:text-white"
                    />
                    <button
                      onClick={sendMessage}
                      disabled={!input.trim() || loading || shouldEnd}
                      className="p-2 bg-primary text-white rounded-xl hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    >
                      <Send size={18} />
                    </button>
                  </div>
                  <div className="flex items-center justify-between mt-2">
                    <button
                      onClick={() => setShowInfoPanel(!showInfoPanel)}
                      className="text-xs text-primary hover:underline flex items-center gap-1"
                    >
                      <Activity size={12} />
                      {showInfoPanel ? 'Masquer infos' : 'Voir infos médicales'}
                    </button>
                    <button
                      onClick={resetChat}
                      className="text-xs text-primary hover:underline flex items-center gap-1"
                    >
                      <RefreshCw size={12} />
                      Nouvelle consultation
                    </button>
                  </div>
                </div>
              </div>

              {/* Info Panel (expanded mode or toggle) */}
              {(isExpanded || showInfoPanel) && (detectedSymptoms.length > 0 || identifiedDisease) && (
                <div className={`${isExpanded ? 'sm:w-72 sm:border-l border-t sm:border-t-0' : 'border-t'} border-border dark:border-gray-700 bg-muted dark:bg-gray-800 overflow-y-auto max-h-48 sm:max-h-none`}>
                  <div className="p-3 space-y-3">
                    {/* Symptoms */}
                    {detectedSymptoms.length > 0 && (
                      <div className="bg-card dark:bg-gray-900 rounded-lg p-3 shadow-sm">
                        <h4 className="text-xs font-semibold text-red-600 flex items-center gap-1 mb-2">
                          <AlertCircle size={12} />
                          Symptômes détectés ({detectedSymptoms.length})
                        </h4>
                        <div className="flex flex-wrap gap-1">
                          {detectedSymptoms.map((s, i) => (
                            <span key={i} className="text-xs px-2 py-0.5 bg-red-100 text-red-700 rounded-full">
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Disease */}
                    {identifiedDisease && (
                      <div className="bg-card dark:bg-gray-900 rounded-lg p-3 shadow-sm">
                        <h4 className="text-xs font-semibold text-green-600 flex items-center gap-1 mb-2">
                          <Heart size={12} />
                          Diagnostic probable
                        </h4>
                        <p className="text-sm font-medium text-foreground dark:text-gray-200">
                          {identifiedDisease.name}
                        </p>
                        {identifiedDisease.confidence && (
                          <div className="mt-2">
                            <div className="flex justify-between text-xs text-muted-foreground mb-1">
                              <span>Confiance</span>
                              <span>{Math.round(identifiedDisease.confidence * 100)}%</span>
                            </div>
                            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                              <div 
                                className="h-full bg-green-500 rounded-full"
                                style={{ width: `${identifiedDisease.confidence * 100}%` }}
                              />
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Possible diseases */}
                    {possibleDiseases.length > 0 && (
                      <div className="bg-card dark:bg-gray-900 rounded-lg p-3 shadow-sm">
                        <h4 className="text-xs font-semibold text-blue-600 flex items-center gap-1 mb-2">
                          <Stethoscope size={12} />
                          Diagnostics différentiels
                        </h4>
                        <div className="space-y-1">
                          {possibleDiseases.slice(0, 3).map((d, i) => (
                            <div key={i} className="text-xs text-muted-foreground dark:text-muted-foreground flex justify-between">
                              <span>{d.name}</span>
                              <span className="text-muted-foreground">{Math.round((d.confidence || 0) * 100)}%</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Treatments */}
                    {treatments.length > 0 && (
                      <div className="bg-card dark:bg-gray-900 rounded-lg p-3 shadow-sm">
                        <h4 className="text-xs font-semibold text-blue-600 flex items-center gap-1 mb-2">
                          <Pill size={12} />
                          Traitements recommandés
                        </h4>
                        <ul className="space-y-1">
                          {treatments.slice(0, 5).map((t, i) => (
                            <li key={i} className="text-xs text-muted-foreground dark:text-muted-foreground flex items-start gap-1">
                              <span className="text-blue-500">•</span>
                              {t}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {/* Urgency */}
                    {urgencyLevel && (
                      <div className={`rounded-lg p-3 ${getUrgencyColor(urgencyLevel)}`}>
                        <div className="flex items-center gap-2">
                          <AlertCircle size={16} />
                          <div>
                            <p className="text-xs font-semibold">Niveau d'urgence</p>
                            <p className="text-sm font-bold">{urgencyLevel}</p>
                          </div>
                        </div>
                        {urgencyLevel.toLowerCase().includes('critique') && (
                          <p className="text-xs mt-2">⚠️ Consultez immédiatement un médecin ou appelez le 15</p>
                        )}
                      </div>
                    )}

                    {/* Report generated */}
                    {shouldEnd && (
                      <div className="bg-card dark:bg-gray-900 rounded-lg p-3 shadow-sm text-center">
                        <FileText size={24} className="mx-auto text-primary mb-2" />
                        <p className="text-xs font-semibold text-foreground dark:text-gray-200">Rapport Médical</p>
                        <p className="text-xs text-muted-foreground">Généré et envoyé au médecin</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
};

export default ChatbotPopup;
