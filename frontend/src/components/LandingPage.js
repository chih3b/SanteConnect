import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import ThemeToggle from "./ThemeToggle";
import {
  Stethoscope,
  Users,
  Calendar,
  ChevronRight,
  ChevronLeft,
  Star,
  ArrowRight,
  Sparkles,
  Brain,
  Mail,
  FileText,
  Mic,
  Search,
  Pill,
  Bot,
  Scan,
  Shield,
  Heart,
  Clock,
  MessageCircle,
  Menu,
  X,
} from "lucide-react";

// Custom hook for scroll animations
function useScrollAnimation() {
  const [visibleSections, setVisibleSections] = useState(new Set());
  
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setVisibleSections((prev) => new Set([...prev, entry.target.id]));
          }
        });
      },
      { threshold: 0.1, rootMargin: "0px 0px -50px 0px" }
    );

    const sections = document.querySelectorAll("[data-animate]");
    sections.forEach((section) => observer.observe(section));

    return () => observer.disconnect();
  }, []);

  return visibleSections;
}

// Hero slider
const heroSlides = [
  {
    image: "https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=1920&q=80",
    title: "Your Health, Simplified",
    subtitle: "Get instant medical guidance, identify medications, and connect with healthcare professionals",
  },
  {
    image: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1920&q=80",
    title: "Smart Medical Assistants",
    subtitle: "Chat with AI doctors who understand your symptoms and guide you to better health",
  },
  {
    image: "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=1920&q=80",
    title: "For Doctors & Patients",
    subtitle: "A complete platform for managing appointments, consultations, and patient care",
  },
];

// Patient Features
const patientFeatures = [
  {
    icon: MessageCircle,
    title: "Talk to Dr. MediBot",
    description: "Describe your symptoms and get helpful medical guidance in a friendly conversation",
  },
  {
    icon: Brain,
    title: "Smart Diagnosis Help",
    description: "Our AI analyzes your symptoms and suggests possible conditions to discuss with your doctor",
  },
  {
    icon: Pill,
    title: "Identify Medications",
    description: "Take a photo of any medication to learn what it is and how to use it safely",
  },
  {
    icon: Scan,
    title: "Scan Prescriptions",
    description: "Upload your prescription and we'll extract all the important details for you",
  },
  {
    icon: Search,
    title: "Find Medications",
    description: "Search our database to find information about any Tunisian medication",
  },
  {
    icon: Mic,
    title: "Voice Consultations",
    description: "Speak naturally with our assistant - no typing needed",
  },
];

// Doctor Features
const doctorFeatures = [
  {
    icon: Bot,
    title: "AI Assistant",
    description: "Your smart helper that understands medical context and assists with daily tasks",
  },
  {
    icon: FileText,
    title: "Document Analysis",
    description: "AI-powered OCR, risk assessment, rehospitalization scoring, and automatic SMS alerts",
  },
  {
    icon: Calendar,
    title: "Appointment Management",
    description: "View, add, and manage your schedule seamlessly with Google Calendar integration",
  },
  {
    icon: Mail,
    title: "Patient Communication",
    description: "Send emails to patients directly from your dashboard via Gmail",
  },
];

// Stats
const stats = [
  { value: "24/7", label: "Always Available" },
  { value: "Instant", label: "Responses" },
  { value: "Secure", label: "& Private" },
  { value: "Free", label: "To Start" },
];

// Testimonials
const testimonials = [
  {
    name: "Sarah Johnson",
    role: "Patient",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&q=80",
    text: "I was worried about my symptoms at 2 AM. The chatbot helped me understand what was happening and when to seek help.",
    rating: 5,
  },
  {
    name: "Dr. Michael Chen",
    role: "Cardiologist",
    image: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150&q=80",
    text: "Managing my appointments and patient communications has never been easier. This saves me hours every week!",
    rating: 5,
  },
  {
    name: "Emily Rodriguez",
    role: "Patient",
    image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&q=80",
    text: "I found a pill in my cabinet and didn't know what it was. Just took a photo and got all the information instantly!",
    rating: 5,
  },
];

