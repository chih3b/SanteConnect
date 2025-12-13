import React, { useState } from 'react';
import { Search } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';

const SearchBar = ({ setResult, setLoading }) => {
  const [query, setQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);

  const searchMedications = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setResult(null);
    setSearchResults([]);

    try {
      const response = await fetch(`http://localhost:8000/search/${encodeURIComponent(query)}`);
      const data = await response.json();
      
      if (data.results && data.results.length > 0) {
        setSearchResults(data.results);
      } else {
        setResult({
          success: false,
          answer: `No medications found for "${query}".\n\nTips:\n• Try the generic name (e.g., "paracetamol" instead of brand name)\n• Check spelling\n• Try searching by active ingredient\n• Use the AI Assistant for help`
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

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Search className="h-5 w-5" />
          Search Medications
        </CardTitle>
        <CardDescription>
          Search by name, active ingredient, or condition
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-2">
          <Input
            placeholder="e.g., Paracétamol, pain relief, headache..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyPress={handleKeyPress}
            className="flex-1"
          />
          <Button 
            onClick={searchMedications}
            disabled={!query.trim()}
          >
            <Search className="h-4 w-4 mr-2" />
            Search
          </Button>
        </div>

        {searchResults.length > 0 && (
          <div className="mt-6 space-y-3">
            <h3 className="text-base font-semibold">
              Search Results ({searchResults.length})
            </h3>
            <p className="text-sm text-muted-foreground mb-4">
              Click on any result for detailed information
            </p>
            {searchResults.map((result, index) => {
              // Color code by similarity
              const similarityColor = 
                result.similarity_score >= 80 ? 'text-green-600' :
                result.similarity_score >= 60 ? 'text-yellow-600' :
                'text-orange-600';
              
              return (
                <Card 
                  key={index}
                  className="cursor-pointer hover:border-primary transition-colors"
                  onClick={() => getMedicationDetails(result.drug_name)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <CardTitle className="text-base text-primary">
                        {result.drug_name}
                      </CardTitle>
                      <span className={`text-xs font-semibold ${similarityColor}`}>
                        {result.similarity_score}% match
                      </span>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-1 text-sm">
                    <p><span className="font-medium">Usage:</span> {result.info.usage}</p>
                    <p><span className="font-medium">Dosage:</span> {result.info.dosage}</p>
                    {result.info.manufacturer && (
                      <p><span className="font-medium">Manufacturer:</span> {result.info.manufacturer}</p>
                    )}
                    <p className="text-primary text-xs mt-2">
                      Click for detailed information →
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default SearchBar;
