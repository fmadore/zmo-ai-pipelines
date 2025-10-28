"""Unified Summary and Keywords Generation (Gemini or OpenAI)

Generates summaries with keywords for all .txt files in TXT/ and writes them to Summaries_TXT/.
User selects provider interactively:
  1) OpenAI Responses API (model: gpt-5-mini)
  2) Google Gemini (model: gemini-2.5-flash)

OpenAI path uses the EXACT required responses.create structure (only the input list contents vary).
Gemini path uses google-genai SDK with GenerateContent.
"""

import os
import json
import logging
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
import pandas as pd

from google import genai
from google.genai import types, errors

try:  # OpenAI optional import
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

# ------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

GEMINI_MODEL = "gemini-2.5-flash"
OPENAI_MODEL = "gpt-5-mini"
PROVIDER_OPENAI = "openai"
PROVIDER_GEMINI = "gemini"

# ------------------------------------------------------------------
# Prompt Loading
# ------------------------------------------------------------------
def load_prompt_template() -> str:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_file = os.path.join(script_dir, 'summary_prompt.md')
    try:
        with open(prompt_file, 'r', encoding='utf-8') as f:
            content = f.read()
        if '{text}' not in content:
            logging.warning("Prompt template missing '{text}' placeholder.")
        return content
    except FileNotFoundError:
        raise FileNotFoundError(f"Prompt template not found: {prompt_file}")
    except Exception as e:
        raise RuntimeError(f"Failed to read prompt template {prompt_file}: {e}")

PROMPT_TEMPLATE = load_prompt_template()

# ------------------------------------------------------------------
# Client Initialization
# ------------------------------------------------------------------
def initialize_gemini_client():
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    client = None
    auth_method = "API Key"
    if credentials_path and os.path.exists(credentials_path):
        try:
            client = genai.Client()
            auth_method = "ADC"
            logging.info("Gemini client initialized via ADC.")
        except Exception as e:
            logging.warning(f"ADC init failed: {e}; falling back to API key.")
            client = None
    if client is None:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY not set and ADC not available.")
        client = genai.Client(api_key=api_key)
        logging.info("Gemini client initialized via API key.")
    logging.info(f"Using Gemini model: {GEMINI_MODEL} ({auth_method})")
    return client

def initialize_openai_client() -> Optional[object]:
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logging.error("OPENAI_API_KEY not set.")
        return None
    if OpenAI is None:
        logging.error("openai package not installed.")
        return None
    logging.info(f"Using OpenAI model: {OPENAI_MODEL}")
    return OpenAI()

# ------------------------------------------------------------------
# Generation Functions
# ------------------------------------------------------------------
def generate_summary_openai(client, text: str) -> Optional[str]:
    if not text.strip():
        return None
    system_prompt = PROMPT_TEMPLATE
    user_prompt = system_prompt.format(text=text)
    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            text={
                "format": {"type": "text"},
                "verbosity": "low"
            },
            reasoning={"effort": "low"},
            tools=[],
            store=True
        )
        raw_output = getattr(response, 'output_text', None)
        if not raw_output:
            segments = []
            for seg in getattr(response, 'output', []) or []:
                if isinstance(seg, dict):
                    c = seg.get('content')
                    if isinstance(c, str):
                        segments.append(c)
            raw_output = '\n'.join(filter(None, segments))
        return raw_output.strip() if raw_output else None
    except Exception as e:
        logging.error(f"OpenAI summary error: {e}")
        return None

def generate_summary_gemini(client, text: str) -> Optional[str]:
    if not text.strip():
        return None
    prompt = PROMPT_TEMPLATE.format(text=text)
    try:
        gen_config = types.GenerateContentConfig(temperature=0.2)
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=gen_config
        )
        if response and hasattr(response, 'text'):
            return response.text.strip().replace('*', '')
        logging.error("Unexpected Gemini response format.")
        return None
    except errors.APIError as e:
        logging.error(f"Gemini API error: {e}")
        return None
    except Exception as e:
        logging.error(f"Gemini summary error: {e}")
        return None

# ------------------------------------------------------------------
# File Processing
# ------------------------------------------------------------------
def process_file(provider: str, client, input_file_path: str, output_file_path: str):
    try:
        with open(input_file_path, 'r', encoding='utf-8') as infile:
            original_text = infile.read()
        if not original_text.strip():
            logging.warning(f"Empty file skipped: {input_file_path}")
            return
        logging.info(f"Summarizing: {os.path.basename(input_file_path)}")
        if provider == PROVIDER_GEMINI:
            summary = generate_summary_gemini(client, original_text)
        else:
            summary = generate_summary_openai(client, original_text)
        if summary:
            with open(output_file_path, 'w', encoding='utf-8') as out:
                out.write(summary)
            logging.info(f"Saved: {os.path.basename(output_file_path)}")
        else:
            logging.error(f"No summary produced for {input_file_path}")
    except FileNotFoundError:
        logging.error(f"File not found: {input_file_path}")
    except IOError as e:
        logging.error(f"IO error {input_file_path}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error {input_file_path}: {e}")

