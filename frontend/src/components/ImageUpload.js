import React, { useState, useRef } from 'react';
import { Upload, Camera, X, Pill, Sparkles, Loader2, Eye } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';

const ImageUpload = ({ setResult, setLoading }) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [stream, setStream] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analyzeProgress, setAnalyzeProgress] = useState(0);
  const [analyzeStage, setAnalyzeStage] = useState('');
  const fileInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  const handleImageSelect = (file) => {
    if (file && file.type.startsWith('image/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setSelectedImage({
          file: file,
          preview: e.target.result
        });
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

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          facingMode: 'environment',
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        } 
      });
      setStream(mediaStream);
      setCameraActive(true);
      
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      }, 100);
    } catch (error) {
      console.error('Error accessing camera:', error);
      alert('Unable to access camera. Please check permissions or use file upload instead.');
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setCameraActive(false);
  };

  const capturePhoto = () => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    canvas.toBlob((blob) => {
      const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
      handleImageSelect(file);
      stopCamera();
    }, 'image/jpeg', 0.95);
  };

  const removeImage = () => {
    setSelectedImage(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const identifyMedication = async () => {
    if (!selectedImage) return;

    setLoading(true);
    setIsAnalyzing(true);
    setResult(null);

    // Simulate progress
    const stages = [
      { progress: 20, stage: '📷 Processing image...' },
      { progress: 40, stage: '🔍 Detecting medication...' },
      { progress: 60, stage: '💊 Analyzing packaging...' },
      { progress: 80, stage: '📚 Searching database...' },
      { progress: 95, stage: '✨ Finalizing...' },
    ];
    
    let currentStage = 0;
    const progressInterval = setInterval(() => {
      if (currentStage < stages.length) {
        setAnalyzeProgress(stages[currentStage].progress);
        setAnalyzeStage(stages[currentStage].stage);
        currentStage++;
      }
    }, 600);

    const formData = new FormData();
    formData.append('file', selectedImage.file);

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);

      const response = await fetch('http://localhost:8000/agent/identify', {
        method: 'POST',
        body: formData,
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      clearInterval(progressInterval);
      setAnalyzeProgress(100);
      setAnalyzeStage('✅ Complete!');
      
      await new Promise(r => setTimeout(r, 500));
      
      const data = await response.json();
      setResult(data);
    } catch (error) {
      clearInterval(progressInterval);
      if (error.name === 'AbortError') {
        setResult({
          success: false,
          answer: 'Request timed out. The image may be too complex. Please try again or use the Search feature.',
          error: 'Timeout'
        });
      } else {
        setResult({
          success: false,
          answer: 'Error connecting to server. Please ensure the backend is running.',
          error: error.message
        });
      }
    } finally {
      setLoading(false);
      setIsAnalyzing(false);
      setAnalyzeProgress(0);
      setAnalyzeStage('');
    }
  };

  return (
    <Card className="card-glow overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-violet-600 to-purple-600 p-4">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-white/20 rounded-lg backdrop-blur">
            <Pill className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-white">Medication Identifier</h2>
            <p className="text-violet-100 text-sm">AI-powered image recognition</p>
          </div>
        </div>
      </div>

      <CardContent className="p-6">
        {cameraActive ? (
          <div className="space-y-4">
            <div className="relative rounded-xl overflow-hidden bg-black">
              <video
                ref={videoRef}
                autoPlay
                playsInline
                className="w-full h-auto"
              />
              <canvas ref={canvasRef} className="hidden" />
            </div>
            <div className="flex gap-2">
              <Button 
                className="flex-1 bg-gradient-to-r from-violet-600 to-purple-600"
                onClick={capturePhoto}
              >
                <Camera className="h-4 w-4 mr-2" />
                Capture Photo
              </Button>
              <Button 
                variant="outline"
                onClick={stopCamera}
              >
                <X className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            </div>
          </div>
        ) : !selectedImage ? (
          <div className="space-y-4">
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
                  <Sparkles className={`absolute -top-1 -right-1 w-5 h-5 text-violet-500 ${dragOver ? 'animate-spin' : 'animate-pulse'}`} />
                </div>
              </div>
              
              <p className="text-lg font-semibold mb-2">Drop medication image here</p>
              <p className="text-sm text-muted-foreground mb-4">
                or click to browse • PNG, JPG, WEBP supported
              </p>
              
              <div className="flex items-center justify-center gap-4 text-xs text-muted-foreground">
                <span className="flex items-center gap-1">
                  <Eye className="w-3 h-3" /> AI Vision
                </span>
                <span className="flex items-center gap-1">
                  <Pill className="w-3 h-3" /> Drug Detection
                </span>
              </div>
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInput}
              accept="image/*"
              className="hidden"
            />

            {/* Camera Button */}
            <Button 
              variant="outline"
              className="w-full"
              onClick={startCamera}
            >
              <Camera className="h-4 w-4 mr-2" />
              Take Photo with Camera
            </Button>

            {/* Tips */}
            <div className="grid grid-cols-3 gap-3">
              {[
                { icon: '📦', title: 'Box/Bottle', desc: 'Show the label' },
                { icon: '💊', title: 'Pills', desc: 'Clear close-up' },
                { icon: '💡', title: 'Good Light', desc: 'Avoid shadows' }
              ].map((tip, i) => (
                <div key={i} className="flex flex-col items-center gap-1 p-3 bg-muted/50 rounded-lg text-center">
                  <span className="text-xl">{tip.icon}</span>
                  <p className="text-xs font-medium">{tip.title}</p>
                  <p className="text-xs text-muted-foreground">{tip.desc}</p>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Image Preview */}
            <div className="relative rounded-xl overflow-hidden border-2 border-primary/30 shadow-lg">
              <img 
                src={selectedImage.preview} 
                alt="Selected medication" 
                className={`w-full max-h-80 object-contain bg-gray-50 transition-all duration-300 ${isAnalyzing ? 'opacity-80' : ''}`}
              />
              
              {/* Analyzing Overlay */}
              {isAnalyzing && (
                <div className="absolute inset-0 bg-gradient-to-b from-transparent via-violet-500/10 to-violet-500/20 flex flex-col items-center justify-center">
                  <div className="absolute inset-0 overflow-hidden">
                    <div className="absolute inset-x-0 h-1 bg-gradient-to-r from-transparent via-violet-500 to-transparent" 
                         style={{ top: `${analyzeProgress}%`, transition: 'top 0.5s ease-out' }} />
                  </div>
                  <div className="bg-white/95 backdrop-blur px-6 py-4 rounded-xl shadow-xl">
                    <div className="flex items-center gap-3">
                      <Loader2 className="w-6 h-6 text-violet-600 animate-spin" />
                      <div>
                        <p className="font-semibold text-violet-900">{analyzeStage}</p>
                        <div className="w-48 h-2 bg-gray-200 rounded-full mt-2 overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-violet-500 to-purple-600 rounded-full transition-all duration-500"
                            style={{ width: `${analyzeProgress}%` }}
                          />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
              
              {!isAnalyzing && (
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

            {/* Action Buttons */}
            <div className="flex gap-3">
              <Button 
                className="flex-1 h-12 text-base bg-gradient-to-r from-violet-600 to-purple-600 hover:from-violet-700 hover:to-purple-700 btn-glow"
                onClick={identifyMedication}
                disabled={isAnalyzing}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Pill className="w-5 h-5 mr-2" />
                    Identify Medication
                  </>
                )}
              </Button>
              <Button 
                variant="outline"
                onClick={removeImage}
                disabled={isAnalyzing}
                className="h-12"
              >
                <X className="w-4 h-4 mr-2" />
                Clear
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default ImageUpload;
