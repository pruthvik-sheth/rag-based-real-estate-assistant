from pinecone import Pinecone

def quick_delete_all_vectors(api_key: str, index_name: str):
    pc = Pinecone(api_key=api_key)
    index = pc.Index(index_name)
    
    # Delete all vectors at once
    index.delete(delete_all=True)
    print("All vectors deleted successfully")

# Usage
api_key = ""
index_name = "real-estate-descriptions"
quick_delete_all_vectors(api_key, index_name)