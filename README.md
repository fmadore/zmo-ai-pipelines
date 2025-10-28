# ZMO AI Pipelines

A collection of easy-to-use AI tools for processing documents and audio files. These tools use Google's Gemini AI to automatically transcribe, extract text, and generate summaries.

## 🎯 What Can These Tools Do?

### 📝 Audio Transcription
Convert your audio recordings into text automatically. Perfect for:
- Meeting recordings
- Interviews
- Lectures and presentations
- Q&A sessions

**Supported formats:** MP3, WAV, M4A, FLAC, OGG, WebM, MP4, AAC

### 📄 OCR (Optical Character Recognition)
Extract text from scanned documents or PDFs with printed text. Works with:
- Any language and writing system
- Newspapers, books, reports, letters
- Forms and technical documents
- Documents with both printed and handwritten text

### ✍️ HTR (Handwritten Text Recognition)
Transcribe handwritten documents with high precision. Specialized support for:
- French handwritten documents
- Arabic handwritten manuscripts
- Multilingual handwritten documents

### 📊 Text Summarization
Generate concise summaries with keywords from long text documents automatically. Choose between OpenAI or Google Gemini models. Summaries are generated in the same language as the input text.

---

## 🚀 Getting Started

### Step 1: Install Python

You need Python 3.8 or newer installed on your computer.
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **Mac/Linux:** Python is usually pre-installed

### Step 2: Get API Keys