export default function LandingPage({ onSelectRole }) {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const visibleSections = useScrollAnimation();

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
  const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + heroSlides.length) % heroSlides.length);

  const closeMobileMenu = () => setMobileMenuOpen(false);

  return (
    <div className="min-h-screen bg-background">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-background/95 backdrop-blur-md border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <img src="/logo.png" alt="SanteConnect" className="w-10 h-10 object-contain" />
              <span className="text-xl font-bold text-foreground">SanteConnect</span>
            </div>

            {/* Desktop Nav */}
            <div className="hidden md:flex items-center gap-8">
              <a href="#patient-features" className="text-muted-foreground hover:text-primary transition-colors font-medium">For Patients</a>
              <a href="#doctor-features" className="text-muted-foreground hover:text-primary transition-colors font-medium">For Doctors</a>
              <a href="#testimonials" className="text-muted-foreground hover:text-primary transition-colors font-medium">Reviews</a>
            </div>

            {/* Desktop Buttons */}
            <div className="hidden md:flex items-center gap-3">
              <ThemeToggle />
              <Button variant="ghost" onClick={() => onSelectRole("patient")} className="text-foreground hover:text-primary">
                Patient Login
              </Button>
              <Button onClick={() => onSelectRole("doctor")} className="btn-glow bg-primary text-white hover:bg-primary/90">
                <Stethoscope className="w-4 h-4 mr-2" />
                Doctor Portal
              </Button>
            </div>

            {/* Mobile Menu Button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 hover:bg-muted rounded-lg transition-colors"
            >
              {mobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
            </button>
          </div>
        </div>

        {/* Mobile Menu */}
        <div className={`md:hidden overflow-hidden transition-all duration-300 ${mobileMenuOpen ? "max-h-96" : "max-h-0"}`}>
          <div className="px-4 py-4 bg-background border-t border-border space-y-3">
            <a 
              href="#patient-features" 
              onClick={closeMobileMenu}
              className="block py-2 px-3 rounded-lg text-foreground hover:bg-muted transition-colors font-medium"
            >
              For Patients
            </a>
            <a 
              href="#doctor-features" 
              onClick={closeMobileMenu}
              className="block py-2 px-3 rounded-lg text-foreground hover:bg-muted transition-colors font-medium"
            >
              For Doctors
            </a>
            <a 
              href="#testimonials" 
              onClick={closeMobileMenu}
              className="block py-2 px-3 rounded-lg text-foreground hover:bg-muted transition-colors font-medium"
            >
              Reviews
            </a>
            <div className="pt-3 border-t border-border space-y-2">
              <div className="flex items-center justify-between px-3 py-2">
                <span className="text-sm text-muted-foreground">Theme</span>
                <ThemeToggle />
              </div>
              <Button 
                variant="outline" 
                onClick={() => { onSelectRole("patient"); closeMobileMenu(); }} 
                className="w-full justify-center"
              >
                <Users className="w-4 h-4 mr-2" />
                Patient Login
              </Button>
              <Button 
                onClick={() => { onSelectRole("doctor"); closeMobileMenu(); }} 
                className="w-full justify-center btn-glow"
              >
                <Stethoscope className="w-4 h-4 mr-2" />
                Doctor Portal
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative h-screen overflow-hidden pt-16">
        {heroSlides.map((slide, index) => (
          <div key={index} className={`absolute inset-0 transition-opacity duration-1000 ${index === currentSlide ? "opacity-100" : "opacity-0 pointer-events-none"}`}>
            <div className="absolute inset-0">
              <img src={slide.image} alt={slide.title} className="w-full h-full object-cover" />
              <div className="absolute inset-0 bg-gradient-to-r from-primary/90 to-primary/70" />
            </div>
            <div className="relative h-full flex items-center">
              <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
                <div className="max-w-2xl">
                  <h1 className={`text-4xl sm:text-5xl lg:text-6xl font-bold text-white mb-6 transition-all duration-700 ${index === currentSlide ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"}`}>
                    {slide.title}
                  </h1>
                  <p className={`text-xl text-white/90 mb-8 transition-all duration-700 delay-200 ${index === currentSlide ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"}`}>
                    {slide.subtitle}
                  </p>
                  <div className={`flex flex-wrap gap-4 transition-all duration-700 delay-300 ${index === currentSlide ? "translate-y-0 opacity-100" : "translate-y-10 opacity-0"}`}>
                    <Button size="lg" onClick={() => onSelectRole("patient")} className="bg-white text-primary hover:bg-white/90 px-8 py-6 text-lg font-semibold">
                      Get Started Free
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                    <Button size="lg" onClick={() => onSelectRole("doctor")} className="bg-transparent border-2 border-white text-white hover:bg-white/20 px-8 py-6 text-lg font-semibold">
                      <Stethoscope className="w-5 h-5 mr-2" />
                      I'm a Doctor
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Slider Controls */}
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 flex items-center gap-4">
          <button onClick={prevSlide} className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white hover:bg-white/30 transition-colors">
            <ChevronLeft className="w-6 h-6" />
          </button>
          <div className="flex gap-2">
            {heroSlides.map((_, index) => (
              <button key={index} onClick={() => setCurrentSlide(index)} className={`h-2 rounded-full transition-all ${index === currentSlide ? "w-8 bg-white" : "w-2 bg-white/50"}`} />
            ))}
          </div>
          <button onClick={nextSlide} className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white hover:bg-white/30 transition-colors">
            <ChevronRight className="w-6 h-6" />
          </button>
        </div>
      </section>

      {/* Stats */}
      <section id="stats-section" data-animate className="py-16 bg-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div 
                key={index} 
                className={`text-center transition-all duration-700 ${
                  visibleSections.has("stats-section") 
                    ? "opacity-100 translate-y-0" 
                    : "opacity-0 translate-y-8"
                }`}
                style={{ transitionDelay: `${index * 100}ms` }}
              >
                <div className="text-4xl sm:text-5xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-white/80">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Patient Features */}
      <section id="patient-features" data-animate className="py-24 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`text-center mb-16 transition-all duration-700 ${
            visibleSections.has("patient-features") ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            <span className="text-primary font-semibold text-sm uppercase tracking-wider">For Patients</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mt-2 mb-4">
              Healthcare Help When You Need It
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Get answers to your health questions, identify medications, and take control of your wellbeing
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            {patientFeatures.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div 
                  key={index} 
                  className={`bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-500 hover:-translate-y-2 group border border-border ${
                    visibleSections.has("patient-features") ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
                  }`}
                  style={{ transitionDelay: `${index * 100}ms` }}
                >
                  <div className="w-14 h-14 bg-primary rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Icon className="w-7 h-7 text-primary-foreground" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              );
            })}
          </div>

          <div className={`text-center mt-12 transition-all duration-700 delay-500 ${
            visibleSections.has("patient-features") ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            <Button size="lg" onClick={() => onSelectRole("patient")} className="btn-glow">
              <Heart className="w-5 h-5 mr-2" />
              Start Your Health Journey
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </div>
        </div>
      </section>

      {/* Doctor Features */}
      <section id="doctor-features" data-animate className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className={`transition-all duration-700 ${
              visibleSections.has("doctor-features") ? "opacity-100 translate-x-0" : "opacity-0 -translate-x-12"
            }`}>
              <span className="text-primary font-semibold text-sm uppercase tracking-wider">For Doctors</span>
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mt-2 mb-6">
                Your Smart Practice Assistant
              </h2>
              <p className="text-lg text-muted-foreground mb-8">
                Streamline your daily workflow with an intelligent assistant that helps you manage appointments, 
                communicate with patients, and handle documents - all in one place.
              </p>

              <div className="grid sm:grid-cols-2 gap-6 mb-8">
                {doctorFeatures.map((feature, index) => {
                  const Icon = feature.icon;
                  return (
                    <div 
                      key={index} 
                      className={`flex gap-4 transition-all duration-500 ${
                        visibleSections.has("doctor-features") ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
                      }`}
                      style={{ transitionDelay: `${200 + index * 100}ms` }}
                    >
                      <div className="w-12 h-12 bg-primary/10 rounded-xl flex items-center justify-center flex-shrink-0">
                        <Icon className="w-6 h-6 text-primary" />
                      </div>
                      <div>
                        <h4 className="font-semibold text-foreground mb-1">{feature.title}</h4>
                        <p className="text-sm text-muted-foreground">{feature.description}</p>
                      </div>
                    </div>
                  );
                })}
              </div>

              <Button size="lg" onClick={() => onSelectRole("doctor")} className="btn-glow">
                <Stethoscope className="w-5 h-5 mr-2" />
                Access Doctor Portal
              </Button>
            </div>

            <div className={`relative transition-all duration-700 delay-300 ${
              visibleSections.has("doctor-features") ? "opacity-100 translate-x-0" : "opacity-0 translate-x-12"
            }`}>
              <div className="bg-gradient-to-br from-primary/5 to-primary/10 rounded-2xl p-8 border border-border">
                <div className="bg-card rounded-xl shadow-lg p-6 mb-4">
                  <div className="flex items-center gap-3 mb-4">
                    <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-blue-600 rounded-full flex items-center justify-center">
                      <Bot className="w-5 h-5 text-white" />
                    </div>
                    <div>
                      <div className="font-semibold">AI Assistant</div>
                      <div className="text-xs text-green-600 flex items-center gap-1">
                        <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                        Ready to help
                      </div>
                    </div>
                  </div>
                  <div className="space-y-3">
                    <div className="bg-muted rounded-lg p-3 text-sm">
                      "What appointments do I have today?"
                    </div>
                    <div className="bg-primary/10 rounded-lg p-3 text-sm">
                      📅 You have 3 appointments: 9:00 AM - Ahmed, 11:00 AM - Fatima, 2:30 PM - Mohamed
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <div className="flex-1 bg-card rounded-lg p-3 text-center border border-border">
                    <Calendar className="w-5 h-5 mx-auto mb-1 text-primary" />
                    <div className="text-xs text-muted-foreground">Calendar</div>
                  </div>
                  <div className="flex-1 bg-card rounded-lg p-3 text-center border border-border">
                    <Mail className="w-5 h-5 mx-auto mb-1 text-primary" />
                    <div className="text-xs text-muted-foreground">Email</div>
                  </div>
                  <div className="flex-1 bg-card rounded-lg p-3 text-center border border-border">
                    <FileText className="w-5 h-5 mx-auto mb-1 text-primary" />
                    <div className="text-xs text-muted-foreground">Documents</div>
                  </div>
                  <div className="flex-1 bg-card rounded-lg p-3 text-center border border-border">
                    <Clock className="w-5 h-5 mx-auto mb-1 text-primary" />
                    <div className="text-xs text-muted-foreground">History</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Why Choose Us */}
      <section id="why-section" data-animate className="py-24 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`text-center mb-16 transition-all duration-700 ${
            visibleSections.has("why-section") ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            <span className="text-primary font-semibold text-sm uppercase tracking-wider">Why SanteConnect</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mt-2 mb-4">
              Healthcare Made Simple
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: Clock, title: "Available Anytime", desc: "Get health guidance 24/7, whether it's 3 PM or 3 AM" },
              { icon: Shield, title: "Private & Secure", desc: "Your health information stays confidential and protected" },
              { icon: Heart, title: "Built with Care", desc: "Designed by healthcare professionals for real needs" },
            ].map((item, index) => {
              const Icon = item.icon;
              return (
                <div 
                  key={index}
                  className={`text-center p-8 transition-all duration-500 ${
                    visibleSections.has("why-section") ? "opacity-100 translate-y-0 scale-100" : "opacity-0 translate-y-8 scale-95"
                  }`}
                  style={{ transitionDelay: `${index * 150}ms` }}
                >
                  <div className="w-16 h-16 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-6">
                    <Icon className="w-8 h-8 text-primary" />
                  </div>
                  <h3 className="text-xl font-semibold mb-3">{item.title}</h3>
                  <p className="text-muted-foreground">{item.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section id="testimonials" data-animate className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className={`text-center mb-16 transition-all duration-700 ${
            visibleSections.has("testimonials") ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}>
            <span className="text-primary font-semibold text-sm uppercase tracking-wider">Reviews</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mt-2 mb-4">
              What People Are Saying
            </h2>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div 
                key={index} 
                className={`bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-500 border border-border ${
                  visibleSections.has("testimonials") ? "opacity-100 translate-y-0" : "opacity-0 translate-y-12"
                }`}
                style={{ transitionDelay: `${index * 150}ms` }}
              >
                <div className="flex gap-1 mb-4">
                  {[...Array(testimonial.rating)].map((_, i) => (
                    <Star key={i} className="w-5 h-5 text-yellow-400 fill-yellow-400" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-6 italic">"{testimonial.text}"</p>
                <div className="flex items-center gap-4">
                  <img src={testimonial.image} alt={testimonial.name} className="w-12 h-12 rounded-full object-cover" />
                  <div>
                    <div className="font-semibold text-foreground">{testimonial.name}</div>
                    <div className="text-sm text-muted-foreground">{testimonial.role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-24 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl translate-x-1/2 translate-y-1/2" />
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <Sparkles className="w-12 h-12 text-white/80 mx-auto mb-6" />
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Take Control of Your Health?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Join thousands of people who trust SanteConnect for their healthcare needs
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button size="lg" onClick={() => onSelectRole("patient")} className="bg-white text-primary hover:bg-white/90 px-8 py-6 text-lg font-semibold">
              <Users className="w-5 h-5 mr-2" />
              Get Started Free
            </Button>
            <Button size="lg" onClick={() => onSelectRole("doctor")} className="bg-transparent border-2 border-white text-white hover:bg-white/20 px-8 py-6 text-lg font-semibold">
              <Stethoscope className="w-5 h-5 mr-2" />
              Doctor Portal
            </Button>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-foreground text-background py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-4 gap-12">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <img src="/logo.png" alt="SanteConnect" className="w-10 h-10 object-contain brightness-0 invert" />
                <span className="text-xl font-bold">SanteConnect</span>
              </div>
              <p className="text-background/70">
                Making healthcare accessible, simple, and smart for everyone.
              </p>
            </div>

            <div>
              <h4 className="font-semibold mb-4">For Patients</h4>
              <ul className="space-y-2 text-background/70">
                <li>Medical Chatbot</li>
                <li>Symptom Checker</li>
                <li>Medication Identifier</li>
                <li>Prescription Scanner</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-4">For Doctors</h4>
              <ul className="space-y-2 text-background/70">
                <li>AI Assistant</li>
                <li>Document Analysis</li>
                <li>Risk Assessment Dashboard</li>
                <li>SMS Notifications</li>
                <li>Calendar Integration</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-4">Contact</h4>
              <ul className="space-y-2 text-background/70">
                <li>support@santeconnect.com</li>
                <li>+216 XX XXX XXX</li>
                <li>Tunis, Tunisia</li>
              </ul>
            </div>
          </div>

          <div className="border-t border-background/20 mt-12 pt-8 text-center text-background/70">
            <p>&copy; {new Date().getFullYear()} SanteConnect. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
