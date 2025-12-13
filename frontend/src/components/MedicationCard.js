import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Heart, Info, Wrench, Brain, AlertCircle, Database, Globe } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';

const MedicationCard = ({ result }) => {
  if (!result) return null;

  const getConfidenceBadge = (confidence) => {
    const configs = {
      high: { icon: CheckCircle2, text: 'High Confidence', className: 'bg-green-50 text-green-700 border-green-200' },
      medium: { icon: AlertTriangle, text: 'Medium Confidence', className: 'bg-yellow-50 text-yellow-700 border-yellow-200' },
      low: { icon: XCircle, text: 'Low Confidence', className: 'bg-red-50 text-red-700 border-red-200' }
    };
    
    const config = configs[confidence] || configs.low;
    const Icon = config.icon;
    
    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium border ${config.className}`}>
        <Icon className="h-3.5 w-3.5" />
        {config.text}
      </span>
    );
  };

  const formatAnswer = (answer) => {
    if (!answer) return 'No information available';
    return answer
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br/>')
      .replace(/• /g, '• ');
  };

  const getDataSources = (toolCalls) => {
    if (!toolCalls || toolCalls.length === 0) return null;
    
    const localTools = ['get_drug_details', 'search_medication', 'check_pregnancy_safety', 
                        'compare_medications', 'find_alternatives', 'check_drug_interactions',
                        'search_by_symptom', 'identify_medication'];
    const mcpTools = ['check_fda_drug_info', 'search_medical_literature', 'check_drug_recalls'];
    
    const hasLocal = toolCalls.some(tc => localTools.some(lt => tc.tool.includes(lt)));
    const hasMCP = toolCalls.some(tc => mcpTools.some(mt => tc.tool.includes(mt)));
    
    return { hasLocal, hasMCP };
  };

  if (!result.success && result.error) {
    return (
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-destructive">
            <XCircle className="h-5 w-5" />
            Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-destructive flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-medium text-sm mb-1">Something went wrong</h3>
                <p className="text-sm text-muted-foreground">{result.answer || result.error}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="mt-6 card-glow">
      <CardHeader>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <CardTitle className="flex items-center gap-2">
            <Heart className="h-5 w-5 text-blue-600" />
            Medication Information
          </CardTitle>
          {result.confidence && getConfidenceBadge(result.confidence)}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Similar Medications Warning */}
        {result.similar_medications && result.similar_medications.length > 1 && (
          <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
            <div className="flex items-start gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-sm text-orange-900 mb-2">Multiple Medications Found</h3>
                <p className="text-sm text-orange-800 mb-3">{result.note}</p>
                <div className="space-y-2">
                  {result.similar_medications.map((med, index) => (
                    <div key={index} className="bg-white rounded-md p-2 border border-orange-200">
                      <div className="flex items-center justify-between">
                        <span className="font-medium text-sm">{med.name}</span>
                        <span className="text-xs text-muted-foreground">{med.dosage}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* AI Response */}
        <div className="bg-muted/50 rounded-lg p-4 border">
          <div className="flex items-center gap-2 mb-3">
            <Info className="h-4 w-4 text-primary" />
            <h3 className="font-semibold text-sm">AI Response</h3>
          </div>
          <div 
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ 
              __html: formatAnswer(result.answer) 
            }}
          />
        </div>

        {/* Data Sources */}
        {result.tool_calls && result.tool_calls.length > 0 && (() => {
          const sources = getDataSources(result.tool_calls);
          return sources && (sources.hasLocal || sources.hasMCP) && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Info className="h-4 w-4 text-blue-600" />
                <h3 className="font-semibold text-sm text-blue-900">Data Sources</h3>
              </div>
              <div className="flex flex-wrap gap-3">
                {sources.hasLocal && (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-md border border-blue-200">
                    <Database className="h-4 w-4 text-blue-600" />
                    <span className="text-xs font-medium text-blue-900">Tunisian Database</span>
                  </div>
                )}
                {sources.hasMCP && (
                  <div className="flex items-center gap-2 px-3 py-1.5 bg-white rounded-md border border-green-200">
                    <Globe className="h-4 w-4 text-green-600" />
                    <span className="text-xs font-medium text-green-900">International Data (FDA/PubMed)</span>
                  </div>
                )}
              </div>
            </div>
          );
        })()}

        {/* Tools Used */}
        {result.tool_calls && result.tool_calls.length > 0 && (
          <div className="bg-muted/50 rounded-lg p-4 border">
            <div className="flex items-center gap-2 mb-3">
              <Wrench className="h-4 w-4 text-primary" />
              <h3 className="font-semibold text-sm">Tools Used</h3>
            </div>
            <div className="flex flex-wrap gap-2">
              {result.tool_calls.map((tool, index) => {
                const isMCP = ['check_fda_drug_info', 'search_medical_literature', 'check_drug_recalls']
                  .some(mt => tool.tool.includes(mt));
                return (
                  <span 
                    key={index}
                    className={`inline-flex items-center px-2.5 py-1 rounded-md text-xs font-medium ${
                      isMCP 
                        ? 'bg-green-100 text-green-700 border border-green-200' 
                        : 'bg-primary/10 text-primary'
                    }`}
                  >
                    {isMCP && <Globe className="h-3 w-3 mr-1" />}
                    {!isMCP && <Database className="h-3 w-3 mr-1" />}
                    {tool.tool.replace('_tool', '').replace('_', ' ')}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* Reasoning */}
        {result.reasoning && (
          <div className="bg-muted/50 rounded-lg p-4 border">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="h-4 w-4 text-primary" />
              <h3 className="font-semibold text-sm">Reasoning</h3>
            </div>
            <p className="text-sm text-muted-foreground">{result.reasoning}</p>
          </div>
        )}

        {/* Disclaimer */}
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="h-5 w-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-semibold text-sm text-yellow-900 mb-1">Important Disclaimer</h3>
              <p className="text-sm text-yellow-800">
                This information is for educational purposes only and should not replace 
                professional medical advice. Always consult with a healthcare provider 
                before making any decisions about medications.
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default MedicationCard;
