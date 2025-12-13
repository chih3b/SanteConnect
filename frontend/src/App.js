import React, { useState } from 'react';
import { Card } from './components/ui/card';
import { AuthProvider, useAuth } from './components/AuthContext';
import LoginPage from './components/LoginPage';
import Sidebar from './components/Sidebar';

const ImageUpload = React.lazy(() => import('./components/ImageUpload'));
const ChatInterface = React.lazy(() => import('./components/ChatInterface'));
const SearchBar = React.lazy(() => import('./components/SearchBar'));
const MedicationCard = React.lazy(() => import('./components/MedicationCard'));

function Spinner() {
  return (
    <div className="flex items-center justify-center p-12">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    </div>
  );
}

function MainApp() {
  const [activeTab, setActiveTab] = useState('chat');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  const titles = {
    identify: 'Medication Identification',
    search: 'Search Medications', 
    chat: 'AI Medical Assistant'
  };
  
  const subtitles = {
    identify: 'Upload an image to identify medications',
    search: 'Search our database of Tunisian medications',
    chat: 'Ask questions about medications'
  };

  const handleConversationCreated = (conv) => {
    setCurrentConversation(conv);
    setRefreshTrigger(r => r + 1); // Trigger sidebar refresh
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
      {/* Main content - responsive margin */}
      <main className="flex-1 flex flex-col min-h-screen lg:ml-64 ml-0">
        {/* Header - responsive padding */}
        <header className="bg-card border-b px-4 sm:px-6 py-4">
          <div className="max-w-6xl mx-auto pl-12 lg:pl-0">
            <h1 className="text-lg sm:text-xl font-semibold">{titles[activeTab]}</h1>
            <p className="text-xs sm:text-sm text-muted-foreground mt-0.5">{subtitles[activeTab]}</p>
          </div>
        </header>
        
        {/* Content - responsive padding */}
        <div className="flex-1 p-4 sm:p-6">
          <div className="max-w-6xl mx-auto">
            <React.Suspense fallback={<Spinner />}>
              {activeTab === 'identify' && <ImageUpload setResult={setResult} setLoading={setLoading} />}
              {activeTab === 'search' && <SearchBar setResult={setResult} setLoading={setLoading} />}
              {activeTab === 'chat' && (
                <ChatInterface 
                  conversation={currentConversation} 
                  onConversationCreated={handleConversationCreated} 
                />
              )}
              {loading && (
                <div className="fixed inset-0 bg-background/90 flex items-center justify-center z-30">
                  <Card className="p-6 sm:p-8 max-w-sm text-center card-glow mx-4">
                    <div className="flex items-center justify-center gap-2 mb-4">
                      <div className="w-3 h-3 rounded-full bg-primary animate-bounce"></div>
                      <div className="w-3 h-3 rounded-full bg-primary animate-bounce" style={{animationDelay:'150ms'}}></div>
                      <div className="w-3 h-3 rounded-full bg-primary animate-bounce" style={{animationDelay:'300ms'}}></div>
                    </div>
                    <p className="mt-4 font-medium">Processing...</p>
                  </Card>
                </div>
              )}
              {result && !loading && activeTab !== 'chat' && <MedicationCard result={result} />}
            </React.Suspense>
          </div>
        </div>
        
        <footer className="bg-card border-t px-4 sm:px-6 py-3 text-center">
          <p className="text-xs sm:text-sm text-muted-foreground">⚠️ For informational purposes only.</p>
        </footer>
      </main>
    </div>
  );
}

function AppContent() {
  const { user, loading } = useAuth();
  if (loading) return <Spinner />;
  if (!user) return <LoginPage />;
  return <MainApp />;
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
