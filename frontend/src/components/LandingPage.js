import { useState, useEffect } from "react";
import { Button } from "./ui/button";
import {
  Stethoscope,
  Users,
  Calendar,
  Shield,
  ChevronRight,
  ChevronLeft,
  Star,
  Activity,
  MessageCircle,
  CheckCircle,
  ArrowRight,
  Sparkles,
} from "lucide-react";

// Hero slider images from Unsplash (medical themed)
const heroSlides = [
  {
    image: "https://images.unsplash.com/photo-1631217868264-e5b90bb7e133?w=1920&q=80",
    title: "Healthcare Reimagined",
    subtitle: "Experience the future of medical care with AI-powered diagnostics and personalized treatment plans",
  },
  {
    image: "https://images.unsplash.com/photo-1576091160399-112ba8d25d1d?w=1920&q=80",
    title: "Expert Doctors, Anytime",
    subtitle: "Connect with certified healthcare professionals from the comfort of your home",
  },
  {
    image: "https://images.unsplash.com/photo-1579684385127-1ef15d508118?w=1920&q=80",
    title: "Your Health, Our Priority",
    subtitle: "Advanced medical technology combined with compassionate care for better outcomes",
  },
];

// Features data
const features = [
  {
    icon: Activity,
    title: "AI Diagnostics",
    description: "Advanced AI analyzes symptoms and provides accurate preliminary assessments",
  },
  {
    icon: Calendar,
    title: "Easy Scheduling",
    description: "Book appointments instantly with real-time availability",
  },
  {
    icon: MessageCircle,
    title: "24/7 Support",
    description: "Get medical guidance anytime with our intelligent chatbot",
  },
  {
    icon: Shield,
    title: "Secure & Private",
    description: "Your health data is encrypted and protected at all times",
  },
];

// Stats data
const stats = [
  { value: "50K+", label: "Patients Served" },
  { value: "200+", label: "Expert Doctors" },
  { value: "98%", label: "Satisfaction Rate" },
  { value: "24/7", label: "Available Support" },
];

// Testimonials
const testimonials = [
  {
    name: "Sarah Johnson",
    role: "Patient",
    image: "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=150&q=80",
    text: "SanteConnect made managing my health so much easier. The AI assistant is incredibly helpful!",
    rating: 5,
  },
  {
    name: "Dr. Michael Chen",
    role: "Cardiologist",
    image: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=150&q=80",
    text: "As a doctor, this platform helps me provide better care with its intelligent tools.",
    rating: 5,
  },
  {
    name: "Emily Rodriguez",
    role: "Patient",
    image: "https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=150&q=80",
    text: "The video consultations are so convenient. I can see my doctor without leaving home!",
    rating: 5,
  },
];

