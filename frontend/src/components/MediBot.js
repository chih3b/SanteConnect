import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  AlertTriangle,
  Activity,
  Video,
  VideoOff,
  RotateCcw,
  Download,
  Clock,
  MessageSquare,
  Heart,
  Stethoscope,
  Brain,
  Eye,
  AlertCircle,
} from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';

const MEDIBOT_API = 'http://localhost:8001';

// Fatigue detection constants
const EAR_THRESHOLD = 0.25;
const MAR_THRESHOLD = 0.6;
const CONSECUTIVE_FRAMES_FOR_BLINK = 3;
const YAWN_CONSECUTIVE_FRAMES = 15;

// Calculate Eye Aspect Ratio
const calculateEAR = (eye) => {
  if (!eye || eye.length < 6) return 1;
  const v1 = Math.sqrt(Math.pow(eye[1].x - eye[5].x, 2) + Math.pow(eye[1].y - eye[5].y, 2));
  const v2 = Math.sqrt(Math.pow(eye[2].x - eye[4].x, 2) + Math.pow(eye[2].y - eye[4].y, 2));
  const h = Math.sqrt(Math.pow(eye[0].x - eye[3].x, 2) + Math.pow(eye[0].y - eye[3].y, 2));
  if (h === 0) return 1;
  return (v1 + v2) / (2.0 * h);
};

// Calculate Mouth Aspect Ratio for yawn detection
const calculateMAR = (mouth) => {
  if (!mouth || mouth.length < 8) return 0;
  const v = Math.sqrt(Math.pow(mouth[2].x - mouth[6].x, 2) + Math.pow(mouth[2].y - mouth[6].y, 2));
  const h = Math.sqrt(Math.pow(mouth[0].x - mouth[4].x, 2) + Math.pow(mouth[0].y - mouth[4].y, 2));
  if (h === 0) return 0;
  return v / h;
};