def process_txt_files(provider: str, client, input_dir: str, output_dir: str):
    if not os.path.exists(input_dir):
        logging.error(f"Input dir not found: {input_dir}")
        return
    os.makedirs(output_dir, exist_ok=True)
    txt_files = [f for f in os.listdir(input_dir) if f.endswith('.txt')]
    if not txt_files:
        logging.warning("No .txt files to process.")
        return
    logging.info(f"Processing {len(txt_files)} files -> {output_dir}")
    for fname in tqdm(txt_files, desc="Generating Summaries"):
        process_file(provider,
                     client,
                     os.path.join(input_dir, fname),
                     os.path.join(output_dir, fname))
    logging.info("Batch complete.")

# ------------------------------------------------------------------
# Spreadsheet Processing
# ------------------------------------------------------------------
def extract_keywords_from_summary(summary_text: str) -> tuple[str, str]:
    """
    Extract keywords from the summary text and return cleaned summary + keywords.
    
    The summary typically includes keywords at the end. This function extracts them,
    removes them from the summary, and formats them as pipe-separated values.
    
    Args:
        summary_text (str): The full summary text with keywords
        
    Returns:
        tuple: (cleaned_summary, pipe_separated_keywords)
    """
    if not summary_text:
        return ("", "")
    
    # Look for common keyword indicators
    keyword_indicators = [
        "Keywords:",
        "Mots-clés:",
        "Key words:",
        "Tags:",
        "الكلمات المفتاحية:",
    ]
    
    cleaned_summary = summary_text
    keywords = ""
    
    for indicator in keyword_indicators:
        if indicator in summary_text:
            # Split at the keyword indicator
            parts = summary_text.split(indicator)
            if len(parts) > 1:
                # Everything before the indicator is the summary
                cleaned_summary = parts[0].strip()
                
                # Everything after is the keywords
                keyword_section = parts[-1].strip()
                
                # Extract keywords (they might be comma-separated or newline-separated)
                # Remove any leading numbers, bullets, or dashes
                import re
                # Replace commas and newlines with pipes
                keywords = re.sub(r'[\n,;]', '|', keyword_section)
                # Clean up multiple pipes and whitespace
                keywords = re.sub(r'\s*\|\s*', ' | ', keywords)
                keywords = re.sub(r'\s+', ' ', keywords)
                # Remove any leading/trailing pipes
                keywords = keywords.strip(' |')
                # Remove bullet points, numbers, dashes
                keywords = re.sub(r'[•\-\d\.]+\s*', '', keywords)
                keywords = keywords.strip()
                
                break
    
    return (cleaned_summary, keywords)

def find_excel_file(directory: Path) -> Optional[Path]:
    """
    Check if there's an Excel file in the specified directory.
    
    Args:
        directory (Path): Directory to search for Excel files
        
    Returns:
        Optional[Path]: Path to the first Excel file found, or None
    """
    excel_extensions = ['*.xlsx', '*.xls']
    
    for pattern in excel_extensions:
        excel_files = list(directory.glob(pattern))
        if excel_files:
            return excel_files[0]  # Return the first Excel file found
    
    return None

