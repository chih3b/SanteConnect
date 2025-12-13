import React, { useState, useRef } from 'react';
import { Upload, Image as ImageIcon, Camera, X } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

const ImageUpload = ({ setResult, setLoading }) => {
  const [selectedImage, setSelectedImage] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [cameraActive, setCameraActive] = useState(false);
  const [stream, setStream] = useState(null);
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
          facingMode: 'environment', // Use back camera on mobile
          width: { ideal: 1920 },
          height: { ideal: 1080 }
        } 
      });
      setStream(mediaStream);
      setCameraActive(true);
      
      // Wait for video element to be ready
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
    
    // Set canvas size to match video
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    // Draw video frame to canvas
    const context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob and create file
    canvas.toBlob((blob) => {
      const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' });
      handleImageSelect(file);
      stopCamera();
    }, 'image/jpeg', 0.95);
  };

  const identifyMedication = async () => {
    if (!selectedImage) return;

    setLoading(true);
    setResult(null);

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
      const data = await response.json();
      setResult(data);
    } catch (error) {
      if (error.name === 'AbortError') {
        setResult({
          success: false,
          answer: 'Request timed out. The image may be too complex or the AI model is busy. Please try again or use the Search feature.',
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
    }
  };

  return (
    <Card className="card-glow">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <ImageIcon className="h-5 w-5 text-blue-600" />
          Upload Medication Image
        </CardTitle>
        <CardDescription>
          Take a clear photo of your medication box, bottle, or pill
        </CardDescription>
      </CardHeader>
      <CardContent>
        {cameraActive ? (
          <div className="space-y-4">
            <div className="relative rounded-lg overflow-hidden bg-black">
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
                className="flex-1"
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
        ) : (
          <>
            <div
              className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
                dragOver 
                  ? 'border-primary bg-primary/5' 
                  : 'border-border hover:border-primary/50 bg-muted/30'
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
            >
              {selectedImage?.preview ? (
                <div>
                  <img 
                    src={selectedImage.preview} 
                    alt="Selected medication" 
                    className="max-w-full max-h-96 mx-auto rounded-lg border"
                  />
                  <p className="text-sm text-muted-foreground mt-4">
                    Click to change image or drag a new one
                  </p>
                </div>
              ) : (
                <div>
                  <Upload className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-base font-medium mb-2">
                    Drop image here or click to select
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Supports JPG, PNG, WEBP
                  </p>
                </div>
              )}
            </div>

            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileInput}
              accept="image/*"
              className="hidden"
            />

            <div className="flex gap-2 mt-4">
              <Button 
                variant="outline"
                className="flex-1"
                onClick={startCamera}
              >
                <Camera className="h-4 w-4 mr-2" />
                Take Photo
              </Button>
            </div>

            {selectedImage && (
              <Button 
                className="w-full mt-2 btn-glow"
                onClick={identifyMedication}
              >
                <ImageIcon className="h-4 w-4 mr-2" />
                Identify Medication
              </Button>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
};

export default ImageUpload;
