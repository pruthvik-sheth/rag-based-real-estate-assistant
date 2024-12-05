import pandas as pd
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from tqdm import tqdm
import time
import os
import argparse
import ast

import warnings
warnings.simplefilter("ignore")

class PropertyDescriptionGenerator:
    def __init__(self, model_name="llama3.2:3b", save_interval=10):
        self.save_interval = save_interval
        self.llm = Ollama(model=model_name)
        
        self.prompt_template = PromptTemplate(
            input_variables=[
                "property_type", "bedrooms", "bathrooms", "suburb", "state", "postcode",
                "year_built", "land_size", "floor_area", "price", "amenities", "nearby_amenities"
            ],
            template="""
            Act as a professional real estate agent and write a detailed, engaging description for the following property:

            Property Details:
            - Type: {property_type}
            - Location: {suburb}, {state} {postcode}
            - Bedrooms: {bedrooms}
            - Bathrooms: {bathrooms}
            - Year Built: {year_built}
            - Land Size: {land_size}
            - Floor Area: {floor_area}
            - Price: ${price:,.2f}

            Features and Amenities:
            {amenities}

            Nearby Facilities:
            {nearby_amenities}

            Please write a natural, engaging description that highlights the property's key features, location benefits, 
            amenities, and potential. Focus on making it informative and appealing to potential buyers or renters.
            Emphasize both the property's features and its surrounding conveniences.
            Keep the description between 100-150 words.
            """
        )
        
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)
    
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

    def generate_single_description(self, row):
        try:
            # Parse amenities and nearby facilities
            amenities = self.parse_list_field(row["amenities"])
            nearby = self.parse_list_field(row["nearby_amenities"])

            # Format amenities and nearby facilities for the prompt
            amenities_text = "- " + "\n- ".join(amenities) if amenities else "No specific amenities listed"
            nearby_text = "- " + "\n- ".join(nearby) if nearby else "No specific nearby facilities listed"

            input_vars = {
                "property_type": row["property_type"],
                "bedrooms": row["bedrooms"],
                "bathrooms": row["bathrooms"],
                "suburb": row["suburb"],
                "state": row["state"],
                "postcode": row["postcode"] if pd.notna(row["postcode"]) else "",
                "year_built": row["year_built"] if pd.notna(row["year_built"]) else "Not specified",
                "land_size": row["land_size"] if pd.notna(row["land_size"]) else "Not specified",
                "floor_area": row["floor_area"] if pd.notna(row["floor_area"]) else "Not specified",
                "price": float(row["price"]),
                "amenities": amenities_text,
                "nearby_amenities": nearby_text
            }
            
            description = self.chain.run(**input_vars)
            return description.strip()
            
        except Exception as e:
            print(f"Error generating description for property at index {row.name}: {str(e)}")
            return "Description generation failed"

    def save_progress(self, df_slice, descriptions, output_path, current_index, start_row, end_row):
        """Save the current progress with range information"""
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"properties_descriptions_{start_row}_to_{end_row}_progress_{timestamp}.csv"
        
        if output_path:
            filename = os.path.join(output_path, filename)
        
        # Create a copy of the slice and add descriptions
        df_to_save = df_slice.copy()
        df_to_save['description'] = descriptions
            
        df_to_save.to_csv(filename, index=False)
        print(f"\nProgress saved at index {current_index}. File: {filename}")

    def generate_descriptions_for_range(self, df, start_row, end_row, output_path=None):
        """Generate descriptions for a specific range of rows"""
        if output_path and not os.path.exists(output_path):
            os.makedirs(output_path)
            
        # Validate row ranges
        start_row = max(0, start_row)
        end_row = min(len(df), end_row)
        
        if start_row >= end_row:
            raise ValueError("Start row must be less than end row")
            
        print(f"Processing rows {start_row} to {end_row} (Total: {end_row - start_row} rows)")
        
        # Create a copy of the dataframe slice we'll be working with
        working_df = df.iloc[start_row:end_row].copy()
        descriptions = []
        
        for idx, row in tqdm(working_df.iterrows(), total=len(working_df)):
            description = self.generate_single_description(row)
            descriptions.append(description)
            
            # Save at intervals
            if len(descriptions) % self.save_interval == 0:
                self.save_progress(
                    working_df.iloc[:len(descriptions)],
                    descriptions,
                    output_path,
                    start_row + len(descriptions),
                    start_row,
                    end_row
                )
            
            time.sleep(0.5)
        
        # Final save if needed
        if len(descriptions) % self.save_interval != 0:
            self.save_progress(
                working_df,
                descriptions,
                output_path,
                start_row + len(descriptions),
                start_row,
                end_row
            )
        
        # Add descriptions to the working DataFrame
        working_df['description'] = descriptions
        return working_df

def main():
    parser = argparse.ArgumentParser(description='Generate property descriptions for a range of rows')
    parser.add_argument('--input', required=True, help='Input CSV file path')
    parser.add_argument('--output-dir', required=True, help='Output directory for generated descriptions')
    parser.add_argument('--start-row', type=int, required=True, help='Starting row index')
    parser.add_argument('--end-row', type=int, required=True, help='Ending row index')
    parser.add_argument('--save-interval', type=int, default=20, help='Save progress every N rows')
    
    args = parser.parse_args()
    
    print(f"Loading data from {args.input}")
    df = pd.read_csv(args.input)
    
    generator = PropertyDescriptionGenerator(save_interval=args.save_interval)
    
    try:
        result_df = generator.generate_descriptions_for_range(
            df,
            args.start_row,
            args.end_row,
            args.output_dir
        )
        
        # Save final results for this range
        final_output = os.path.join(
            args.output_dir,
            f"properties_descriptions_{args.start_row}_to_{args.end_row}_final.csv"
        )
        result_df.to_csv(final_output, index=False)
        print(f"\nCompleted! Final dataset saved to {final_output}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")

if __name__ == "__main__":
    main()