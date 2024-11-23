import React, { useState } from 'react';
import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
// Importing the speech recognition module		
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;		
const recognition = SpeechRecognition ? new SpeechRecognition() : null;
function App() {
  const [searchType, setSearchType] = useState(null);
  const [query, setQuery] = useState('');
  const [orderNumber, setOrderNumber] = useState('');
  const [image, setImage] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [recommendations, setRecommendations] = useState([]);
  const [orderStatus, setOrderStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [imageSearchResults, setImageSearchResults] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const handleSearch = () => {
    if (searchType === 'product' && !query) {
      alert('Please enter a search term for products.');
      return;
    }
    if (searchType === 'order' && !orderNumber) {
      alert('Please enter your order number.');
      return;
    }

    setSearchResults([]);
    setRecommendations([]);
    setImageSearchResults([]);
    setOrderStatus(null);
    setError('');
    setLoading(true);

    if (searchType === 'product') {
      fetch('http://localhost:5000/api/search?query=' + query)
        .then((response) => response.json())
        .then((data) => {
          console.log("Full Response Data:", data);
    
          if (Array.isArray(data)) {
            const formattedSearchResults = data.map((product) => {
              try {
                const parsedCategory = product.category ? JSON.parse(product.category) : [];
                // Handle NaN values for image_url
                product.image_url = product.image_url && product.image_url !== 'NaN' ? product.image_url : 'default-image.jpg'; // Replace with a valid fallback image
                return { ...product, category: parsedCategory };
              } catch (error) {
                console.error("Error parsing category:", error);
                return { ...product, category: [] };
              }
            });
            setSearchResults(formattedSearchResults);
          } else if (data && data.search_results && Array.isArray(data.search_results)) {
            const formattedSearchResults = (data.search_results || []).map((product) => {
              try {
                const parsedCategory = product.category ? JSON.parse(product.category) : [];
                // Handle NaN values for image_url
                product.image_url = product.image_url && product.image_url !== 'NaN' ? product.image_url : 'default-image.jpg'; // Replace with a valid fallback image
                return { ...product, category: parsedCategory };
              } catch (error) {
                console.error("Error parsing category:", error);
                return { ...product, category: [] };
              }
            });
    
            setSearchResults(formattedSearchResults);
    
            // Check if no search results are found and set error accordingly
            if (formattedSearchResults.length === 0) {
              setError('No products found ');
            } else if (Array.isArray(data.category_recommendations)) {
              setRecommendations(data.category_recommendations);
            } else {
              setRecommendations([]);
            }
          } else if (data && data.error) {
            // If the response contains an error, display the error message
            setError(data.error);  // For example: "No products found"
          } else {
            setError('Invalid data format: Expected search_results as an array or raw array.');
          }
        })
        .catch((error) => {
          setError('Error fetching data. Please try again.');
          console.error('Error:', error);
        })
        .finally(() => {
          setLoading(false);
          setSearchType(null);
        });
    }
    
    
    else if (searchType === 'order') {
      fetch('http://localhost:5000/api/order-status?orderNo=' + orderNumber)
        .then((response) => {
          if (!response.ok) {
            throw new Error('Order not found.');
          }
          return response.json();
        })
        .then((data) => {
          if (data && data.order_no) {
            setOrderStatus(data);
          } else {
            setError('Order not found or invalid response format.');
          }
        })
        .catch((error) => {
          setError(error.message || 'Error fetching data. Please try again.');
        })
        .finally(() => {
          setLoading(false);
          setSearchType(null);
        });
    }
  };

  const handleImageSearch = async (event) => {
    event.preventDefault();
    if (!image) {
      alert('Please upload an image.');
      return;
    }

    setLoading(true);
    setError('');
    setImageSearchResults([]);

    const formData = new FormData();
    formData.append('image', image);

    try {
      const response = await fetch('http://localhost:5000/api/image-search', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok) {
        setImageSearchResults(data.search_results || []);
      } else {
        setError('No matching products found.');
        setImageSearchResults([]);
      }
    } catch (err) {
      setError('Error processing the image search. Please try again.');
      setImageSearchResults([]);
    } finally {
      setLoading(false);
      setSearchType(null);
    }
  };

  const handleInputChange = (event) => {
    if (searchType === 'product') {
      setQuery(event.target.value);
    } else if (searchType === 'order') {
      setOrderNumber(event.target.value);
    }
  };

  const handleSearchTypeSelection = (type) => {
    setSearchType(type);
    setQuery('');
    setOrderNumber('');
    setSearchResults([]);
    setRecommendations([]);
    setImageSearchResults([]);
    setOrderStatus(null);
    setError('');
    setLoading(false);
  };
  const startListening = () => {

    if (!recognition) {

      alert('Voice recognition is not supported in your browser.');

      return;

    }

    setIsListening(true);

    recognition.start();

    recognition.onresult = (event) => {

      const spokenQuery = event.results[0][0].transcript;

      setQuery(spokenQuery);

      setIsListening(false);

    };

    recognition.onerror = (event) => {

      console.error('Recognition error:', event);

      setIsListening(false);

    };

  };

  return (
    <div className="App container">
      <header className="App-header text-center my-4">
  <h1 
    style={{
      textAlign: 'center',
      color:'rgb(115, 166, 145)',
      fontWeight: 'bold',
      textShadow: '2px 2px 10px rgba(0, 0, 0, 0.4)',
      backgroundColor: '#B0E0E6',  
      padding: '20px'
    }}
  >
    SmartShopper
  </h1>
</header>



      {!searchType ? (
        <div className="mb-3 text-center">
         
          <div className="button-container">
            <button className="btn btn-primary" onClick={() => handleSearchTypeSelection('product')}>
              Search for Products
            </button>
            <button className="btn btn-secondary" onClick={() => handleSearchTypeSelection('order')}>
              Check Order Status
            </button>
            <button className="btn btn-success" onClick={() => handleSearchTypeSelection('image')}>
              Search by Image
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="mb-3">
            {searchType === 'product' && (
              <div>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Search for products..."
                  value={query}
                  onChange={handleInputChange}
                />
                <button className="button-search" onClick={handleSearch}>
                  Search Products
                </button>
                <button

                  className="btn btn-warning mt-2"

                  onClick={startListening}

                  disabled={isListening}

                >

                  {isListening ? 'Listening...' : 'Search with Voice'}

                </button>
              </div>
            )}

            {searchType === 'order' && (
              <div>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Enter Order Number"
                  value={orderNumber}
                  onChange={handleInputChange}
                />
                <button className="btn btn-secondary mt-2" onClick={handleSearch}>
                  Check Order Status
                </button>
              </div>
            )}

            {searchType === 'image' && (
              <div>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setImage(e.target.files[0])}
                />
                <button className="btn btn-success mt-2" onClick={handleImageSearch}>
                  Search using Image
                </button>
              </div>
            )}
          </div>
        </>
      )}

{loading && (
  <div className="text-center">
    <img 
      src="/1488.gif" 
      alt="Loading..." 
      style={{ width: '50px', height: '50px' }} 
    />
  </div>
)}



      {error && <div className="alert alert-danger" role="alert">{error}</div>}

     {/* Display search results */}
{Array.isArray(searchResults) && searchResults.length > 0 && (
  <div>
    <h2 className='recommendation-title'>Search Results</h2>
    <div className="row">
      {searchResults.map((product, index) => (
        <div key={index} className="col-md-4 mb-4">
          <div className="card">
            <img
              src={product.image_url && product.image_url !== 'NaN' ? product.image_url : "https://i.pngimg.me/thumb/f/720/m2i8K9m2K9A0i8N4.jpg"}
              className="card-img-top"
              alt={product.image_url ? "Product image" : product.title}
              onError={(e) => {
                e.target.src = "https://i.pngimg.me/thumb/f/720/m2i8K9m2K9A0i8N4.jpg";
                e.target.alt = product.title;
              }}
            />
            <h5 className="card-title" title={product.title}>{product.title}</h5>
            <p className="card-text" title={product.top_review}>
              {product.top_review.substring(0, 100)}{product.top_review.length > 100 && '...'}
            </p>
            <p className="card-text">Rating: {product.rating}</p>
            <p className="card-text">Product Price: {product.initial_price}</p>
            <p className="card-text">Categories:</p>
            <ul>
              {product.category && product.category.length > 0 ? product.category.map((cat, idx) => (
                <li key={idx}>{cat}</li>
              )) : <li>No categories available</li>}
            </ul>
            <a href={product.url} className="btn btn-primary" target="_blank" rel="noopener noreferrer">
              View Product
            </a>
          </div>
        </div>
      ))}
    </div>
  </div>
)}

{/* Display recommended products based on sentiment */}
{Array.isArray(recommendations) && recommendations.length > 0 && (
  <div>
    <h2 class="recommendation-title">Most Recommended Product Based On Review Sentiment and Rating</h2>
    <div className="row">
      {recommendations.map((product, index) => {
        // Log product category before parsing
        console.log("Product category (before parse):", product.category);

        // Safely parse categories and handle NaN or invalid values
        let categories = [];
        try {
          // Check if the category is valid and can be parsed
          categories = product.category && product.category !== "NaN" ? JSON.parse(product.category) : [];
        } catch (error) {
          console.error("Error parsing category:", error);
          categories = [];  // Fallback to empty array in case of parse error
        }

        // Log parsed categories
        console.log("Parsed categories:", categories);

        // Handle invalid image_url (e.g., NaN or empty)
        const imageUrl = product.image_url && product.image_url !== "NaN" ? product.image_url : "https://i.pngimg.me/thumb/f/720/m2i8K9m2K9A0i8N4.jpg";

        return (
          <div key={index} className="col-md-6 mb-6">
            <div className="card">
              <img
                src={imageUrl}
                className="card-img-top"
                alt={imageUrl !== "https://i.pngimg.me/thumb/f/720/m2i8K9m2K9A0i8N4.jpg" ? "Product image" : product.title}
                onError={(e) => {
                  // Default image on error or if image_url is invalid
                  e.target.src = "https://i.pngimg.me/thumb/f/720/m2i8K9m2K9A0i8N4.jpg";
                  e.target.alt = product.title;
                }}
              />
              <h5 className="card-title" title={product.title}>{product.title}</h5>
              <p className="card-text">Categories:</p>
              <ul>
                {categories.length > 0 ? categories.map((cat, idx) => (
                  <li key={idx}>{cat}</li>
                )) : <li>No categories available</li>}
              </ul>
              <p className="card-text">Sentiment Score: {product.sentiment_score}</p>
              <p className="card-text">Product Price: {product.initial_price}</p>
              <p className="card-text">Rating: {product.rating}</p>
              <a href={product.url} className="btn btn-primary" target="_blank" rel="noopener noreferrer">
                View Product
              </a>
            </div>
          </div>
        );
      })}
    </div>
  </div>
)}



      {Array.isArray(imageSearchResults) && imageSearchResults.length > 0 && (
        <div>
          <h2>Image-Based Search Results</h2>
          <div className="row">
            {imageSearchResults.map((product, index) => (
              <div key={index} className="col-md-8 mb-4">
                <div className="card">
                  <img
                    src={product.image_url || "https://i.pngimg.me/thumb/f/720/m2i8K9m2K9A0i8N4.jpg"}
                    className="card-img-top"
                    alt={product.image_url ? "Product image" : product.title}
                    onError={(e) => {
                      e.target.src = "https://i.pngimg.me/thumb/f/720/m2i8K9m2K9A0i8N4.jpg";
                      e.target.alt = product.title;
                    }}
                  />
                  <h5 className="cardimage-title" title={product.title}>{product.title}</h5>
              <p className="card-text">Sentiment Score: {product.sentiment_score}</p>
              <p className="card-text">Product Price: {product.initial_price}</p>
              <p className="cardimage-text">Top Review: {product.top_review}</p>
                  <a href={product.url} className="btn btn-primary" target="_blank" rel="noopener noreferrer">
                    View Product
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

{orderStatus && (
  <div className="card" style={{ backgroundColor: '#A0E0D9', width: '80%', margin: '20px auto' }}> {/* Lighter Turquoise Blue */}
    <div className="card-body">
      <h2 className="card-title" style={{ backgroundColor: '#FFFFFF', textAlign: 'center' }}>
        Order Status
      </h2>
      <div className="row" style={{ display: 'flex', justifyContent: 'center', textAlign: 'center' }}>
        <div className="col-md-12">
          <p style={{ fontSize: '18px' }}>Order Number: {orderStatus.order_no}</p>
          <p style={{ fontSize: '18px' }}>Status: {orderStatus.order_status}</p>
          <p style={{ fontSize: '18px' }}>Date of Order: {orderStatus.order_date}</p>
          <p style={{ fontSize: '18px' }}>Current Location: {orderStatus.current_location}</p>
          <p style={{ fontSize: '18px' }}>Shipping Address: {orderStatus.ship_state}</p>
          <p style={{ fontSize: '18px' }}>Delivery/Expected Date of delivery: {orderStatus.delivery_date}</p>

        </div>
      </div>
    </div>
  </div>
)}




    </div>
  );
}

export default App;
