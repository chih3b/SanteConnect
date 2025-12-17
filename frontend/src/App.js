import React, { useState } from "react";
import { Card } from "./components/ui/card";
import { AuthProvider, useAuth } from "./components/AuthContext";
import { ThemeProvider } from "./components/ThemeContext";
import LoginPage from "./components/LoginPage";
import LandingPage from "./components/LandingPage";
import DoctorLoginPage from "./components/DoctorLoginPage";
import DoctorDashboard from "./components/DoctorDashboard";
import Sidebar from "./components/Sidebar";
import ChatbotPopup from "./components/ChatbotPopup";
import { Menu } from "lucide-react";

const ImageUpload = React.lazy(() => import("./components/ImageUpload"));
const ChatInterface = React.lazy(() => import("./components/ChatInterface"));
const SearchBar = React.lazy(() => import("./components/SearchBar"));
const MedicationCard = React.lazy(() => import("./components/MedicationCard"));
const PrescriptionScan = React.lazy(() =>
  import("./components/PrescriptionScan")
);
const MediBot = React.lazy(() => import("./components/MediBot"));

function Spinner() {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );
}

// Patient Main App
function PatientApp() {
  const [activeTab, setActiveTab] = useState("chat");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const titles = {
    identify: "Medication Identification",
    search: "Search Medications",
    chat: "AI Medical Assistant",
    "scan-prescription": "Scan your Prescription",
    medibot: "Dr. MediBot - Consultation Médicale",
  };

  const subtitles = {
    identify: "Upload an image to identify medications",
    search: "Search our database of Tunisian medications",
    chat: "Ask questions about medications",
    "scan-prescription": "Upload your prescription for analysis",
    medibot: "Consultation médicale vocale avec IA",
  };

  const handleConversationCreated = (conv) => {
    setCurrentConversation(conv);
    setRefreshTrigger((r) => r + 1);
  };

  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
        currentConversation={currentConversation}
        onSelectConversation={setCurrentConversation}
        refreshTrigger={refreshTrigger}
      />
      <main className="flex-1 flex flex-col min-h-screen lg:ml-64 ml-0">
        {/* Mobile Header with Logo and Menu Button */}
        <div className="lg:hidden bg-card border-b px-4 py-3 flex items-center gap-3">
          <button
            onClick={() => window.openMobileSidebar?.()}
            className="p-2 hover:bg-muted rounded-lg"
          >
            <Menu size={22} />
          </button>
          <img src="/logo.png" alt="SanteConnect" className="w-8 h-8 object-contain" />
          <span className="font-bold text-sm">SanteConnect</span>
        </div>
        
        <header className="bg-card border-b px-4 sm:px-6 py-4 hidden lg:block">
          <div className="max-w-6xl mx-auto">
            <h1 className="text-lg sm:text-xl font-semibold">
              {titles[activeTab]}
            </h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">
              {subtitles[activeTab]}
            </p>
          </div>
        </header>

        <div className="flex-1 p-4 sm:p-6">
          <div className="max-w-6xl mx-auto">
            <React.Suspense fallback={<Spinner />}>
              {activeTab === "identify" && (
                <ImageUpload setResult={setResult} setLoading={setLoading} />
              )}
              {activeTab === "scan-prescription" && (
                <PrescriptionScan setResult={setResult} setLoading={setLoading} />
              )}
              {activeTab === "search" && (
                <SearchBar setResult={setResult} setLoading={setLoading} />
              )}
              {activeTab === "chat" && (
                <ChatInterface
                  conversation={currentConversation}
                  onConversationCreated={handleConversationCreated}
                />
              )}
              {activeTab === "medibot" && <MediBot />}
              {loading && (
                <div className="fixed inset-0 bg-background/90 flex items-center justify-center z-30">
                  <Card className="p-6 sm:p-8 max-w-sm text-center card-glow mx-4">
                    <div className="flex items-center justify-center gap-2 mb-4">
                      <div className="w-3 h-3 rounded-full bg-primary animate-bounce"></div>
                      <div
                        className="w-3 h-3 rounded-full bg-primary animate-bounce"
                        style={{ animationDelay: "150ms" }}
                      ></div>
                      <div
                        className="w-3 h-3 rounded-full bg-primary animate-bounce"
                        style={{ animationDelay: "300ms" }}
                      ></div>
                    </div>
                    <p className="mt-4 font-medium">Processing...</p>
                  </Card>
                </div>
              )}
              {result &&
                !loading &&
                activeTab !== "chat" &&
                activeTab !== "scan-prescription" && (
                  <MedicationCard result={result} />
                )}
            </React.Suspense>
          </div>
        </div>

        <footer className="bg-card border-t px-4 sm:px-6 py-3 text-center">
          <p className="text-xs sm:text-sm text-muted-foreground">
            ⚠️ For informational purposes only.
          </p>
        </footer>
      </main>

      <ChatbotPopup />
    </div>
  );
}

// Main App Content with Role-based Routing
function AppContent() {
  const { user, userRole, loading } = useAuth();
  const [selectedRole, setSelectedRole] = useState(null);

  if (loading) return <Spinner />;

  // If user is logged in
  if (user) {
    // Doctor dashboard
    if (userRole === "doctor") {
      return <DoctorDashboard />;
    }
    // Patient app
    return <PatientApp />;
  }

  // Not logged in - show role selection or login
  if (!selectedRole) {
    return <LandingPage onSelectRole={setSelectedRole} />;
  }

  if (selectedRole === "doctor") {
    return <DoctorLoginPage onBack={() => setSelectedRole(null)} />;
  }

  // Patient login (existing LoginPage)
  return <LoginPage onBack={() => setSelectedRole(null)} />;
}

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <AppContent />
      </AuthProvider>
    </ThemeProvider>
  );
}