export default function LandingPage({ onSelectRole }) {
  const [currentSlide, setCurrentSlide] = useState(0);

  // Auto-advance slider
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
    }, 6000);
    return () => clearInterval(timer);
  }, []);

  const nextSlide = () => setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
  const prevSlide = () => setCurrentSlide((prev) => (prev - 1 + heroSlides.length) % heroSlides.length);

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

            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-muted-foreground hover:text-primary transition-colors font-medium">Features</a>
              <a href="#about" className="text-muted-foreground hover:text-primary transition-colors font-medium">About</a>
              <a href="#testimonials" className="text-muted-foreground hover:text-primary transition-colors font-medium">Testimonials</a>
            </div>

            <div className="flex items-center gap-3">
              <Button variant="ghost" onClick={() => onSelectRole("patient")} className="hidden sm:flex text-foreground hover:text-primary">
                Patient Login
              </Button>
              <Button onClick={() => onSelectRole("doctor")} className="btn-glow bg-primary text-white hover:bg-primary/90">
                <Stethoscope className="w-4 h-4 mr-2" />
                Doctor Portal
              </Button>
            </div>
          </div>
        </div>
      </nav>


      {/* Hero Section with Slider */}
      <section className="relative h-screen overflow-hidden pt-16">
        {heroSlides.map((slide, index) => (
          <div
            key={index}
            className={`absolute inset-0 transition-opacity duration-1000 ${index === currentSlide ? "opacity-100" : "opacity-0 pointer-events-none"}`}
          >
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
                      Get Started
                      <ChevronRight className="w-5 h-5 ml-2" />
                    </Button>
                    <Button size="lg" onClick={() => onSelectRole("doctor")} className="bg-transparent border-2 border-white text-white hover:bg-white/20 px-8 py-6 text-lg font-semibold">
                      <Stethoscope className="w-5 h-5 mr-2" />
                      Doctor Portal
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
              <button
                key={index}
                onClick={() => setCurrentSlide(index)}
                className={`h-2 rounded-full transition-all ${index === currentSlide ? "w-8 bg-white" : "w-2 bg-white/50"}`}
              />
            ))}
          </div>
          <button onClick={nextSlide} className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-sm flex items-center justify-center text-white hover:bg-white/30 transition-colors">
            <ChevronRight className="w-6 h-6" />
          </button>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 bg-primary">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl sm:text-5xl font-bold text-white mb-2">{stat.value}</div>
                <div className="text-white/80">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="text-primary font-semibold text-sm uppercase tracking-wider">Why Choose Us</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mt-2 mb-4">
              Healthcare Made Simple
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Experience seamless healthcare with our innovative platform designed for both patients and doctors
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-all duration-300 hover:-translate-y-2 group border border-border">
                  <div className="w-14 h-14 bg-primary rounded-xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform">
                    <Icon className="w-7 h-7 text-primary-foreground" />
                  </div>
                  <h3 className="text-xl font-semibold text-foreground mb-3">{feature.title}</h3>
                  <p className="text-muted-foreground">{feature.description}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>


      {/* About Section */}
      <section id="about" className="py-24 bg-background">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div className="relative">
              <div className="relative z-10">
                <img
                  src="https://images.unsplash.com/photo-1666214280557-f1b5022eb634?w=800&q=80"
                  alt="Doctor consultation"
                  className="rounded-2xl shadow-2xl"
                />
              </div>
              <div className="absolute -bottom-8 -right-8 w-64 h-64 bg-primary rounded-2xl -z-10 opacity-20" />
            </div>

            <div>
              <span className="text-primary font-semibold text-sm uppercase tracking-wider">About SanteConnect</span>
              <h2 className="text-3xl sm:text-4xl font-bold text-foreground mt-2 mb-6">
                Transforming Healthcare Through Technology
              </h2>
              <p className="text-lg text-muted-foreground mb-8">
                SanteConnect bridges the gap between patients and healthcare providers using cutting-edge AI technology. 
                Our platform enables seamless communication, intelligent diagnostics, and personalized care plans.
              </p>

              <div className="space-y-4">
                {[
                  "AI-powered symptom analysis and recommendations",
                  "Secure video consultations with certified doctors",
                  "Integrated appointment scheduling and reminders",
                  "Complete medical history and records management",
                ].map((item, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div className="w-6 h-6 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                      <CheckCircle className="w-4 h-4 text-primary" />
                    </div>
                    <span className="text-foreground">{item}</span>
                  </div>
                ))}
              </div>

              <Button size="lg" className="mt-8 btn-glow">
                Learn More
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-24 bg-muted/30">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <span className="text-primary font-semibold text-sm uppercase tracking-wider">Testimonials</span>
            <h2 className="text-3xl sm:text-4xl font-bold text-foreground mt-2 mb-4">
              What Our Users Say
            </h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">
              Join thousands of satisfied patients and doctors who trust SanteConnect
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <div key={index} className="bg-card rounded-2xl p-8 shadow-lg hover:shadow-xl transition-shadow border border-border">
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

      {/* CTA Section */}
      <section className="py-24 bg-primary relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-0 left-0 w-96 h-96 bg-white rounded-full blur-3xl -translate-x-1/2 -translate-y-1/2" />
          <div className="absolute bottom-0 right-0 w-96 h-96 bg-white rounded-full blur-3xl translate-x-1/2 translate-y-1/2" />
        </div>

        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center relative z-10">
          <Sparkles className="w-12 h-12 text-white/80 mx-auto mb-6" />
          <h2 className="text-3xl sm:text-4xl font-bold text-white mb-6">
            Ready to Transform Your Healthcare Experience?
          </h2>
          <p className="text-xl text-white/90 mb-8">
            Join SanteConnect today and experience the future of healthcare
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            <Button size="lg" onClick={() => onSelectRole("patient")} className="bg-white text-primary hover:bg-white/90 px-8 py-6 text-lg font-semibold">
              <Users className="w-5 h-5 mr-2" />
              Patient Sign Up
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
                Revolutionizing healthcare through technology and compassion.
              </p>
            </div>

            <div>
              <h4 className="font-semibold mb-4">Quick Links</h4>
              <ul className="space-y-2 text-background/70">
                <li><a href="#features" className="hover:text-background transition-colors">Features</a></li>
                <li><a href="#about" className="hover:text-background transition-colors">About Us</a></li>
                <li><a href="#testimonials" className="hover:text-background transition-colors">Testimonials</a></li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold mb-4">Services</h4>
              <ul className="space-y-2 text-background/70">
                <li><span className="hover:text-background transition-colors cursor-pointer">AI Diagnostics</span></li>
                <li><span className="hover:text-background transition-colors cursor-pointer">Video Consultations</span></li>
                <li><span className="hover:text-background transition-colors cursor-pointer">Appointment Booking</span></li>
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