**For Gemini (required for Audio, OCR, and HTR):**
1. Go to [Google AI Studio](https://aistudio.google.com/api-keys)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy your API key (you'll need it in the next step)

**For OpenAI (optional, for Text Summarization only):**
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Create a new API key
4. Copy your API key

### Step 3: Set Up Your Environment

1. **Download or clone this project** to your computer
2. **Open a terminal/command prompt** in the project folder
3. **Install required packages:**
   ```
   pip install -r requirements.txt
   ```
4. **Create a `.env` file** by copying the example:
   - Rename `.env.example` to `.env`
   - Open `.env` in a text editor
   - Replace `your_gemini_api_key_here` with your actual Gemini API key
   - (Optional) Replace `your_openai_api_key_here` with your OpenAI API key if you want to use OpenAI for summaries

### Step 4: (Optional) Install FFmpeg for Audio Splitting

If you want to split long audio files into smaller segments for better accuracy:

**Windows:**
```
winget install Gyan.FFmpeg
```

**Mac:**
```
brew install ffmpeg
```

**Linux:**
```
sudo apt-get install ffmpeg
```

After installation, update the paths in your `.env` file if needed.

---

## 📖 How to Use Each Tool

All tools now support **two modes of operation**:
1. **Direct Mode** - Process all files in a folder
2. **Spreadsheet Mode** - Use an Excel file to specify which files to process and collect results

### 🎤 Audio Transcription

**Direct Mode:**
1. Place your audio files in the `Audio-transcription/Audio/` folder
2. Open a terminal in the `Audio-transcription/` folder
3. Run:
   ```
   python transcribe_audio.py
   ```
4. Follow the prompts to:
   - Choose between faster or higher quality processing
   - Select a transcription style (meeting minutes, interview, lecture, etc.)
   - Decide if you want to split long audio files
5. Find your transcriptions in the `Audio-transcription/Transcriptions/` folder

**Tips:**
- Splitting audio into 10-minute segments can improve accuracy for long recordings
- Use the appropriate prompt style for best results (e.g., "meeting minutes" for business meetings)

### 📄 OCR (Printed Text)

**Direct Mode:**
1. Place your PDF files in the `OCR/PDF/` folder
2. Open a terminal in the `OCR/` folder
3. Run:
   ```
   python gemini_ocr_processor.py
   ```
4. Choose your Gemini model (Flash or Pro)
5. The script will process all PDFs automatically
6. Find the extracted text in the `OCR/OCR_Results/` folder
7. Check the `OCR/log/` folder for processing details

**Spreadsheet Mode:**
1. Create an Excel file (`.xlsx` or `.xls`) with a column named `filename`
2. List the PDF filenames you want to process in this column
3. Place the Excel file in the `OCR/PDF/` folder
4. Place your PDF files in the same `OCR/PDF/` folder
5. Run:
   ```
   python gemini_ocr_processor.py
   ```
6. Choose your Gemini model
7. The script will automatically detect the Excel file and:
   - Process only the PDFs listed in the spreadsheet
   - Add an `OCR` column with the extracted text
   - Save the updated spreadsheet with results
8. Check the `OCR/log/` folder for processing details

**Spreadsheet Benefits:**
- Process specific files from a large collection
- Keep all results organized in one file
- Easily feed OCR results to the Summary pipeline
- Track which files have been processed

**Best for:**
- Books, newspapers, magazines
- Printed documents in any language
- Forms and official documents

### ✍️ HTR (Handwritten Text)

**Direct Mode:**
1. Place your PDF files in the `HTR/PDF/` folder
2. Open a terminal in the `HTR/` folder
3. Run:
   ```
   python gemini_htr_processor.py
   ```
4. Choose the language:
   - **1** for French handwritten documents
   - **2** for Arabic handwritten manuscripts
   - **3** for multilingual documents
5. Choose your Gemini model (Flash or Pro)
6. Find the transcribed text in the `HTR/OCR_Results/` folder
7. Check the `HTR/log/` folder for processing details

**Spreadsheet Mode:**
1. Create an Excel file (`.xlsx` or `.xls`) with a column named `filename`
2. List the PDF filenames you want to process in this column
3. Place the Excel file in the `HTR/PDF/` folder
4. Place your PDF files in the same `HTR/PDF/` folder
5. Run:
   ```
   python gemini_htr_processor.py
   ```
6. Choose the language and model
7. The script will automatically detect the Excel file and:
   - Process only the PDFs listed in the spreadsheet
   - Add an `HTR` column with the transcribed text
   - Save the updated spreadsheet with results
8. Check the `HTR/log/` folder for processing details

**Note:** Handwritten text recognition is more challenging and may require manual review for accuracy.

### 📊 Text Summarization

**Direct Mode:**
1. Place your text files (.txt) in the `Summary/TXT/` folder
2. Open a terminal in the `Summary/` folder
3. Run:
   ```
   python AI_generate_summaries.py
   ```
4. Choose your AI provider:
   - **1** for OpenAI (requires OpenAI API key)
   - **2** for Google Gemini (uses your Gemini API key)
5. Find your summaries with keywords in the `Summary/Summaries_TXT/` folder

**Spreadsheet Mode:**
1. Use an Excel file (`.xlsx` or `.xls`) with an `OCR` or `HTR` column containing the text to summarize
   - This can be the output from the OCR or HTR pipeline
2. Place the Excel file in the `Summary/TXT/` folder
3. Run:
   ```
   python AI_generate_summaries.py
   ```
4. Choose your AI provider
5. The script will automatically detect the Excel file and:
   - Read text from the `OCR` column
   - Generate summaries for each row
   - Add a `Summary` column with the results
   - Add a `Keywords` column with extracted keywords (pipe-separated: `keyword1 | keyword2 | keyword3`)
   - Save the updated spreadsheet
   
**Spreadsheet Benefits:**
- Seamless integration with OCR/HTR outputs
- All data in one organized file
- Easy to review and compare original text with summaries
- Automatically skips rows with errors or missing data
- Keywords extracted and formatted separately for easy filtering/analysis

**Features:**
- Generates concise summaries in the same language as the input text
- Automatically extracts 5-10 relevant keywords for each document
- Works with any language
- Choose between OpenAI GPT or Google Gemini models

---

## 🔄 Complete Pipeline Workflow

You can now chain all three tools together using spreadsheets:

**Example: OCR → Summary Pipeline**
1. Create `data.xlsx` with a `filename` column listing your PDF files
2. Place `data.xlsx` and PDFs in `OCR/PDF/` folder
3. Run OCR: `python gemini_ocr_processor.py`
   - Result: Excel file now has `filename` and `OCR` columns
4. Move `data.xlsx` to `Summary/TXT/` folder
5. Run Summary: `python AI_generate_summaries.py`
   - Result: Excel file now has `filename`, `OCR`, `Summary`, and `Keywords` columns

**Example: HTR → Summary Pipeline**
1. Create `manuscripts.xlsx` with a `filename` column
2. Place it in `HTR/PDF/` with your handwritten PDFs
3. Run HTR: `python gemini_htr_processor.py`
   - Result: Excel file now has `filename` and `HTR` columns
4. Move `manuscripts.xlsx` to `Summary/TXT/` folder
5. Run Summary (it will read from `OCR` or `HTR` column)
   - Result: Excel file now has `filename`, `HTR`, `Summary`, and `Keywords` columns

**Spreadsheet Column Names:**
- **Input for OCR/HTR:** `filename` (required)
- **Output from OCR:** `OCR` (created automatically)
- **Output from HTR:** `HTR` (created automatically)
- **Input for Summary:** `OCR` or `HTR` (must exist)
- **Output from Summary:** `Summary` and `Keywords` (created automatically)

---

## 📁 Project Structure

```
zmo-ai-pipelines/
├── Audio-transcription/
│   ├── Audio/              ← Put audio files here
│   ├── Transcriptions/     ← Transcriptions appear here
│   ├── prompts/            (Different transcription styles)
│   └── transcribe_audio.py
├── OCR/
│   ├── PDF/                ← Put PDFs here (and optional Excel file)
│   ├── OCR_Results/        ← Extracted text appears here (direct mode)
│   ├── log/                (Processing logs)
│   └── gemini_ocr_processor.py
├── HTR/
│   ├── PDF/                ← Put PDFs here (and optional Excel file)
│   ├── OCR_Results/        ← Transcriptions appear here (direct mode)
│   ├── log/                (Processing logs)
│   └── gemini_htr_processor.py
├── Summary/
│   ├── TXT/                ← Put text files or Excel file here
│   ├── Summaries_TXT/      ← Summaries appear here (direct mode)
│   └── AI_generate_summaries.py
├── .env                    ← Your API keys go here
└── requirements.txt        (List of required packages)
```

**Note:** When using spreadsheet mode, the Excel file is updated in place with new columns containing the results.

---

## 💡 Tips for Best Results

### For Audio Transcription:
- Use clear audio recordings without too much background noise
- For long recordings (over 30 minutes), enable audio splitting
- Choose the right prompt style for your content type

### For OCR:
- Use high-quality scans (300 DPI or higher recommended)
- Ensure pages are properly oriented (not upside down)
- Clear, well-lit scans work best

### For HTR:
- High-resolution scans are crucial for handwritten documents
- Clean, clear handwriting transcribes better
- Historical documents may require manual review for accuracy

### For Spreadsheet Mode:
- Use `.xlsx` or `.xls` format (Excel files)
- The `filename` column is required for OCR/HTR processing
- Files without the `.pdf` extension will have it added automatically
- Rows with missing filenames or files will be skipped with clear error messages
- The spreadsheet is updated in place - keep a backup if needed
- You can process the same spreadsheet multiple times (e.g., re-run failed items)
- Empty or error rows are clearly marked so you can identify issues

### General:
- Process one or a few files at a time initially to check quality
- Check the log files if something goes wrong
- Keep your API key private and never share it
- Spreadsheet mode is ideal for batch processing and keeping organized records

---

## ❓ Troubleshooting

### "API Key not found" error
- Make sure you created the `.env` file (not `.env.example`)
- Check that your API key is correctly pasted in the `.env` file
- Ensure there are no extra spaces or quotes around the key

### "No audio/PDF files found" error
- Check that you placed files in the correct folder
- Verify the file format is supported
- Make sure the file isn't corrupted

### FFmpeg-related errors (audio splitting)
- Audio transcription works without FFmpeg, you just can't split files
- Install FFmpeg using the instructions in Step 4
- Update the paths in your `.env` file if needed

### Processing is slow
- This is normal! AI processing takes time
- Larger files take longer to process
- Consider using the faster model (gemini-2.5-flash) for quick tasks

---

## 📞 Support

If you encounter issues:
1. Check the log files in the respective `log/` folders
2. Review the troubleshooting section above
3. Make sure all requirements are installed: `pip install -r requirements.txt`
4. Verify your API key is valid and has quota remaining

---

## 📄 License

This project uses AI services that are subject to their respective terms of service. Make sure your use complies with Google Gemini's usage policies.

---

**Happy Processing! 🎉**