def process_with_spreadsheet(provider: str, client, excel_path: Path) -> None:
    """
    Process summaries based on OCR text in an Excel spreadsheet.
    
    Reads the 'OCR' column from the spreadsheet, generates summaries,
    and writes the results back to a new 'Summary' column.
    
    Args:
        provider (str): AI provider ('openai' or 'gemini')
        client: Initialized AI client
        excel_path (Path): Path to the Excel spreadsheet
    """
    print("\n" + "="*60)
    print("📊 SPREADSHEET MODE")
    print("="*60)
    print(f"📁 Excel file: {excel_path.name}")
    print("="*60 + "\n")
    
    try:
        # Read the Excel file
        print("📖 Reading Excel spreadsheet...")
        df = pd.read_excel(excel_path)
        
        # Check if 'OCR' column exists
        if 'OCR' not in df.columns:
            print("❌ Error: 'OCR' column not found in spreadsheet!")
            print(f"   Available columns: {list(df.columns)}")
            logging.error(f"'OCR' column not found in {excel_path}. Available: {list(df.columns)}")
            return
        
        print(f"✅ Found {len(df)} rows in spreadsheet")
        
        # Add Summary and Keywords columns if they don't exist
        if 'Summary' not in df.columns:
            df['Summary'] = ''
        if 'Keywords' not in df.columns:
            df['Keywords'] = ''
        
        # Track statistics
        stats = {
            'total_rows': len(df),
            'processed': 0,
            'skipped_empty': 0,
            'skipped_error': 0,
            'failed': 0
        }
        
        # Process each row
        for idx, row in df.iterrows():
            row_num = idx + 1  # 1-indexed for display
            print(f"\n{'─'*60}")
            print(f"Row {row_num}/{len(df)}")
            print(f"{'─'*60}")
            
            # Get OCR text from the row
            ocr_text = row.get('OCR')
            
            # Handle empty or missing OCR text
            if pd.isna(ocr_text) or not str(ocr_text).strip():
                print(f"⚠️  Row {row_num}: No OCR text - skipping")
                df.at[idx, 'Summary'] = '[SKIPPED: No OCR text provided]'
                df.at[idx, 'Keywords'] = ''
                stats['skipped_empty'] += 1
                continue
            
            ocr_text = str(ocr_text).strip()
            
            # Check if OCR text is an error message
            if ocr_text.startswith('[ERROR:') or ocr_text.startswith('[SKIPPED:'):
                print(f"⚠️  Row {row_num}: OCR contains error/skip message - skipping")
                df.at[idx, 'Summary'] = '[SKIPPED: OCR failed]'
                df.at[idx, 'Keywords'] = ''
                stats['skipped_error'] += 1
                continue
            
            # Get filename for logging (if available)
            filename = row.get('filename', f'Row {row_num}')
            print(f"📄 Processing: {filename}")
            print(f"   OCR text length: {len(ocr_text)} characters")
            
            # Generate summary
            try:
                if provider == PROVIDER_GEMINI:
                    summary = generate_summary_gemini(client, ocr_text)
                else:
                    summary = generate_summary_openai(client, ocr_text)
                
                if summary:
                    # Extract keywords from the summary and get cleaned summary
                    cleaned_summary, keywords = extract_keywords_from_summary(summary)
                    
                    df.at[idx, 'Summary'] = cleaned_summary
                    df.at[idx, 'Keywords'] = keywords
                    stats['processed'] += 1
                    print(f"✅ Row {row_num}: Successfully generated summary")
                    if keywords:
                        print(f"   Keywords: {keywords}")
                else:
                    df.at[idx, 'Summary'] = '[ERROR: Summary generation failed]'
                    df.at[idx, 'Keywords'] = ''
                    stats['failed'] += 1
                    print(f"❌ Row {row_num}: Summary generation failed")
                    
            except Exception as e:
                df.at[idx, 'Summary'] = f'[ERROR: {str(e)}]'
                df.at[idx, 'Keywords'] = ''
                stats['failed'] += 1
                print(f"❌ Row {row_num}: Error - {e}")
                logging.error(f"Row {row_num} ({filename}): {e}")
        
        # Save the updated spreadsheet
        print(f"\n{'='*60}")
        print("💾 Saving results to spreadsheet...")
        df.to_excel(excel_path, index=False)
        print(f"✅ Spreadsheet updated: {excel_path}")
        
        # Print summary statistics
        print(f"\n{'='*60}")
        print("📈 PROCESSING SUMMARY")
        print(f"{'='*60}")
        print(f"Total rows: {stats['total_rows']}")
        print(f"Successfully processed: {stats['processed']}")
        print(f"Skipped (no OCR text): {stats['skipped_empty']}")
        print(f"Skipped (OCR error): {stats['skipped_error']}")
        print(f"Failed: {stats['failed']}")
        
        if stats['total_rows'] > 0:
            success_rate = (stats['processed'] / stats['total_rows']) * 100
            print(f"Success rate: {success_rate:.1f}%")
        
        print(f"{'='*60}\n")
        
        # Log summary
        logging.info(f"Spreadsheet processing complete: {stats['processed']}/{stats['total_rows']} successful")
        
    except Exception as e:
        print(f"\n❌ Error processing spreadsheet: {e}")
        logging.error(f"Error processing spreadsheet {excel_path}: {e}", exc_info=True)

# ------------------------------------------------------------------
# User Interaction & Main
# ------------------------------------------------------------------
def select_provider() -> str:
    while True:
        choice = input("Select AI model: 1) ChatGPT (OpenAI)  2) Google Gemini  > ").strip()
        if choice == '1':
            return PROVIDER_OPENAI
        if choice == '2':
            return PROVIDER_GEMINI
        print("Invalid choice. Enter 1 or 2.")

def main():
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        input_dir = os.path.join(script_dir, 'TXT')
        output_dir = os.path.join(script_dir, 'Summaries_TXT')
        logging.info("Starting summary generation pipeline")
        
        provider = select_provider()
        if provider == PROVIDER_GEMINI:
            client = initialize_gemini_client()
        else:
            client = initialize_openai_client()
            if client is None:
                return
        
        # Check for Excel spreadsheet in the TXT directory (where input files are)
        input_path = Path(input_dir)
        excel_file = find_excel_file(input_path)
        
        if excel_file:
            # Spreadsheet mode: Process summaries from OCR column
            print(f"\n✅ Found Excel spreadsheet: {excel_file.name}")
            print("📊 Will generate summaries from OCR column in spreadsheet")
            process_with_spreadsheet(provider, client, excel_file)
        else:
            # Direct mode: Process TXT files
            print("\n📁 No Excel spreadsheet found")
            print("📂 Will process TXT files from folder")
            print(f"Input: {input_dir}")
            print(f"Output: {output_dir}")
            process_txt_files(provider, client, input_dir, output_dir)
        
        logging.info("Completed successfully")
    except FileNotFoundError as e:
        logging.error(e)
    except ValueError as e:
        logging.error(e)
    except errors.APIError as e:
        logging.error(f"Gemini API setup error: {e}")
    except Exception as e:
        logging.error(f"Unexpected failure: {e}")

if __name__ == '__main__':
    main()
