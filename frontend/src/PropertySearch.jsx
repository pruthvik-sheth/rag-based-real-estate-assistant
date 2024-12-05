import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Search, Heart, ArrowLeft, X, ExternalLink, Bell } from 'lucide-react';

const PropertySearch = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [searchQuery, setSearchQuery] = useState(searchParams.get('q') || '');
  const [properties, setProperties] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [aiResponse, setAiResponse] = useState('');

  useEffect(() => {
    if (searchQuery) {
      searchProperties(searchQuery);
    }
  }, []);

  const searchProperties = async (query) => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:5000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          top_k: 5
        }),
      });
      
      const data = await response.json();
      if (data.success) {
        setProperties(data.properties || []);
        setAiResponse(data.response || '');
      } else {
        setError('Failed to fetch properties');
      }
    } catch (err) {
      setError('Error connecting to the server');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (searchQuery) {
      searchProperties(searchQuery);
      navigate(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
    }).format(price);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="border-b bg-white sticky top-0 z-10">
        <div className="flex items-center gap-4 p-4 max-w-7xl mx-auto">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-900"
          >
            <ArrowLeft className="w-4 h-4" />
            Back
          </button>
          <div className="flex-1">
            <form onSubmit={handleSearch}>
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Enter location or search properties..."
                  className="w-full p-2 pr-10 border rounded-lg"
                />
                <button 
                  type="submit"
                  className="absolute right-2 top-1/2 -translate-y-1/2"
                >
                  <Search className="w-5 h-5 text-gray-400" />
                </button>
              </div>
            </form>
          </div>
          <button 
            onClick={() => navigate('/')}
            className="p-2 hover:bg-gray-100 rounded-lg"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto p-4">
        {loading ? (
          <div className="text-center py-8">Loading...</div>
        ) : error ? (
          <div className="text-center py-8 text-red-600">{error}</div>
        ) : (
          <>
            {/* House Icon with Response */}
            <div className="flex gap-4 mb-6">
              <div className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center">
                🏠
              </div>
              <div className="flex-1">
                <div className="bg-gray-100 rounded-lg p-3 text-sm">
                  {aiResponse}
                </div>
              </div>
            </div>

            {/* Property Count and Actions */}
            <div className="bg-gray-100 rounded-lg p-6 mb-6">
              <div className="flex items-center gap-4 mb-4">
                <div className="p-2 bg-white rounded-lg">
                  🏠
                </div>
                <div>
                  <p className="text-lg">
                    We found {properties.length} homes in this area. Click the button below to see them all on our search page.
                  </p>
                </div>
              </div>
              
              <div className="flex flex-col sm:flex-row gap-4">
                <button className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition">
                  GO TO HOME SEARCH
                </button>
                <button className="px-4 py-2 bg-white hover:bg-gray-50 rounded-lg transition flex items-center justify-center gap-2">
                  <Bell className="w-4 h-4" />
                  GET ALERTS FOR THESE HOMES
                </button>
              </div>
            </div>

            {/* Property Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {properties.map((property) => (
                <div key={property.property_id} className="bg-white rounded-lg overflow-hidden border shadow-sm">
                  <div className="relative">
                    <img
                      src={property.images || "/api/placeholder/400/300"}
                      alt={property.street_address}
                      className="w-full h-48 object-cover"
                    />
                    <button className="absolute top-2 right-2 p-1.5 bg-white rounded-full hover:bg-gray-100">
                      <Heart className="w-5 h-5" />
                    </button>
                    <div className="absolute top-2 left-2 bg-red-500 text-white px-3 py-1 rounded-full text-sm">
                      Open Tomorrow, 9:30-12:30 PM
                    </div>
                  </div>
                  
                  <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-xl font-medium">
                        {formatPrice(property.price)}
                      </h3>
                      <button className="p-1 hover:bg-gray-100 rounded">
                        <ExternalLink className="w-5 h-5" />
                      </button>
                    </div>
                    
                    <p className="text-gray-600">
                      {property.bedrooms} beds • {property.bathrooms} baths • 
                      {property.floor_area} sqft • {property.property_type}
                    </p>
                    
                    <p className="text-gray-500 text-sm mt-1">
                      {property.street_address},
                      {property.suburb}, {property.state} {property.postcode}
                    </p>
                    
                    <div className="mt-2 flex flex-wrap gap-2">
                      {property.amenities?.slice(0, 2).map((amenity, index) => (
                        <span 
                          key={index}
                          className="px-2 py-1 bg-gray-100 text-sm rounded"
                        >
                          {amenity}
                        </span>
                      ))}
                      {property.amenities?.length > 2 && (
                        <span className="px-2 py-1 bg-blue-50 text-blue-600 text-sm rounded">
                          +{property.amenities.length - 2} more
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default PropertySearch;