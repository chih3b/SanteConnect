import React, { useState } from 'react';
import { Search, Pill, Sparkles, TrendingUp, Loader2 } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';

const SearchBar = ({ setResult, setLoading }) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearching, setIsSearching] = useState(false);

  const popularSearches = [
    'Doliprane', 'Paracétamol', 'Aspirin', 'Ibuprofen', 'Amoxicilline'
  ];

  const searchMedications = async (searchQuery = query) => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    setIsSearching(true);
    setResult(null);
    setSearchResults([]);

    try {
      const response = await fetch(`http://localhost:8000/search/${encodeURIComponent(searchQuery)}`);
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        setSearchResults(data.results);
      } else {
        setResult({
          success: false,
          answer: `No medications found for "${searchQuery}".\n\nTips:\n• Try the generic name (e.g., "paracetamol" instead of brand name)\n• Check spelling\n• Try searching by active ingredient`
        });
      }
    } catch (error) {
      setResult({
        success: false,
        answer: 'Error connecting to server. Please ensure the backend is running.',
        error: error.message
      });
    } finally {
      setLoading(false);
      setIsSearching(false);
    }
  };

  const getMedicationDetails = async (drugName) => {
    setLoading(true);
    setResult(null);

    try {
      const response = await fetch(`http://localhost:8000/agent/query?query=${encodeURIComponent(`Tell me about ${drugName}`)}`);
      const data = await response.json();
      setResult(data);
      setSearchResults([]);
    } catch (error) {
      setResult({
        success: false,
        answer: 'Error getting medication details.',
        error: error.message
      });
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      searchMedications();
    }
  };

  const handleQuickSearch = (term) => {
    setQuery(term);
    searchMedications(term);
  };

  return (
    <div className="space-y-6">
      {/* Search Card */}
      <Card className="card-glow overflow-hidden">
        <div className="bg-gradient-to-r from-emerald-600 to-teal-600 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-card/20 rounded-lg backdrop-blur">
              <Search className="w-6 h-6 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-white">Search Medications</h2>
              <p className="text-emerald-100 text-sm">Find information about any medication</p>
            </div>
          </div>
        </div>
        
        <CardContent className="p-6 space-y-4">
          {/* Search Input */}
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                placeholder="Search by name, ingredient, or condition..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={handleKeyPress}
                className="pl-10 h-12 text-base"
              />
            </div>
            <Button 
              onClick={() => searchMedications()}
              disabled={!query.trim() || isSearching}
              className="h-12 px-6 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700"
            >
              {isSearching ? (
                <Loader2 className="w-5 h-5 animate-spin" />
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </>
              )}
            </Button>
          </div>

          {/* Popular Searches */}
          <div>
            <div className="flex items-center gap-2 mb-3">
              <TrendingUp className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Popular searches</span>
            </div>
            <div className="flex flex-wrap gap-2">
              {popularSearches.map((term) => (
                <button
                  key={term}
                  onClick={() => handleQuickSearch(term)}
                  className="px-3 py-1.5 bg-muted hover:bg-primary/10 hover:text-primary rounded-full text-sm font-medium transition-colors"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Search Results */}
      {searchResults.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-emerald-600" />
              Found {searchResults.length} medication(s)
            </h3>
            <span className="text-sm text-muted-foreground">Click for details</span>
          </div>
          
          <div className="grid gap-3">
            {searchResults.map((result, index) => {
              const matchColor = 
                result.similarity_score >= 80 ? 'from-green-500 to-emerald-500' :
                result.similarity_score >= 60 ? 'from-yellow-500 to-amber-500' :
                'from-orange-500 to-red-500';
              
              return (
                <Card 
                  key={index}
                  className="cursor-pointer hover:shadow-lg transition-all duration-300 hover:-translate-y-1 overflow-hidden group"
                  onClick={() => getMedicationDetails(result.drug_name)}
                >
                  <div className="flex">
                    {/* Match indicator */}
                    <div className={`w-1.5 bg-gradient-to-b ${matchColor}`} />
                    
                    <div className="flex-1 p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex items-start gap-3">
                          <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                            <Pill className="w-5 h-5 text-emerald-600" />
                          </div>
                          <div>
                            <h4 className="font-semibold text-primary group-hover:underline">
                              {result.drug_name}
                            </h4>
                            <p className="text-sm text-muted-foreground mt-1 line-clamp-1">
                              {result.info.usage}
                            </p>
                            {result.info.dosage && (
                              <p className="text-xs text-muted-foreground mt-1">
                                💊 {result.info.dosage}
                              </p>
                            )}
                          </div>
                        </div>
                        
                        <div className="text-right flex-shrink-0">
                          <span className={`inline-block px-2.5 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${matchColor}`}>
                            {result.similarity_score}%
                          </span>
                          <p className="text-xs text-muted-foreground mt-1">match</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default SearchBar;
