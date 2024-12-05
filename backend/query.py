from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from langchain_community.llms import Ollama
from typing import List, Dict
import ast
import pandas as pd

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

        print(results)
        
        return [match.metadata for match in results.matches]
    
    def format_properties_context(self, properties: List[Dict]) -> str:
        """Format properties into a context string for the LLM"""
        context = "Here are the relevant properties:\n\n"
        
        for i, prop in enumerate(properties, 1):
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
            amenities = prop.get('amenities', [])
            if amenities:
                if isinstance(amenities, str):
                    try:
                        amenities = ast.literal_eval(amenities)
                    except:
                        amenities = []
                context += f"- Amenities: {', '.join(amenities)}\n"
            
            # Add nearby amenities if available
            nearby = prop.get('nearby_amenities', [])
            if nearby:
                if isinstance(nearby, str):
                    try:
                        nearby = ast.literal_eval(nearby)
                    except:
                        nearby = []
                context += f"- Nearby: {', '.join(nearby)}\n"
            
            # Add property description
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

        Response:"""
        
        return prompt

    def answer_query(self, user_query: str, top_k: int = 5) -> str:
        """Main method to answer user queries"""
        try:
            # Get relevant properties
            relevant_properties = self.get_relevant_properties(user_query, top_k)
            
            if not relevant_properties:
                return "I couldn't find any relevant properties matching your query."
            
            # Generate prompt with context
            prompt = self.generate_prompt(user_query, relevant_properties)
            
            # Get response from LLM
            response = self.llm.invoke(prompt)
            
            return response
            
        except Exception as e:
            return f"An error occurred while processing your query: {str(e)}"

def main():
    api_key = "pcsk_5uU8T3_KakXgiejJDfQ26a93nLw8zfw9JEGmkAwsGY1iyURGerH8GLTBBTPpLHuNiKjH11"
    index_name = "real-estate-descriptions"
    
    assistant = RealEstateAssistant(api_key, index_name)
    
    # Example queries that leverage the new dataset structure
    example_queries = [
        "Show properties with highest land size",
        # "Show me 3BHK properties in Sydney with a pool",
        # "Show me properties with modern amenities like air conditioning and built-in robes",
        # "Find family homes near schools and parks with at least 3 bedrooms",
        # "What properties have good investment potential based on location and features?",
        # "Show me properties built after 2000 with large land size",
        # "Find homes with luxury features like pools and spas",
        # "What properties are available near public transport and shopping centers?",
    ]
    
    for query in example_queries:
        print(f"\nQuery: {query}")
        print("Response:", assistant.answer_query(query))
        print("-" * 80)

if __name__ == "__main__":
    main()