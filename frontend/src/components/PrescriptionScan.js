import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, X, Pill, AlertTriangle, Shield, CheckCircle2, Database, Globe, Brain, Scan, Sparkles, Camera, Loader2, Eye, Copy, RefreshCw } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

const PrescriptionScan = ({ setResult, setLoading }) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [filterPhi, setFilterPhi] = useState(true);
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanStage, setScanStage] = useState('');
  const [showCopied, setShowCopied] = useState(false);
  const fileInputRef = useRef(null);

  // Simulate scan progress animation
  useEffect(() => {
    if (isScanning) {
      const stages = [
        { progress: 15, stage: '📷 Reading image...' },
        { progress: 30, stage: '🔍 Analyzing prescription...' },
        { progress: 50, stage: '📝 Extracting text with OCR...' },
        { progress: 70, stage: '💊 Identifying medications...' },
        { progress: 85, stage: '🔎 Searching drug databases...' },
        { progress: 95, stage: '✨ Finalizing results...' },
      ];
      
      let currentStage = 0;
      const interval = setInterval(() => {
        if (currentStage < stages.length) {
          setScanProgress(stages[currentStage].progress);
          setScanStage(stages[currentStage].stage);
          currentStage++;
        }
      }, 800);
      
      return () => clearInterval(interval);
    } else {
      setScanProgress(0);
      setScanStage('');
    }
  }, [isScanning]);

  const handleImageSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage({
          file: file,
          preview: e.target.result
        });
        setScanResult(null);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    handleImageSelect(file);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleFileInput = (e) => {
    const file = e.target.files[0];
    handleImageSelect(file);
  };

  const removeImage = () => {
    setSelectedImage(null);
    setScanResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleSubmit = async () => {
    if (!selectedImage) return;

    setLoading(true);
    setIsScanning(true);
    setScanResult(null);
    
    const formData = new FormData();
    formData.append('file', selectedImage.file);

    try {
      const response = await fetch(`http://localhost:8000/prescription/scan?filter_phi=${filterPhi}`, {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const result = await response.json();
        setScanProgress(100);
        setScanStage('✅ Complete!');
        await new Promise(r => setTimeout(r, 500));
        setScanResult(result);
        setResult(result);
      } else {
        const error = await response.json();
        setScanResult({ 
          success: false, 
          error: error.detail || 'Failed to process prescription' 
        });
      }
    } catch (error) {
      console.error('Error:', error);
      setScanResult({ 
        success: false, 
        error: 'Network error occurred. Please ensure the server is running.' 
      });
    } finally {
      setLoading(false);
      setIsScanning(false);
    }
  };

  const copyText = (text) => {
    navigator.clipboard.writeText(text);
    setShowCopied(true);
    setTimeout(() => setShowCopied(false), 2000);
  };

  const formatText = (text) => {
    if (!text) return '<span class="text-muted-foreground italic">No text extracted</span>';
    return text
      .replace(/\[([A-Z_]+)_REDACTED\]/g, '<span class="inline-flex items-center gap-1 bg-yellow-200 text-yellow-800 px-1.5 py-0.5 rounded text-xs font-mono animate-pulse">🔒 $1</span>')
      .replace(/\n/g, '<br/>');
  };

  return (
    <div className="space-y-6">
      {/* Upload Card */}
      <Card className="card-glow overflow-hidden">
        <div className="bg-gradient-to-r from-blue-600 to-indigo-600 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-white/20 rounded-lg backdrop-blur">
              <Scan className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">AI Prescription Scanner</h2>
              <p className="text-blue-100 text-sm">Powered by Azure Vision & Medical AI</p>
            </div>
          </div>
        </div>
        
        <CardContent className="p-6 space-y-4">
          {!selectedImage ? (
            <>
              {/* Upload Area */}
              <div
                className={`relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-300 cursor-pointer group ${
                  dragOver 
                    ? 'border-primary bg-primary/10 scale-[1.02]' 
                    : 'border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/30'
                }`}
                onDrop={handleDrop}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onClick={() => fileInputRef.current?.click()}
              >
                <div className={`transition-transform duration-300 ${dragOver ? 'scale-110' : 'group-hover:scale-105'}`}>
                  <div className="relative inline-block">
                    <Upload className={`w-16 h-16 mx-auto mb-4 transition-colors duration-300 ${dragOver ? 'text-primary' : 'text-muted-foreground'}`} />
                    <Sparkles className={`absolute -top-1 -right-1 w-5 h-5 text-yellow-500 ${dragOver ? 'animate-spin' : 'animate-pulse'}`} />
                  </div>
                </div>
                
                <p className="text-lg font-semibold mb-2">Drop your prescription here</p>
                <p className="text-sm text-muted-foreground mb-4">
                  or click to browse • PNG, JPG, JPEG supported
                </p>
                
                <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1">
                    <Eye className="w-3 h-3" /> OCR Extraction
                  </span>
                  <span className="flex items-center gap-1">
                    <Pill className="w-3 h-3" /> Drug Detection
                  </span>
                  <span className="flex items-center gap-1">
                    <Shield className="w-3 h-3" /> HIPAA Safe
                  </span>
                </div>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  capture="environment"
                  onChange={handleFileInput}
                  className="hidden"
                />
              </div>

              {/* Quick tips */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {[
                  { icon: '📸', title: 'Clear Image', desc: 'Use good lighting' },
                  { icon: '📄', title: 'Full View', desc: 'Capture entire prescription' },
                  { icon: '✨', title: 'High Quality', desc: 'Avoid blurry photos' }
                ].map((tip, i) => (
                  <div key={i} className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg text-sm">
                    <span className="text-xl">{tip.icon}</span>
                    <div>
                      <p className="font-medium">{tip.title}</p>
                      <p className="text-xs text-muted-foreground">{tip.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <>
              {/* Image Preview with Overlay */}
              <div className="relative rounded-xl overflow-hidden border-2 border-primary/30 shadow-lg">
                <img
                  src={selectedImage.preview}
                  alt="Selected prescription"
                  className={`w-full max-h-80 object-contain bg-gray-50 transition-all duration-300 ${isScanning ? 'opacity-80' : ''}`}
                />
                
                {/* Scanning Overlay */}
                {isScanning && (
                  <div className="absolute inset-0 bg-gradient-to-b from-transparent via-blue-500/10 to-blue-500/20 flex flex-col items-center justify-center">
                    <div className="absolute inset-0 overflow-hidden">
                      <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-blue-500 to-transparent animate-scan" 
                           style={{ top: `${scanProgress}%`, transition: 'top 0.5s ease-out' }} />
                    </div>
                    <div className="bg-white/95 backdrop-blur px-6 py-4 rounded-xl shadow-xl">
                      <div className="flex items-center gap-3">
                        <Loader2 className="w-6 h-6 text-blue-600 animate-spin" />
                        <div>
                          <p className="font-semibold text-blue-900">{scanStage}</p>
                          <div className="w-48 h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-blue-500 to-indigo-600 rounded-full transition-all duration-500"
                              style={{ width: `${scanProgress}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                {!isScanning && (
                  <Button
                    onClick={removeImage}
                    size="sm"
                    variant="destructive"
                    className="absolute top-3 right-3 shadow-lg"
                  >
                    <X className="w-4 h-4" />
                  </Button>
                )}
              </div>

              {/* PHI Filter Toggle */}
              <div className={`flex items-center gap-3 p-4 rounded-xl border-2 transition-colors ${filterPhi ? 'bg-green-50 border-green-200' : 'bg-muted/50 border-transparent'}`}>
                <Shield className={`w-6 h-6 transition-colors ${filterPhi ? 'text-green-600' : 'text-muted-foreground'}`} />
                <label className="flex items-center gap-3 cursor-pointer flex-1">
                  <div className="relative">
                    <input
                      type="checkbox"
                      checked={filterPhi}
                      onChange={(e) => setFilterPhi(e.target.checked)}
                      className="sr-only"
                    />
                    <div className={`w-12 h-6 rounded-full transition-colors ${filterPhi ? 'bg-green-500' : 'bg-gray-300'}`}>
                      <div className={`w-5 h-5 bg-white rounded-full shadow-md transform transition-transform ${filterPhi ? 'translate-x-6' : 'translate-x-0.5'} mt-0.5`} />
                    </div>
                  </div>
                  <div>
                    <span className="font-medium">HIPAA Privacy Protection</span>
                    <p className="text-xs text-muted-foreground">
                      {filterPhi ? '✓ Names, addresses & IDs will be hidden' : 'Patient data will be visible'}
                    </p>
                  </div>
                </label>
              </div>

              {/* Action Buttons */}
              <div className="flex gap-3">
                <Button 
                  onClick={handleSubmit} 
                  disabled={isScanning}
                  className="flex-1 h-12 text-base bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 btn-glow"
                >
                  {isScanning ? (
                    <>
                      <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <Scan className="w-5 h-5 mr-2" />
                      Analyze Prescription
                    </>
                  )}
                </Button>
                <Button 
                  onClick={removeImage} 
                  variant="outline"
                  disabled={isScanning}
                  className="h-12"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  New
                </Button>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Results */}
      {scanResult && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
          {/* Error State */}
          {!scanResult.success && scanResult.error && (
            <Card className="border-red-200 bg-red-50 animate-shake">
              <CardContent className="pt-6">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  </div>
                  <div>
                    <p className="font-semibold text-red-900">Analysis Failed</p>
                    <p className="text-sm text-red-700 mt-1">{scanResult.error}</p>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="mt-3 text-red-700 border-red-300 hover:bg-red-100"
                      onClick={handleSubmit}
                    >
                      <RefreshCw className="w-4 h-4 mr-2" /> Try Again
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Success State */}
          {scanResult.success && (
            <>
              {/* Success Banner */}
              <div className="bg-gradient-to-r from-green-500 to-emerald-600 text-white p-4 rounded-xl flex items-center gap-3">
                <div className="p-2 bg-white/20 rounded-lg">
                  <CheckCircle2 className="w-6 h-6" />
                </div>
                <div className="flex-1">
                  <p className="font-semibold">Analysis Complete!</p>
                  <p className="text-green-100 text-sm">
                    Found {scanResult.total_medications || 0} medication(s) • 
                    {scanResult.phi_detected ? ' PHI Protected' : ' No PHI detected'}
                  </p>
                </div>
                {scanResult.tools_used?.length > 0 && (
                  <div className="hidden sm:flex items-center gap-1 text-xs bg-white/20 px-2 py-1 rounded-full">
                    <Sparkles className="w-3 h-3" />
                    {scanResult.tools_used.length} AI tools used
                  </div>
                )}
              </div>

              {/* Extracted Text */}
              <Card className="overflow-hidden">
                <CardHeader className="bg-muted/50 border-b">
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <FileText className="w-4 h-4 text-blue-600" />
                      Extracted Text
                      {scanResult.phi_detected && (
                        <span className="ml-2 px-2 py-0.5 bg-yellow-100 text-yellow-800 text-xs rounded-full animate-pulse">
                          🔒 PHI Redacted
                        </span>
                      )}
                    </CardTitle>
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => copyText(scanResult.redacted_text || scanResult.extracted_text)}
                      className="text-xs"
                    >
                      {showCopied ? <CheckCircle2 className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
                      {showCopied ? 'Copied!' : 'Copy'}
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="p-0">
                  <div 
                    className="text-sm p-4 font-mono whitespace-pre-wrap max-h-60 overflow-y-auto bg-gray-50 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: formatText(scanResult.redacted_text || scanResult.extracted_text) }}
                  />
                </CardContent>
              </Card>

              {/* Medications Found */}
              {scanResult.medications && scanResult.medications.length > 0 && (
                <Card className="card-glow overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <div className="p-1.5 bg-blue-100 rounded-lg">
                        <Pill className="w-4 h-4 text-blue-600" />
                      </div>
                      Medications Detected
                      <span className="ml-auto px-2.5 py-1 bg-blue-600 text-white text-xs rounded-full font-bold">
                        {scanResult.total_medications}
                      </span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 space-y-2">
                    {scanResult.medications.map((med, index) => (
                      <div 
                        key={index} 
                        className="flex items-center gap-3 p-4 bg-gradient-to-r from-blue-50 to-transparent rounded-xl border border-blue-100 hover:border-blue-300 transition-all hover:shadow-md group"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center group-hover:scale-110 transition-transform">
                          <span className="text-lg">💊</span>
                        </div>
                        <div className="flex-1">
                          <p className="font-semibold capitalize text-blue-900">{med.name}</p>
                          {med.dosage && (
                            <p className="text-sm text-blue-600">{med.dosage}</p>
                          )}
                        </div>
                        <CheckCircle2 className="w-5 h-5 text-green-500" />
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* Drug Alternatives */}
              {scanResult.drug_alternatives && scanResult.drug_alternatives.length > 0 && (
                <Card className="overflow-hidden">
                  <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 border-b">
                    <CardTitle className="flex items-center gap-2 text-base">
                      <div className="p-1.5 bg-green-100 rounded-lg">
                        <Database className="w-4 h-4 text-green-600" />
                      </div>
                      Drug Information & Alternatives
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="p-4 space-y-4">
                    {scanResult.drug_alternatives.map((drugInfo, index) => (
                      <div key={index} className="border rounded-xl overflow-hidden hover:shadow-lg transition-shadow">
                        {/* Drug Header */}
                        <div className="bg-gradient-to-r from-indigo-500 to-purple-600 text-white p-4">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-white/20 rounded-lg">
                              <Pill className="w-5 h-5" />
                            </div>
                            <div>
                              <p className="font-semibold capitalize text-lg">{drugInfo.original_drug?.name || 'Unknown'}</p>
                              {drugInfo.original_drug?.dosage && (
                                <p className="text-indigo-100 text-sm">{drugInfo.original_drug.dosage}</p>
                              )}
                            </div>
                          </div>
                        </div>
                        
                        <div className="p-4 space-y-4">
                          {/* Source indicators */}
                          {drugInfo.drug_info?.sources_found && (
                            <div className="flex flex-wrap gap-2">
                              {drugInfo.drug_info.sources_found.map((source, i) => (
                                <span key={i} className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-muted rounded-full text-xs font-medium">
                                  {source.includes('FDA') && <Globe className="w-3.5 h-3.5 text-green-600" />}
                                  {source.includes('RxNorm') && <Database className="w-3.5 h-3.5 text-blue-600" />}
                                  {source.includes('LLaMA') && <Brain className="w-3.5 h-3.5 text-purple-600" />}
                                  {source.includes('Essential') && <Database className="w-3.5 h-3.5 text-orange-600" />}
                                  {source}
                                </span>
                              ))}
                            </div>
                          )}

                          {/* LLM Response */}
                          {drugInfo.drug_info?.text_from_llm && (
                            <div className="bg-gradient-to-r from-purple-50 to-pink-50 border border-purple-200 rounded-xl p-4">
                              <div className="flex items-center gap-2 mb-3">
                                <div className="p-1.5 bg-purple-100 rounded-lg">
                                  <Brain className="w-4 h-4 text-purple-600" />
                                </div>
                                <span className="text-sm font-semibold text-purple-800">AI-Generated Information</span>
                                <Sparkles className="w-4 h-4 text-purple-400 animate-pulse" />
                              </div>
                              <p className="text-sm text-purple-900 whitespace-pre-wrap leading-relaxed">{drugInfo.drug_info.text_from_llm}</p>
                            </div>
                          )}
                          
                          {/* Alternatives list */}
                          {drugInfo.drug_info?.alternatives && drugInfo.drug_info.alternatives.length > 0 && (
                            <div>
                              <p className="text-sm font-semibold text-muted-foreground mb-3 flex items-center gap-2">
                                <RefreshCw className="w-4 h-4" />
                                Alternative Medications
                              </p>
                              <div className="grid gap-2">
                                {drugInfo.drug_info.alternatives.slice(0, 5).map((alt, altIndex) => (
                                  <div 
                                    key={altIndex} 
                                    className="flex items-start gap-3 p-3 bg-muted/50 rounded-lg hover:bg-muted transition-colors"
                                  >
                                    <span className="w-6 h-6 rounded-full bg-primary/10 text-primary flex items-center justify-center text-xs font-bold">
                                      {altIndex + 1}
                                    </span>
                                    <div className="flex-1 min-w-0">
                                      <p className="font-medium capitalize">{alt.generic_name}</p>
                                      {alt.brand_names && alt.brand_names.length > 0 && (
                                        <p className="text-xs text-muted-foreground">
                                          🏷️ {alt.brand_names.slice(0, 3).join(', ')}
                                        </p>
                                      )}
                                      {alt.indication && (
                                        <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{alt.indication}</p>
                                      )}
                                    </div>
                                    {alt.similarity && (
                                      <span className="px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full font-semibold">
                                        {Math.round(alt.similarity * 100)}%
                                      </span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              )}

              {/* No Medications Found */}
              {(!scanResult.medications || scanResult.medications.length === 0) && (
                <Card className="border-yellow-200 bg-gradient-to-r from-yellow-50 to-orange-50">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-4">
                      <div className="p-3 bg-yellow-100 rounded-xl">
                        <AlertTriangle className="w-6 h-6 text-yellow-600" />
                      </div>
                      <div>
                        <p className="font-semibold text-yellow-900 text-lg">No Medications Detected</p>
                        <p className="text-sm text-yellow-800 mt-1">
                          The prescription image may be unclear or doesn't contain recognized medication names.
                        </p>
                        <div className="mt-4 flex flex-wrap gap-2">
                          <Button variant="outline" size="sm" onClick={removeImage} className="border-yellow-300 text-yellow-800 hover:bg-yellow-100">
                            <Camera className="w-4 h-4 mr-2" /> Try Different Image
                          </Button>
                          <Button variant="outline" size="sm" onClick={handleSubmit} className="border-yellow-300 text-yellow-800 hover:bg-yellow-100">
                            <RefreshCw className="w-4 h-4 mr-2" /> Retry Analysis
                          </Button>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Disclaimer */}
              <Card className="border-orange-200 bg-gradient-to-r from-orange-50 to-amber-50">
                <CardContent className="py-4">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="w-5 h-5 text-orange-600 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="font-semibold text-orange-900 text-sm">⚠️ Medical Disclaimer</p>
                      <p className="text-sm text-orange-800 mt-1">
                        This information is for reference only. Always consult with a healthcare professional
                        before making any changes to your medication. Drug alternatives should only be
                        substituted under medical supervision.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </>
          )}
        </div>
      )}
      
      {/* Custom CSS for animations */}
      <style>{`
        @keyframes scan {
          0% { opacity: 0; }
          50% { opacity: 1; }
          100% { opacity: 0; }
        }
        .animate-scan {
          animation: scan 2s ease-in-out infinite;
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-5px); }
          75% { transform: translateX(5px); }
        }
        .animate-shake {
          animation: shake 0.5s ease-in-out;
        }
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(10px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-in {
          animation: fade-in 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default PrescriptionScan;