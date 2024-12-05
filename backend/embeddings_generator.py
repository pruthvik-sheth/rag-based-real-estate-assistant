import pandas as pd
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from tqdm import tqdm
import numpy as np
import time
import argparse
import os
import ast
from typing import List, Dict

class PropertyEmbeddingsUploader:
    def __init__(self, 
                 pinecone_api_key: str,
                 index_name: str,
                 batch_size: int = 100):
        
        print("Loading embedding model...")
        self.model = SentenceTransformer('intfloat/e5-large-v2')
        self.batch_size = batch_size
        
        print("Initializing Pinecone...")
        self.pc = Pinecone(api_key=pinecone_api_key)
        
        if index_name not in self.pc.list_indexes().names():
            print(f"Creating new index: {index_name}")
            self.pc.create_index(
                name=index_name,
                dimension=self.model.get_sentence_embedding_dimension(),
                metric='cosine',
                spec=ServerlessSpec(
                    cloud='aws',
                    region='us-east-1'
                )
            )
        
        self.index = self.pc.Index(index_name)

    def parse_list_field(self, field):
        """Safely parse list fields from the CSV"""
        if pd.isna(field):
            return []
        try:
            if isinstance(field, str):
                return ast.literal_eval(field)
            return field
        except:
            return []

    def prepare_metadata(self, row: pd.Series) -> Dict:
        """Prepare metadata for a property"""
        # Parse amenities and nearby facilities
        amenities = self.parse_list_field(row['amenities'])
        nearby_amenities = self.parse_list_field(row['nearby_amenities'])
        
        # Parse images if it's a string
        images = row['images'] if pd.notna(row['images']) else ""
        
        return {
            'property_id': str(row['rea_property_id']),
            'property_type': str(row['property_type']),
            'suburb': str(row['suburb']),
            'state': str(row['state']),
            'postcode': str(row['postcode']) if pd.notna(row['postcode']) else '',
            'bedrooms': int(row['bedrooms']) if pd.notna(row['bedrooms']) else 0,
            'bathrooms': int(row['bathrooms']) if pd.notna(row['bathrooms']) else 0,
            'price': float(row['price']),
            'url': str(row['url']),
            'street_address': str(row['street_address']),
            'year_built': str(row['year_built']) if pd.notna(row['year_built']) else '',
            'land_size': str(row['land_size']) if pd.notna(row['land_size']) else '',
            'floor_area': str(row['floor_area']) if pd.notna(row['floor_area']) else '',
            'amenities': amenities,
            'nearby_amenities': nearby_amenities,
            'description': str(row['description']),
            'images': images
        }

    def generate_embeddings(self, descriptions: List[str]) -> np.ndarray:
        """Generate embeddings for a list of descriptions"""
        # Create enhanced descriptions including amenities and location
        enhanced_descriptions = []
        for desc in descriptions:
            enhanced_desc = f"query: {desc}"
            enhanced_descriptions.append(enhanced_desc)
        return self.model.encode(enhanced_descriptions, normalize_embeddings=True)
    
    def upsert_batch(self, batch_df: pd.DataFrame, embeddings: np.ndarray) -> bool:
        """Upsert a batch of vectors to Pinecone"""
        try:
            vectors = []
            for idx, (_, row) in enumerate(batch_df.iterrows()):
                vectors.append((
                    str(row['rea_property_id']),
                    embeddings[idx].tolist(),
                    self.prepare_metadata(row)
                ))
            
            self.index.upsert(vectors=vectors)
            return True
        except Exception as e:
            print(f"Error upserting batch: {str(e)}")
            return False

    def process_dataset(self, df: pd.DataFrame) -> int:
        """Process entire dataset in batches"""
        successful_uploads = 0
        
        # Create batches
        num_batches = (len(df) + self.batch_size - 1) // self.batch_size
        print(f"Processing {len(df)} properties in {num_batches} batches...")
        
        for start_idx in tqdm(range(0, len(df), self.batch_size)):
            # Get batch
            end_idx = min(start_idx + self.batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx]
            
            try:
                # Generate embeddings for current batch
                batch_descriptions = batch_df['description'].tolist()
                batch_embeddings = self.generate_embeddings(batch_descriptions)
                
                # Upsert the batch
                if self.upsert_batch(batch_df, batch_embeddings):
                    successful_uploads += len(batch_df)
                
                # Add delay between batches
                time.sleep(0.5)
                
            except Exception as e:
                print(f"Error processing batch {start_idx//self.batch_size}: {str(e)}")
                continue
        
        return successful_uploads

def main():
    parser = argparse.ArgumentParser(description='Upload property embeddings to Pinecone')
    parser.add_argument('--input', required=True, help='Input CSV file with descriptions')
    parser.add_argument('--pinecone-key', required=True, help='Pinecone API key')
    parser.add_argument('--index-name', required=True, help='Pinecone index name')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    # Initialize uploader
    uploader = PropertyEmbeddingsUploader(
        pinecone_api_key=args.pinecone_key,
        index_name=args.index_name,
        batch_size=args.batch_size
    )
    
    try:
        successful_uploads = uploader.process_dataset(df)
        print(f"\nSuccessfully uploaded {successful_uploads} out of {len(df)} properties to Pinecone")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()