const MediBot = () => {
  // State
  const [conversationStarted, setConversationStarted] = useState(false);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabled] = useState(true);
  const [voiceModeEnabled, setVoiceModeEnabled] = useState(false);
  const [potentialDiseases, setPotentialDiseases] = useState([]);
  const [showEmergency, setShowEmergency] = useState(false);
  const [sessionId] = useState(() => `session_${Date.now()}`);

  // Camera & Fatigue Detection
  const [cameraEnabled, setCameraEnabled] = useState(false);
  const [localStream, setLocalStream] = useState(null);
  const [fatigueLevel, setFatigueLevel] = useState('none');
  const [fatigueMetrics, setFatigueMetrics] = useState({ ear: 1, blinkCount: 0, yawnCount: 0 });
  const [faceMeshReady, setFaceMeshReady] = useState(false);

  // Stats
  const [consultationTime, setConsultationTime] = useState(0);
  const [symptomsCount, setSymptomsCount] = useState(0);

  // Refs
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const synthRef = useRef(window.speechSynthesis);
  const audioRef = useRef(null);
  const videoRef = useRef(null);
  const faceMeshRef = useRef(null);
  const animationRef = useRef(null);
  const silenceTimerRef = useRef(null);
  const accumulatedTextRef = useRef('');

  // Fatigue tracking refs
  const blinkCountRef = useRef(0);
  const yawnCountRef = useRef(0);
  const eyeClosedFramesRef = useRef(0);
  const yawnCounterRef = useRef(0);
  const startTimeRef = useRef(Date.now());

  const SILENCE_DELAY = 2;

  // Scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Consultation timer
  useEffect(() => {
    let interval = null;
    if (conversationStarted) {
      interval = setInterval(() => {
        setConsultationTime((prev) => prev + 1);
      }, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [conversationStarted]);

  // Format time
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${String(mins).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  };


  // Speak text using browser TTS
  const speakText = useCallback(
    (text) => {
      if (!voiceEnabled) return Promise.resolve();

      return new Promise((resolve) => {
        synthRef.current.cancel();
        const cleanText = text.replace(/[*_#⚠️❓•]/g, '').replace(/\n/g, ' ');
        const utterance = new SpeechSynthesisUtterance(cleanText);
        utterance.lang = 'fr-FR';
        utterance.rate = 0.9;
        utterance.pitch = 1.0;

        const voices = synthRef.current.getVoices();
        const frenchVoice = voices.find((v) => v.lang.startsWith('fr'));
        if (frenchVoice) utterance.voice = frenchVoice;

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => {
          setIsSpeaking(false);
          resolve();
        };
        utterance.onerror = () => {
          setIsSpeaking(false);
          resolve();
        };

        synthRef.current.speak(utterance);
      });
    },
    [voiceEnabled]
  );

  // Play audio from base64
  const playAudioBase64 = useCallback(
    (base64Audio) => {
      if (!voiceEnabled) return Promise.resolve();

      return new Promise((resolve) => {
        try {
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current = null;
          }

          const binaryString = atob(base64Audio);
          const bytes = new Uint8Array(binaryString.length);
          for (let i = 0; i < binaryString.length; i++) {
            bytes[i] = binaryString.charCodeAt(i);
          }
          const audioBlob = new Blob([bytes], { type: 'audio/mpeg' });
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);
          audioRef.current = audio;

          audio.onplay = () => setIsSpeaking(true);
          audio.onended = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
            audioRef.current = null;
            resolve();
          };
          audio.onerror = () => {
            setIsSpeaking(false);
            resolve();
          };

          audio.play().catch(() => {
            speakText(base64Audio);
            resolve();
          });
        } catch (error) {
          console.error('Audio playback error:', error);
          resolve();
        }
      });
    },
    [voiceEnabled, speakText]
  );

  // Calculate fatigue level
  const calculateFatigueLevel = useCallback((ear, blinkRate, yawns) => {
    let score = 0;
    if (ear < 0.2) score += 3;
    else if (ear < EAR_THRESHOLD) score += 2;
    if (blinkRate < 10 || blinkRate > 25) score += 2;
    if (yawns > 3) score += 3;
    else if (yawns > 1) score += 2;
    else if (yawns > 0) score += 1;

    if (score >= 5) return 'high';
    if (score >= 3) return 'medium';
    if (score >= 1) return 'low';
    return 'none';
  }, []);

  // Process face landmarks for fatigue detection
  const processLandmarks = useCallback(
    (landmarks) => {
      if (!landmarks || landmarks.length === 0) return;

      const leftEyeIndices = [33, 160, 158, 133, 153, 144];
      const rightEyeIndices = [362, 385, 387, 263, 373, 380];
      const mouthIndices = [61, 146, 91, 181, 84, 17, 314, 405];

      const leftEye = leftEyeIndices.map((idx) => landmarks[idx]);
      const rightEye = rightEyeIndices.map((idx) => landmarks[idx]);
      const mouth = mouthIndices.map((idx) => landmarks[idx]);

      const leftEAR = calculateEAR(leftEye);
      const rightEAR = calculateEAR(rightEye);
      const avgEAR = (leftEAR + rightEAR) / 2;

      // Blink detection
      if (avgEAR < EAR_THRESHOLD) {
        eyeClosedFramesRef.current += 1;
      } else {
        if (eyeClosedFramesRef.current >= CONSECUTIVE_FRAMES_FOR_BLINK) {
          blinkCountRef.current += 1;
        }
        eyeClosedFramesRef.current = 0;
      }

      // Yawn detection
      const mar = calculateMAR(mouth);
      if (mar > MAR_THRESHOLD) {
        yawnCounterRef.current += 1;
        if (yawnCounterRef.current >= YAWN_CONSECUTIVE_FRAMES) {
          yawnCountRef.current += 1;
          yawnCounterRef.current = 0;
        }
      } else {
        yawnCounterRef.current = 0;
      }

      // Calculate blink rate
      const elapsedMinutes = (Date.now() - startTimeRef.current) / 60000;
      const blinkRate = elapsedMinutes > 0 ? blinkCountRef.current / elapsedMinutes : 0;

      // Update fatigue level
      const level = calculateFatigueLevel(avgEAR, blinkRate, yawnCountRef.current);
      setFatigueLevel(level);
      setFatigueMetrics({
        ear: avgEAR,
        blinkCount: blinkCountRef.current,
        yawnCount: yawnCountRef.current,
      });

      // Report to backend periodically
      if (Math.random() < 0.02) {
        fetch(`${MEDIBOT_API}/fatigue/report`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            eye_aspect_ratio: avgEAR,
            is_yawning: mar > MAR_THRESHOLD,
            blink_count: blinkCountRef.current,
            fatigue_level: level,
            timestamp: new Date().toISOString(),
          }),
        }).catch(() => {});
      }
    },
    [calculateFatigueLevel]
  );


  // Initialize MediaPipe FaceMesh
  useEffect(() => {
    if (!cameraEnabled) return;

    const initFaceMesh = () => {
      if (typeof window.FaceMesh === 'undefined') {
        const script1 = document.createElement('script');
        script1.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/face_mesh.js';
        script1.crossOrigin = 'anonymous';

        const script2 = document.createElement('script');
        script2.src = 'https://cdn.jsdelivr.net/npm/@mediapipe/camera_utils/camera_utils.js';
        script2.crossOrigin = 'anonymous';

        script1.onload = () => {
          script2.onload = () => setupFaceMesh();
          document.head.appendChild(script2);
        };
        document.head.appendChild(script1);
      } else {
        setupFaceMesh();
      }
    };

    const setupFaceMesh = () => {
      if (!window.FaceMesh) return;

      const faceMesh = new window.FaceMesh({
        locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
      });

      faceMesh.setOptions({
        maxNumFaces: 1,
        refineLandmarks: true,
        minDetectionConfidence: 0.5,
        minTrackingConfidence: 0.5,
      });

      faceMesh.onResults((results) => {
        if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
          processLandmarks(results.multiFaceLandmarks[0]);
        }
      });

      faceMeshRef.current = faceMesh;
      setFaceMeshReady(true);
    };

    initFaceMesh();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [cameraEnabled, processLandmarks]);

  // Process video frames for fatigue detection
  useEffect(() => {
    if (!faceMeshReady || !faceMeshRef.current || !videoRef.current || !cameraEnabled) return;

    const processFrame = () => {
      if (videoRef.current && videoRef.current.readyState >= 2) {
        faceMeshRef.current.send({ image: videoRef.current }).then(() => {
          animationRef.current = requestAnimationFrame(processFrame);
        });
      } else {
        animationRef.current = requestAnimationFrame(processFrame);
      }
    };

    processFrame();

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, [faceMeshReady, cameraEnabled]);

  // Clear silence timer
  const clearSilenceTimer = useCallback(() => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }
  }, []);

  // Send message to API
  const sendMessageToAPI = useCallback(
    async (text) => {
      if (!text.trim() || loading) return;

      const userMessage = text.trim();
      const newUserMsg = {
        type: 'user',
        content: userMessage,
        timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
      };
      setMessages((prev) => [...prev, newUserMsg]);
      setLoading(true);

      // Detect symptoms
      const symptomKeywords = ['douleur', 'mal', 'fièvre', 'toux', 'fatigue', 'nausée', 'vertige'];
      symptomKeywords.forEach((keyword) => {
        if (userMessage.toLowerCase().includes(keyword)) {
          setSymptomsCount((prev) => prev + 1);
        }
      });

      try {
        const response = await fetch(`${MEDIBOT_API}/chat`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ message: userMessage, session_id: sessionId }),
        });

        const data = await response.json();

        const botMsg = {
          type: 'bot',
          content: data.response,
          timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
          diseases: data.potential_diseases,
          isEmergency: data.is_emergency,
          processingTime: data.processing_time,
        };
        setMessages((prev) => [...prev, botMsg]);

        if (data.potential_diseases?.length > 0) {
          setPotentialDiseases(data.potential_diseases);
        }

        if (data.is_emergency) {
          setShowEmergency(true);
        }

        // Play audio response
        if (data.audio_base64) {
          await playAudioBase64(data.audio_base64);
        } else if (voiceEnabled) {
          await speakText(data.response);
        }
      } catch (error) {
        console.error('Chat error:', error);
        const errorMsg = {
          type: 'bot',
          content: 'Désolé, je rencontre des difficultés de connexion. Veuillez réessayer.',
          timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
        };
        setMessages((prev) => [...prev, errorMsg]);
      } finally {
        setLoading(false);
      }
    },
    [loading, sessionId, playAudioBase64, speakText, voiceEnabled]
  );


  // Setup speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.lang = 'fr-FR';
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.maxAlternatives = 1;

      recognition.onresult = (event) => {
        let finalTranscript = '';
        let interimTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }

        const displayText = accumulatedTextRef.current + (finalTranscript || interimTranscript);
        setInput(displayText);

        if (finalTranscript.trim()) {
          accumulatedTextRef.current += finalTranscript;
          // Start silence timer
          clearSilenceTimer();
          silenceTimerRef.current = setTimeout(() => {
            const textToSend = accumulatedTextRef.current.trim();
            if (textToSend.length > 2) {
              recognition.stop();
              sendMessageToAPI(textToSend);
            }
            accumulatedTextRef.current = '';
            setInput('');
          }, SILENCE_DELAY * 1000);
        }
      };

      recognition.onstart = () => setIsListening(true);
      recognition.onend = () => {
        setIsListening(false);
        // Restart if voice mode is enabled and not speaking/loading
        if (voiceModeEnabled && !isSpeaking && !loading && conversationStarted) {
          setTimeout(() => {
            if (voiceModeEnabled && !isSpeaking && !loading) {
              try {
                recognition.start();
              } catch (e) {}
            }
          }, 1500);
        }
      };
      recognition.onerror = () => setIsListening(false);

      recognitionRef.current = recognition;
    }

    return () => {
      clearSilenceTimer();
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {}
      }
    };
  }, [clearSilenceTimer, sendMessageToAPI, voiceModeEnabled, isSpeaking, loading, conversationStarted]);

  // Auto-restart recognition after bot speaks
  useEffect(() => {
    if (voiceModeEnabled && conversationStarted && !isSpeaking && !loading && recognitionRef.current) {
      const timer = setTimeout(() => {
        if (!isListening && voiceModeEnabled && !isSpeaking && !loading) {
          try {
            accumulatedTextRef.current = '';
            setInput('');
            recognitionRef.current.start();
          } catch (e) {}
        }
      }, 1500);
      return () => clearTimeout(timer);
    }
  }, [isSpeaking, loading, voiceModeEnabled, conversationStarted, isListening]);

  // Toggle camera
  const toggleCamera = () => {
    if (!cameraEnabled) {
      navigator.mediaDevices
        .getUserMedia({ video: true, audio: false })
        .then((stream) => {
          if (videoRef.current) {
            videoRef.current.srcObject = stream;
          }
          setLocalStream(stream);
          setCameraEnabled(true);
        })
        .catch((error) => {
          console.error('Camera error:', error);
          alert("Impossible d'accéder à la caméra");
        });
    } else {
      if (localStream) {
        localStream.getTracks().forEach((track) => track.stop());
      }
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      setLocalStream(null);
      setCameraEnabled(false);
      setFaceMeshReady(false);
    }
  };

  // Toggle voice mode
  const toggleVoiceMode = () => {
    const newState = !voiceModeEnabled;
    setVoiceModeEnabled(newState);

    if (newState && conversationStarted && !isSpeaking && !loading && recognitionRef.current) {
      setTimeout(() => {
        try {
          accumulatedTextRef.current = '';
          recognitionRef.current.start();
        } catch (e) {}
      }, 500);
    } else if (!newState && recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch (e) {}
    }
  };

  // Start consultation
  const startConsultation = () => {
    setConversationStarted(true);
    setVoiceModeEnabled(true);
    startTimeRef.current = Date.now();

    const greeting =
      "Bonjour ! Je suis Dr. MediBot, votre assistant médical virtuel. Je vais vous poser quelques questions pour comprendre vos symptômes. Pour commencer, pouvez-vous me dire ce qui vous amène aujourd'hui ?";

    const greetingMsg = {
      type: 'bot',
      content: greeting,
      timestamp: new Date().toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' }),
    };
    setMessages([greetingMsg]);

    // Load voices and speak
    const loadVoices = () =>
      new Promise((resolve) => {
        const voices = synthRef.current.getVoices();
        if (voices.length > 0) {
          resolve(voices);
        } else {
          synthRef.current.onvoiceschanged = () => resolve(synthRef.current.getVoices());
        }
      });

    loadVoices().then(() => speakText(greeting));
  };

  // Reset consultation
  const resetConsultation = async () => {
    if (!window.confirm('Voulez-vous recommencer la consultation ?')) return;

    synthRef.current.cancel();
    if (audioRef.current) audioRef.current.pause();
    clearSilenceTimer();

    try {
      await fetch(`${MEDIBOT_API}/session/${sessionId}/clear`, { method: 'POST' });
    } catch (e) {}

    setConversationStarted(false);
    setMessages([]);
    setPotentialDiseases([]);
    setConsultationTime(0);
    setSymptomsCount(0);
    setVoiceModeEnabled(false);
    setIsSpeaking(false);
    setLoading(false);
    setInput('');
    blinkCountRef.current = 0;
    yawnCountRef.current = 0;
    setFatigueLevel('none');
    setFatigueMetrics({ ear: 1, blinkCount: 0, yawnCount: 0 });
  };

  // Save transcript
  const saveTranscript = () => {
    let content = 'CONSULTATION MEDICALE VOCALE - Dr. MediBot\n';
    content += `Date: ${new Date().toLocaleString('fr-FR')}\n`;
    content += `Durée: ${formatTime(consultationTime)}\n`;
    content += `Échanges: ${messages.length}\n\n`;
    content += '==================================================\n\n';

    messages.forEach((msg) => {
      const sender = msg.type === 'bot' ? 'Dr. MediBot' : 'Vous';
      content += `[${sender}] ${msg.content}\n\n`;
    });

    if (potentialDiseases.length > 0) {
      content += '\n==================================================\n';
      content += 'DIAGNOSTICS POSSIBLES:\n';
      potentialDiseases.forEach((d) => {
        content += `- ${d.name} (${d.confidence}%)\n`;
      });
    }

    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `consultation_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get fatigue color
  const getFatigueColor = () => {
    switch (fatigueLevel) {
      case 'high':
        return 'text-red-500';
      case 'medium':
        return 'text-yellow-500';
      case 'low':
        return 'text-green-500';
      default:
        return 'text-blue-500';
    }
  };

  const getFatigueBg = () => {
    switch (fatigueLevel) {
      case 'high':
        return 'bg-red-500/20 border-red-500';
      case 'medium':
        return 'bg-yellow-500/20 border-yellow-500';
      case 'low':
        return 'bg-green-500/20 border-green-500';
      default:
        return 'bg-blue-500/20 border-blue-500';
    }
  };


  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] bg-background">
      {/* Emergency Modal */}
      {showEmergency && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <Card className="max-w-md p-6 bg-red-50 border-red-500 border-2">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="h-8 w-8 text-red-600" />
              <h2 className="text-xl font-bold text-red-700">⚠️ URGENCE DÉTECTÉE</h2>
            </div>
            <p className="text-red-700 mb-4">
              Vos symptômes nécessitent une attention médicale immédiate.
            </p>
            <div className="space-y-2 mb-4">
              <a href="tel:190" className="block p-3 bg-red-600 text-white rounded-lg text-center font-bold hover:bg-red-700">
                🚑 SAMU : 190
              </a>
              <a href="tel:197" className="block p-3 bg-orange-600 text-white rounded-lg text-center font-bold hover:bg-orange-700">
                🚒 Pompiers : 197
              </a>
              <a href="tel:112" className="block p-3 bg-blue-600 text-white rounded-lg text-center font-bold hover:bg-blue-700">
                📞 Urgences EU : 112
              </a>
            </div>
            <Button onClick={() => setShowEmergency(false)} variant="outline" className="w-full">
              Fermer
            </Button>
          </Card>
        </div>
      )}

      {/* Welcome Screen */}
      {!conversationStarted ? (
        <div className="flex-1 flex items-center justify-center p-6">
          <Card className="max-w-2xl w-full p-8 text-center">
            <div className="w-20 h-20 mx-auto mb-6 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center">
              <Stethoscope className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-2xl font-bold mb-2">Bienvenue sur Dr. MediBot</h2>
            <p className="text-muted-foreground mb-6">
              Une consultation médicale entièrement vocale avec intelligence artificielle
            </p>

            <div className="grid grid-cols-3 gap-4 mb-6">
              <div className="p-4 rounded-lg bg-muted/50">
                <Mic className="w-8 h-8 mx-auto mb-2 text-primary" />
                <p className="text-sm font-medium">Consultation 100% vocale</p>
              </div>
              <div className="p-4 rounded-lg bg-muted/50">
                <Brain className="w-8 h-8 mx-auto mb-2 text-primary" />
                <p className="text-sm font-medium">IA médicale avancée</p>
              </div>
              <div className="p-4 rounded-lg bg-muted/50">
                <Eye className="w-8 h-8 mx-auto mb-2 text-primary" />
                <p className="text-sm font-medium">Détection de fatigue</p>
              </div>
            </div>

            <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30 mb-6 text-left">
              <div className="flex items-start gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-yellow-700">
                  <strong>Important :</strong> Ce système ne remplace pas une consultation médicale réelle.
                  En cas de symptômes graves, appelez immédiatement le 190 (SAMU).
                </p>
              </div>
            </div>

            <Button onClick={startConsultation} size="lg" className="w-full btn-glow">
              <Mic className="w-5 h-5 mr-2" />
              Démarrer la Consultation Vocale
            </Button>
          </Card>
        </div>
      ) : (
        <>
          {/* Main Content */}
          <div className="flex-1 flex flex-col gap-4 p-4 overflow-hidden">
            {/* Video Container - Full width, side by side */}
            <div className="grid grid-cols-2 gap-4 h-[200px] flex-shrink-0">
              {/* Patient Video */}
              <div className="relative bg-muted rounded-xl overflow-hidden border">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  playsInline
                  className="w-full h-full object-cover"
                />
                {!cameraEnabled && (
                  <div className="absolute inset-0 flex flex-col items-center justify-center bg-muted">
                    <VideoOff className="w-12 h-12 text-muted-foreground mb-2" />
                    <p className="text-sm text-muted-foreground">Caméra désactivée</p>
                  </div>
                )}
                <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-white">
                  Vous
                </div>
                {/* Voice Activity Indicator */}
                {isListening && (
                  <div className="absolute top-2 right-2 flex items-center gap-1 px-2 py-1 bg-green-500 rounded-full">
                    <div className="flex gap-0.5">
                      {[...Array(5)].map((_, i) => (
                        <div
                          key={i}
                          className="w-1 bg-white rounded-full animate-pulse"
                          style={{
                            height: `${8 + Math.random() * 8}px`,
                            animationDelay: `${i * 100}ms`,
                          }}
                        />
                      ))}
                    </div>
                  </div>
                )}
                {/* Fatigue Detection Overlay */}
                {cameraEnabled && (
                  <div className={`absolute top-2 left-2 p-2 rounded-lg text-xs ${getFatigueBg()} border backdrop-blur-sm`}>
                    <div className={`font-semibold ${getFatigueColor()}`}>
                      Fatigue: {fatigueLevel}
                    </div>
                    <div className="text-muted-foreground mt-1 space-y-0.5">
                      <div>EAR: {fatigueMetrics.ear.toFixed(2)}</div>
                      <div>Clignements: {fatigueMetrics.blinkCount}</div>
                      <div>Bâillements: {fatigueMetrics.yawnCount}</div>
                    </div>
                    {fatigueLevel === 'high' && (
                      <div className="mt-2 p-1 bg-red-500/30 rounded text-red-200 text-[10px]">
                        ⚠️ Fatigue élevée!
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Bot Avatar */}
              <div className="relative bg-gradient-to-br from-green-900 to-emerald-800 rounded-xl overflow-hidden border flex items-center justify-center">
                <div
                  className={`w-24 h-24 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center shadow-xl ${
                    isSpeaking ? 'animate-pulse' : ''
                  }`}
                >
                  <Activity className="w-12 h-12 text-white" />
                </div>
                <div className="absolute bottom-2 left-2 px-2 py-1 bg-black/60 rounded text-xs text-white">
                  Dr. MediBot
                </div>
                <div
                  className={`absolute top-2 right-2 flex items-center gap-1.5 px-2 py-1 rounded-full text-xs text-white ${
                    isSpeaking ? 'bg-purple-500' : loading ? 'bg-yellow-500' : 'bg-green-500'
                  }`}
                >
                  <span className="w-2 h-2 rounded-full bg-white animate-pulse" />
                  {isSpeaking ? 'Parle...' : loading ? 'Réfléchit...' : 'En ligne'}
                </div>
                {/* Bot Voice Activity */}
                {isSpeaking && (
                  <div className="absolute bottom-12 flex gap-0.5">
                    {[...Array(5)].map((_, i) => (
                      <div
                        key={i}
                        className="w-1 bg-white rounded-full animate-pulse"
                        style={{
                          height: `${12 + Math.random() * 12}px`,
                          animationDelay: `${i * 100}ms`,
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Video Controls */}
              <div className="flex items-center justify-center gap-2">
                <Button
                  variant={cameraEnabled ? 'default' : 'outline'}
                  size="icon"
                  onClick={toggleCamera}
                  title={cameraEnabled ? 'Désactiver caméra' : 'Activer caméra'}
                >
                  {cameraEnabled ? <Video size={18} /> : <VideoOff size={18} />}
                </Button>
                <Button
                  variant={voiceModeEnabled ? 'default' : 'outline'}
                  onClick={toggleVoiceMode}
                  className={voiceModeEnabled ? 'bg-green-600 hover:bg-green-700' : ''}
                >
                  {voiceModeEnabled ? <Mic size={18} /> : <MicOff size={18} />}
                  <span className="ml-2">VOCAL</span>
                </Button>
                <Button
                  variant={voiceEnabled ? 'default' : 'outline'}
                  size="icon"
                  onClick={() => setVoiceEnabled(!voiceEnabled)}
                  title={voiceEnabled ? 'Désactiver son' : 'Activer son'}
                >
                  {voiceEnabled ? <Volume2 size={18} /> : <VolumeX size={18} />}
                </Button>
              </div>

              {/* Voice Status */}
              <div
                className={`p-4 rounded-xl text-white ${
                  isListening
                    ? 'bg-gradient-to-r from-green-600 to-emerald-600'
                    : isSpeaking
                    ? 'bg-gradient-to-r from-purple-600 to-violet-600'
                    : loading
                    ? 'bg-gradient-to-r from-yellow-600 to-orange-600'
                    : 'bg-gradient-to-r from-blue-600 to-indigo-600'
                }`}
              >
                <div className="flex items-center gap-3">
                  {isListening ? (
                    <Mic className="w-6 h-6" />
                  ) : isSpeaking ? (
                    <Volume2 className="w-6 h-6" />
                  ) : (
                    <MessageSquare className="w-6 h-6" />
                  )}
                  <div>
                    <h3 className="font-semibold">
                      {isListening
                        ? '🎤 Écoute active'
                        : isSpeaking
                        ? '🔊 Dr. MediBot parle'
                        : loading
                        ? '⏳ Analyse...'
                        : 'Mode Vocal'}
                    </h3>
                    <p className="text-sm opacity-90">
                      {isListening
                        ? 'Parlez maintenant...'
                        : isSpeaking
                        ? 'Écoutez la réponse...'
                        : loading
                        ? 'Traitement en cours...'
                        : voiceModeEnabled
                        ? 'Prêt à écouter'
                        : 'Cliquez sur VOCAL pour activer'}
                    </p>
                  </div>
                </div>
                {voiceModeEnabled && input && (
                  <div className="mt-3 p-2 bg-white/20 rounded-lg">
                    <p className="text-sm">{input || 'En attente...'}</p>
                  </div>
                )}
              </div>

            {/* Consultation Panel - Bottom section */}
            <div className="flex-1 flex flex-col gap-3 overflow-hidden min-h-[300px]">
              {/* Panel Header */}
              <div className="flex items-center justify-between flex-shrink-0">
                <h2 className="font-semibold">Consultation</h2>
                <div className="flex gap-2">
                  <Button variant="ghost" size="icon" onClick={resetConsultation} title="Nouvelle consultation">
                    <RotateCcw size={18} />
                  </Button>
                  <Button variant="ghost" size="icon" onClick={saveTranscript} title="Sauvegarder">
                    <Download size={18} />
                  </Button>
                </div>
              </div>

              {/* Messages */}
              <div className="flex-1 overflow-y-auto space-y-3 pr-2 min-h-[200px]">
                {messages.map((message, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg ${
                      message.type === 'user' ? 'bg-primary/10 ml-8' : 'bg-muted mr-8'
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      {message.type === 'bot' ? (
                        <div className="w-6 h-6 rounded-full bg-green-600 flex items-center justify-center flex-shrink-0">
                          <Activity size={12} className="text-white" />
                        </div>
                      ) : (
                        <div className="w-6 h-6 rounded-full bg-blue-600 flex items-center justify-center flex-shrink-0">
                          <svg className="w-3 h-3 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                            <circle cx="12" cy="7" r="4" />
                          </svg>
                        </div>
                      )}
                      <div className="flex-1">
                        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
                        <span className="text-xs text-muted-foreground">{message.timestamp}</span>
                      </div>
                    </div>
                  </div>
                ))}
                {loading && (
                  <div className="p-3 rounded-lg bg-muted mr-8">
                    <div className="flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-green-600 flex items-center justify-center">
                        <Activity size={12} className="text-white animate-pulse" />
                      </div>
                      <div className="flex gap-1">
                        <div className="w-2 h-2 rounded-full bg-green-600 animate-bounce" />
                        <div className="w-2 h-2 rounded-full bg-green-600 animate-bounce" style={{ animationDelay: '150ms' }} />
                        <div className="w-2 h-2 rounded-full bg-green-600 animate-bounce" style={{ animationDelay: '300ms' }} />
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Potential Diseases */}
              {potentialDiseases.length > 0 && (
                <div className="p-3 rounded-lg bg-muted/50 border">
                  <p className="text-xs text-muted-foreground mb-2">Diagnostics possibles :</p>
                  <div className="flex flex-wrap gap-2">
                    {potentialDiseases.map((disease, i) => (
                      <span
                        key={i}
                        className="text-xs px-2 py-1 bg-primary/10 text-primary rounded-full"
                        title={`Symptômes: ${disease.symptoms?.join(', ')}`}
                      >
                        {disease.name} ({disease.confidence}%)
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Stats */}
              <div className="grid grid-cols-3 gap-2">
                <div className="p-3 rounded-lg bg-muted/50 text-center">
                  <MessageSquare className="w-5 h-5 mx-auto mb-1 text-primary" />
                  <p className="text-lg font-bold">{messages.length}</p>
                  <p className="text-xs text-muted-foreground">Échanges</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 text-center">
                  <Clock className="w-5 h-5 mx-auto mb-1 text-primary" />
                  <p className="text-lg font-bold">{formatTime(consultationTime)}</p>
                  <p className="text-xs text-muted-foreground">Durée</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 text-center">
                  <Heart className="w-5 h-5 mx-auto mb-1 text-primary" />
                  <p className="text-lg font-bold">{symptomsCount}</p>
                  <p className="text-xs text-muted-foreground">Symptômes</p>
                </div>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default MediBot;
