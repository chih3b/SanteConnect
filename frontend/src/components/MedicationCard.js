import { useState } from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Heart, ChevronDown, ChevronUp, Copy, Check, Pill, Brain, Zap } from 'lucide-react';
import { Card, CardContent } from './ui/card';
import { Button } from './ui/button';

const MedicationCard = ({ result }) => {
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  if (!result) return null;

  const getConfidenceBadge = (confidence) => {
    const configs = {
      high: { icon: CheckCircle2, text: 'High Confidence', bg: 'bg-green-500', light: 'bg-green-50 text-green-700 border-green-200' },
      medium: { icon: AlertTriangle, text: 'Medium Confidence', bg: 'bg-yellow-500', light: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
      low: { icon: XCircle, text: 'Low Confidence', bg: 'bg-red-500', light: 'bg-red-50 text-red-700 border-red-200' }
    };
    
    const config = configs[confidence] || configs.low;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold border ${config.light}`}>
        <Icon className="h-3.5 w-3.5" />
        {config.text}
      </span>
    );
  };

  const formatAnswer = (answer) => {
    if (!answer) return 'No information available';
    return answer
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-foreground">$1</strong>')
      .replace(/\n\n/g, '</p><p class="mt-3">')
      .replace(/\n/g, '<br/>')
      .replace(/• /g, '<span class="text-primary">•</span> ');
  };

  const copyAnswer = () => {
    navigator.clipboard.writeText(result.answer || '');
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  // Error state
  if (!result.success && result.error) {
    return (
      <Card className="mt-6 border-red-200 bg-gradient-to-br from-red-50 to-orange-50">
        <CardContent className="pt-6">
          <div className="flex items-start gap-4">
            <div className="p-3 bg-red-100 rounded-xl">
              <XCircle className="w-6 h-6 text-red-600" />
            </div>
            <div>
              <h3 className="font-semibold text-red-900 text-lg">Something went wrong</h3>
              <p className="text-sm text-red-700 mt-1">{result.answer || result.error}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-6 card-glow overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-card/20 rounded-lg backdrop-blur">
              <Heart className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Medication Information</h2>
              <p className="text-blue-100 text-sm">AI-powered analysis</p>
            </div>
          </div>
          {result.confidence && getConfidenceBadge(result.confidence)}
        </div>
      </div>

      <CardContent className="p-6 space-y-4">
        {/* Similar Medications Warning */}
        {result.similar_medications && result.similar_medications.length > 1 && (
          <div className="bg-gradient-to-r from-orange-50 to-amber-50 border border-orange-200 rounded-xl p-4">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <AlertTriangle className="w-5 h-5 text-orange-600" />
              </div>
              <div className="flex-1">
                <h3 className="font-semibold text-orange-900">Multiple Medications Found</h3>
                <p className="text-sm text-orange-700 mt-1">{result.note}</p>
                <div className="flex flex-wrap gap-2 mt-3">
                  {result.similar_medications.map((med, index) => (
                    <span key={index} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-card rounded-lg border border-orange-200 text-sm">
                      <Pill className="w-3.5 h-3.5 text-orange-600" />
                      {med.name}
                      {med.dosage && <span className="text-muted-foreground">({med.dosage})</span>}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Answer */}
        <div className="bg-muted/30 rounded-xl p-5 border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Pill className="w-4 h-4 text-primary" />
              Information
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={copyAnswer}
              className="text-xs"
            >
              {copied ? (
                <>
                  <Check className="w-3.5 h-3.5 mr-1 text-green-600" />
                  Copied!
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5 mr-1" />
                  Copy
                </>
              )}
            </Button>
          </div>
          <div 
            className="prose prose-sm max-w-none text-muted-foreground leading-relaxed"
            dangerouslySetInnerHTML={{ __html: `<p>${formatAnswer(result.answer)}</p>` }}
          />
        </div>

        {/* XAI Explainability Section */}
        {(result.tool_calls?.length > 0 || result.reasoning || result.xai) && (
          <div className="border rounded-xl overflow-hidden">
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="w-full flex items-center justify-between p-4 bg-muted/30 hover:bg-muted/50 transition-colors"
            >
              <span className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                <Brain className="w-4 h-4" />
                {showDetails ? 'Hide' : 'Show'} AI reasoning
              </span>
              {showDetails ? (
                <ChevronUp className="w-4 h-4 text-muted-foreground" />
              ) : (
                <ChevronDown className="w-4 h-4 text-muted-foreground" />
              )}
            </button>
            
            {showDetails && (
              <div className="p-4 space-y-4 border-t bg-muted/10">
                {/* XAI Reasoning Chain */}
                {result.xai?.reasoning_steps && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
                      <Brain className="w-3 h-3" /> Reasoning Chain
                    </p>
                    <div className="space-y-2">
                      {result.xai.reasoning_steps.map((step, index) => (
                        <div key={index} className="flex items-start gap-2 p-2 bg-background rounded-lg">
                          <span className="w-5 h-5 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold flex-shrink-0">
                            {step.step}
                          </span>
                          <div className="flex-1 min-w-0">
                            <div className="font-medium text-xs">{step.action}</div>
                            <div className="text-xs text-muted-foreground">{step.reasoning}</div>
                          </div>
                          <span className={`px-1.5 py-0.5 rounded text-xs flex-shrink-0 ${
                            step.confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                            step.confidence >= 0.5 ? 'bg-yellow-100 text-yellow-700' :
                            'bg-red-100 text-red-700'
                          }`}>
                            {Math.round(step.confidence * 100)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Tools Used */}
                {result.tool_calls && result.tool_calls.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1">
                      <Zap className="w-3 h-3" /> Tools Used
                    </p>
                    <div className="flex flex-wrap gap-1.5">
                      {result.tool_calls.map((tool, index) => (
                        <span 
                          key={index}
                          className="px-2 py-1 bg-purple-100 text-purple-800 rounded text-xs"
                        >
                          {tool.tool.replace(/_/g, ' ')}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Summary */}
                {result.xai?.summary && (
                  <div className="p-2 bg-blue-50 rounded-lg text-xs text-blue-800">
                    <span className="font-medium">Summary:</span> {result.xai.summary}
                  </div>
                )}
                
                {/* Reasoning (fallback) */}
                {!result.xai && result.reasoning && (
                  <div>
                    <p className="text-xs font-medium text-muted-foreground mb-2">AI reasoning:</p>
                    <p className="text-sm text-muted-foreground">{result.reasoning}</p>
                  </div>
                )}
                
                {/* Duration */}
                {result.xai?.duration_ms && (
                  <div className="text-xs text-muted-foreground pt-2 border-t">
                    ⏱️ Response time: {Math.round(result.xai.duration_ms)}ms
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Disclaimer */}
        <div className="bg-gradient-to-r from-amber-50 to-yellow-50 border border-amber-200 rounded-xl p-4">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-amber-900 text-sm">Medical Disclaimer</h3>
              <p className="text-sm text-amber-700 mt-1">
                This information is for educational purposes only. Always consult a healthcare professional before making medication decisions.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MedicationCard;
