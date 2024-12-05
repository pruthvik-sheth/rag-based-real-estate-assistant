from flask import Flask, request, jsonify
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama
from typing import List, Dict
import os
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get environment variables
PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
PINECONE_INDEX_NAME = os.getenv('PINECONE_INDEX_NAME')

app = Flask(__name__)
CORS(app)

class RealEstateAssistant:
    def __init__(self, pinecone_api_key: str, index_name: str):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index = self.pc.Index(index_name)
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer('intfloat/e5-large-v2')
        
        # Initialize Llama
        self.llm = Ollama(model="llama3.2:3b")
        
    def get_relevant_properties(self, query: str, top_k: int = 5) -> List[Dict]:
        """Get relevant properties based on the query"""
        # Generate embedding for the query
        query_embedding = self.embedding_model.encode(f"query: {query}", normalize_embeddings=True)
        
        # Query Pinecone
        results = self.index.query(
            vector=query_embedding.tolist(),
            top_k=top_k,
            include_metadata=True
        )
        
        return results.matches
    
    def format_properties_context(self, properties: List[Dict]) -> str:
        """Format properties into a context string for the LLM"""
        context = "Here are the relevant properties:\n\n"
        
        for i, match in enumerate(properties, 1):
            prop = match.metadata
            context += f"Property {i}:\n"
            context += f"- Type: {prop['property_type']}\n"
            context += f"- Location: {prop['street_address']}, {prop['suburb']}, {prop['state']} {prop['postcode']}\n"
            context += f"- Bedrooms: {prop['bedrooms']}\n"
            context += f"- Bathrooms: {prop['bathrooms']}\n"
            context += f"- Year Built: {prop['year_built']}\n"
            context += f"- Land Size: {prop['land_size']}\n"
            context += f"- Floor Area: {prop['floor_area']}\n"
            context += f"- Price: ${float(prop['price']):,.2f}\n"
            
            # Add amenities if available
            if 'amenities' in prop and prop['amenities']:
                context += f"- Amenities: {', '.join(prop['amenities'])}\n"
            
            # Add nearby amenities if available
            if 'nearby_amenities' in prop and prop['nearby_amenities']:
                context += f"- Nearby: {', '.join(prop['nearby_amenities'])}\n"
            
            # Add property description if available
            if 'description' in prop:
                context += f"- Description: {prop['description']}\n"
            
            context += f"- URL: {prop['url']}\n\n"
        
        return context

    def generate_prompt(self, query: str, properties: List[Dict]) -> str:
        """Generate a prompt for the LLM"""
        context = self.format_properties_context(properties)
        
        prompt = f"""You are a knowledgeable Australian real estate assistant. Based on the following properties and the user's query, 
        provide a helpful and informative response. Include specific details from the properties when relevant.

        User Query: {query}

        Available Property Information:
        {context}

        Please provide a detailed response that:
        1. Directly addresses the user's query
        2. References specific properties and their features when relevant
        3. Highlights relevant amenities and nearby facilities
        4. Compares properties when appropriate
        5. Mentions specific suburbs and locations
        6. Discusses prices and value propositions
        7. Considers property features like land size and year built when relevant

        Format your response in a natural, conversational way while maintaining professionalism.
        Include specific property details to support your recommendations.

        Your output should be well structured and easy to read, with clear and concise language.

        Response:"""
        
        return prompt

    def process_query(self, user_query: str, top_k: int = 5) -> Dict:
        """Process query and return both LLM response and property metadata"""
        try:
            # Get relevant properties
            matches = self.get_relevant_properties(user_query, top_k)
            
            if not matches:
                return {
                    "success": True,
                    "response": "I couldn't find any relevant properties matching your query.",
                    "properties": []
                }
            
            # Generate prompt with context
            prompt = self.generate_prompt(user_query, matches)
            
            # Get response from LLM
            llm_response = self.llm.invoke(prompt)
            
            # Extract metadata from matches
            properties = []
            for match in matches:
                property_data = match.metadata
                property_data['score'] = match.score
                properties.append(property_data)
            
            return {
                "success": True,
                "response": llm_response,
                "properties": properties
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "An error occurred while processing your query.",
                "properties": []
            }

# Validate environment variables
if not PINECONE_API_KEY or not PINECONE_INDEX_NAME:
    raise ValueError("Missing required environment variables. Please check your .env file.")

# Initialize the assistant
try:
    assistant = RealEstateAssistant(
        pinecone_api_key=PINECONE_API_KEY,
        index_name=PINECONE_INDEX_NAME
    )
except Exception as e:
    print(f"Error initializing RealEstateAssistant: {str(e)}")
    raise

@app.route('/api/query', methods=['POST'])
def query_properties():
    try:
        data = request.get_json()
        user_query = data.get('query')
        top_k = data.get('top_k', 5)
        
        if not user_query:
            return jsonify({
                "success": False,
                "error": "No query provided"
            }), 400
        
        result = assistant.process_query(user_query, top_k)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "message": "Real Estate Assistant API is running"
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)