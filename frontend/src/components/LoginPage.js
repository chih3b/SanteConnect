import { useState } from "react";
import { useAuth } from "./AuthContext";
import { Button } from "./ui/button";
import { Card } from "./ui/card";
import { ArrowLeft, Heart, Shield, Clock } from "lucide-react";

const LoginPage = ({ onBack }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let result;
      if (isLogin) {
        result = await login(email, password);
      } else {
        if (!name.trim()) {
          setError('Name is required');
          setLoading(false);
          return;
        }
        result = await register(email, password, name);
      }

      if (!result.success) {
        setError(result.error);
      }
    } catch (err) {
      setError('Connection error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-primary via-blue-600 to-indigo-700 p-12 flex-col justify-between relative overflow-hidden">
        {/* Background Pattern */}
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-20 w-72 h-72 bg-white rounded-full blur-3xl" />
          <div className="absolute bottom-20 right-20 w-96 h-96 bg-white rounded-full blur-3xl" />
        </div>
        
        <div className="relative z-10">
          <div className="flex items-center gap-3 mb-8">
            <img src="/logo.png" alt="SanteConnect" className="w-12 h-12 object-contain brightness-0 invert" />
            <span className="text-2xl font-bold text-white">SanteConnect</span>
          </div>
          
          <h1 className="text-4xl font-bold text-white mb-4">
            Your Health Journey<br />Starts Here
          </h1>
          <p className="text-xl text-white/80">
            Access AI-powered medical assistance, medication information, and personalized health guidance.
          </p>
        </div>

        <div className="relative z-10 space-y-6">
          {[
            { icon: Heart, title: "Smart Health Assistant", desc: "Get instant answers to your health questions" },
            { icon: Shield, title: "Secure & Private", desc: "Your health data is always protected" },
            { icon: Clock, title: "Available 24/7", desc: "Access healthcare guidance anytime" },
          ].map((feature, i) => (
            <div key={i} className="flex items-start gap-4">
              <div className="p-2 bg-white/20 rounded-lg">
                <feature.icon className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-white">{feature.title}</h3>
                <p className="text-sm text-white/70">{feature.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Right Side - Form */}
      <div className="flex-1 flex items-center justify-center p-6 lg:p-12">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <img src="/logo.png" alt="SanteConnect" className="w-10 h-10 object-contain" />
            <span className="text-xl font-bold">SanteConnect</span>
          </div>

          {/* Back Button */}
          {onBack && (
            <button
              onClick={onBack}
              className="flex items-center gap-2 text-muted-foreground hover:text-foreground mb-6 transition-colors"
            >
              <ArrowLeft size={18} />
              <span className="text-sm">Back to home</span>
            </button>
          )}

          <Card className="p-6 sm:p-8 card-glow">
            {/* Header */}
            <div className="text-center mb-8">
              <h1 className="text-2xl font-bold">Patient Portal</h1>
              <p className="text-muted-foreground mt-1 text-sm">
                {isLogin ? 'Welcome back! Sign in to continue' : 'Create your account to get started'}
              </p>
            </div>

            {/* Tabs */}
            <div className="flex mb-6 bg-muted rounded-lg p-1">
              <button
                onClick={() => setIsLogin(true)}
                className={`flex-1 py-2.5 rounded-md text-sm font-medium transition-all ${
                  isLogin ? 'bg-background shadow text-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Sign In
              </button>
              <button
                onClick={() => setIsLogin(false)}
                className={`flex-1 py-2.5 rounded-md text-sm font-medium transition-all ${
                  !isLogin ? 'bg-background shadow text-primary' : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Sign Up
              </button>
            </div>

            {/* Error */}
            {error && (
              <div className="mb-4 p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive text-sm">
                {error}
              </div>
            )}

            {/* Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {!isLogin && (
                <div>
                  <label className="block text-sm font-medium mb-1.5">Full Name</label>
                  <input
                    type="text"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    className="w-full px-4 py-2.5 border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                    placeholder="Your name"
                  />
                </div>
              )}
              
              <div>
                <label className="block text-sm font-medium mb-1.5">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-2.5 border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="you@example.com"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1.5">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-2.5 border border-input rounded-lg bg-background focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
                  placeholder="••••••••"
                  required
                  minLength={6}
                />
              </div>

              <Button
                type="submit"
                disabled={loading}
                className="w-full h-11 btn-glow"
              >
                {loading ? 'Please wait...' : (isLogin ? 'Sign In' : 'Create Account')}
              </Button>
            </form>

            <p className="mt-6 text-center text-sm text-muted-foreground">
              {isLogin ? "Don't have an account? " : "Already have an account? "}
              <button
                onClick={() => setIsLogin(!isLogin)}
                className="text-primary hover:underline font-medium"
              >
                {isLogin ? 'Sign up' : 'Sign in'}
              </button>
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
