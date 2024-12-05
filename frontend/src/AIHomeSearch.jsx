import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MessageCircle } from 'lucide-react';

const AIHomeSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const navigate = useNavigate();

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const quickSearches = [
    { text: "3BHK homes in Victoria", query: "3BHK homes in Victoria" },
    { text: "Affordable homes in New South Wales", query: "Affordable homes in New South Wales" },
    // { text: "Show me homes with price drops", query: "homes with price drops" },
    // { text: "How is the housing market here?", query: "housing market analysis" }
  ];

  return (
    <div className="relative h-screen bg-gradient-to-b from-black/50 to-black/30 flex flex-col items-center justify-center px-4">
      {/* Background Image */}
      <div className="absolute inset-0 -z-10">
        <img
          src="background.jpg"
          alt="Modern home at dusk"
          className="w-full h-full object-cover"
        />
      </div>

      {/* Main Content */}
      <h1 className="text-4xl md:text-6xl text-white font-serif mb-8 text-center">AI-powered home search.</h1>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="w-full max-w-2xl">
        <div className="relative">
          <input
            type="text"
            placeholder="Enter an address, city, neighborhood or ZIP code"
            className="w-full p-4 pr-12 rounded-lg shadow-lg text-lg"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <button 
            type="submit"
            className="absolute right-2 top-1/2 -translate-y-1/2 p-2"
          >
            <Search className="w-6 h-6 text-gray-500" />
          </button>
        </div>
      </form>

      {/* Quick Search Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-8 w-full max-w-2xl">
        {quickSearches.map((item, index) => (
          <button
            key={index}
            onClick={() => {
              setSearchQuery(item.query);
              navigate(`/search?q=${encodeURIComponent(item.query)}`);
            }}
            className="p-4 bg-black/60 text-white rounded-lg hover:bg-black/70 transition text-left"
          >
            {item.text}
          </button>
        ))}
      </div>

      {/* Action Buttons */}
      <div className="mt-8 flex flex-col md:flex-row gap-4">
        <button 
          onClick={() => navigate('/search')}
          className="flex items-center justify-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
        >
          <MessageCircle className="w-5 h-5" />
          Ask Flyhomes AI
        </button>
      </div>
    </div>
  );
};

export default AIHomeSearch;