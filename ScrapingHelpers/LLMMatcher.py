import os
import pandas as pd
import json
import time
from datetime import timedelta
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")

# Initialize Azure OpenAI client
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,  
    api_version=AZURE_OPENAI_API_VERSION,
    azure_endpoint=AZURE_OPENAI_ENDPOINT
)

ACCIDENTS_FILE = 'CleanedForScrapingNews.xlsx'
POSTS_DIR = 'cleanedStandardizedPosts'
OUTPUT_DIR = 'matched_results'

# List of stations to skip
STATIONS_TO_SKIP = [
     "GRS BOHINJ",
     "GRS BOVEC"
]

def find_post_file(postaja_name, directory):
    if not os.path.exists(directory):
        print(f"Directory {directory} does not exist.")
        return []

    found_files = []
    
    # Always check for grzs.xlsx
    grzs_path = os.path.join(directory, 'grzs.xlsx')
    if os.path.exists(grzs_path):
        found_files.append(grzs_path)

    files = [f for f in os.listdir(directory) if f.endswith('.xlsx') and f.lower() != 'grzs.xlsx']
    
    # Normalize names for comparison
    normalized_postaja = postaja_name.lower().replace('grs', '').replace(' ', '').replace('_', '').replace('-', '')
    
    for f in files:
        normalized_filename = f.lower().replace('.xlsx', '').replace(' ', '').replace('_', '').replace('-', '')
        # Check for exact match or containment
        if normalized_postaja and (normalized_postaja in normalized_filename or normalized_filename in normalized_postaja):
            found_files.append(os.path.join(directory, f))
            
    return found_files

def call_llm_matcher(accident_info, candidate_posts):
    posts_text = []
    for idx, row in candidate_posts.iterrows():
        # Assuming 'Vsebina' is the content column, and we might want the date too
        content = row.get('Vsebina', '')
        date = row.get('datum', '')
        posts_text.append(f"Date: {date}\nContent: {content}\n---")
    
    posts_context = "\n".join(posts_text)
    
    prompt = f"""
You are an expert investigator. Your task is to match a mountain accident report to a specific post describing it.
 
Accident Details:
{json.dumps(accident_info, default=str, indent=2)}

Candidate Posts (from nearby dates):
{posts_context}

Task:
1. Identify which Candidate Post best matches the Accident Details using the provided information. If none match well, leave values null.
2. From the matched post (or the accident details if implied), extract:
   - Location of the accident (be specific, e.g., mountain name, peak, valley. Do NOT use the rescue station name like 'GRS Bohinj').
   - Route taken (if mentioned).
   - Possible ages of the participants (if mentioned).
If no match is found, return nulls for all fields.

Output Format:
Use slovene when outputting the JSON.
Provide a JSON object with the following keys:
- "Lokacija": "Extracted specific location (not station name)",
- "Pot": "Extracted route",
- "starost_udelezencev": "Extracted ages (e.g., '45, 52')"

Return ONLY the JSON.
"""

    try:
        response = client.chat.completions.create(
            model=AZURE_OPENAI_DEPLOYMENT_NAME, 
            messages=[
                {"role": "system", "content": "You are a helpful assistant that outputs JSON."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        if response.usage:
            print(f"Token usage: Prompt: {response.usage.prompt_tokens}, Completion: {response.usage.completion_tokens}, Total: {response.usage.total_tokens}")
        
        content = response.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"Error calling LLM: {e}")
        return None

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"Loading accidents from {ACCIDENTS_FILE}...")
    try:
        accidents_df = pd.read_excel(ACCIDENTS_FILE)
    except FileNotFoundError:
        print(f"Error: {ACCIDENTS_FILE} not found.")
        return

    # Ensure Datum is datetime
    accidents_df['Datum'] = pd.to_datetime(accidents_df['Datum'])

    # Group by Postaja to process each station's file once
    grouped = accidents_df.groupby('Postaja')

    for postaja, group in grouped:
        if postaja in STATIONS_TO_SKIP:
            print(f"Skipping station: {postaja}")
            continue

        print(f"Processing station: {postaja}")
        
        post_files = find_post_file(str(postaja), POSTS_DIR)
        
        if not post_files:
            print(f"  No matching files found for station: {postaja}")
            continue
            
        print(f"  Found posts files: {post_files}")
        
        dfs = []
        for post_file_path in post_files:
            try:
                df = pd.read_excel(post_file_path)
                
                # Normalize date column
                if 'datum' in df.columns:
                    df.rename(columns={'datum': 'Datum'}, inplace=True)
                
                if 'Datum' in df.columns:
                    df['Datum'] = pd.to_datetime(df['Datum'])
                    dfs.append(df)
                else:
                    print(f"  Date column not found in {post_file_path}. Skipping.")
                
            except Exception as e:
                print(f"  Error reading {post_file_path}: {e}")
                continue

        if not dfs:
            continue

        posts_df = pd.concat(dfs, ignore_index=True)
        date_col = 'Datum'

        results = []

        for idx, accident in group.iterrows():
            accident_date = accident['Datum']
            
            # Filter posts + 1 day
            start_date = accident_date #- timedelta(days=1)
            end_date = accident_date + timedelta(days=1)
            
            candidate_posts = posts_df[
                (posts_df[date_col] >= start_date) & 
                (posts_df[date_col] <= end_date)
            ]
            
            if candidate_posts.empty:
                continue
            
            accident_info = accident.to_dict()
            print(f"  Matching accident on {accident_date} with {len(candidate_posts)} candidate posts...")
            llm_result = call_llm_matcher(accident_info, candidate_posts)
            
            if llm_result:
                res = accident.to_dict()
                print("llm result:", llm_result)
                if llm_result.get("Lokacija") is not None:
                    res.update(llm_result)
                    results.append(res)
                    print(res)
            else:
                print("  LLM failed to return result.")
                res = accident.to_dict()
                results.append(res)

            time.sleep(1)
        # Save results for this station
        if results:
            output_filename = f"Matched_{str(postaja).replace(' ', '_')}.xlsx"
            output_path = os.path.join(OUTPUT_DIR, output_filename)
            pd.DataFrame(results).to_excel(output_path, index=False)
            print(f"  Saved results to {output_path}")

if __name__ == "__main__":
    main()
