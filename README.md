# ZMO AI Pipelines

A collection of easy-to-use AI tools designed for researchers and social scientists. These tools use Google's Gemini AI to automatically transcribe audio, extract text from documents (OCR/HTR), and generate summaries.

## ☁️ Easiest Way to Use (No Installation Required!)

We have created **Google Colab notebooks** that run entirely in your browser. You don't need to install anything on your computer.

**1. Audio Transcription**  
Convert interviews, meetings, and lectures into text.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Audio-transcription/Audio_Transcription_Colab.ipynb)

**2. OCR (Printed Text)**  
Extract text from PDFs, books, and newspapers.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/OCR/OCR_Colab.ipynb)

**3. HTR (Handwritten Text)**  
Transcribe handwritten manuscripts and documents.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/HTR/HTR_Colab.ipynb)

**4. Text Summarization**  
Generate summaries and keywords from your texts.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Summary/Summary_Colab.ipynb)

**How to use:**
1. Click one of the "Open in Colab" badges above.
2. Sign in with your Google account.
3. Follow the simple step-by-step instructions in the notebook.
4. You will need a free [Gemini API key](https://aistudio.google.com/app/api-keys).

---

## 🎯 What Can These Tools Do?

### 📝 Audio Transcription
Perfect for qualitative research:
- **Interviews:** Transcribe one-on-one interviews with speaker labels.
- **Focus Groups:** Identify different speakers (best with clear audio).
- **Lectures:** Create structured notes from recordings.
- **Meetings:** Generate minutes and action items.

### 📄 OCR (Optical Character Recognition)
Digitize your archives:
- Extract text from scanned PDFs, images, or books.
- Works with almost any language (Arabic, French, English, German, etc.).
- Great for digitizing newspapers, reports, and official documents.

### ✍️ HTR (Handwritten Text Recognition)
Unlock handwritten archives:
- Transcribe handwritten letters, manuscripts, and field notes.
- Specialized support for **French** and **Arabic** handwriting.
- Useful for historians and archivists working with non-digital sources.

### 📊 Text Summarization
Analyze large amounts of text:
- Generate concise summaries of long documents.
- Automatically extract keywords for tagging and organization.
- Process hundreds of documents at once using Excel sheets.

---

## 💻 Advanced Usage: Local Installation

If you are comfortable with using the terminal/command line, you can run these tools directly on your computer. This is faster for processing large batches of files.

### Step 1: Install Python
You need Python 3.8 or newer.
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **Mac/Linux:** Usually pre-installed.

### Step 2: Get Your API Key
1. Go to [Google AI Studio](https://aistudio.google.com/api-keys).
2. Click "Create API Key".
3. Copy the key (it starts with `AIza...`).

### Step 3: Setup
1. Download this project (Code -> Download ZIP) and unzip it.
2. Open a terminal in the project folder.
3. Install requirements:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a file named `.env` and paste your API key inside:
   ```
   GEMINI_API_KEY=your_key_here
   ```

### Step 4: Run the Tools
Each tool has its own folder. Navigate to the folder and run the script.

**Audio Transcription:**
```bash
cd Audio-transcription
python transcribe_audio.py
```
*Follow the on-screen prompts to select your audio files and settings.*

**OCR (Printed Text):**
```bash
cd OCR
python gemini_ocr_processor.py
```

**HTR (Handwritten Text):**
```bash
cd HTR
python gemini_htr_processor.py
```

**Summarization:**
```bash
cd Summary
python AI_generate_summaries.py
```

---

## 📊 Batch Processing with Excel (Spreadsheet Mode)

For researchers working with many files, you can use Excel to organize your work.

1. Create an Excel file (`.xlsx`) with a column named `filename`.
2. List your PDF filenames in that column.
3. Place the Excel file in the same folder as your PDFs (e.g., `OCR/PDF/`).
4. Run the script. It will detect the Excel file and:
   - Process only the listed files.
   - Add a new column with the results (text or summary).
   - Save the Excel file automatically.

This is perfect for creating a database of your sources!

---

## 💡 Tips for Researchers

- **Audio Quality:** The better the recording, the better the transcript. Try to minimize background noise.
- **Privacy:** Your data is sent to Google's servers for processing but is not used to train their public models (when using the paid API or specific enterprise settings). Always check the latest privacy terms if working with sensitive data.
- **Verification:** AI is powerful but not perfect. Always review the transcripts and OCR results, especially for critical quotes or names.

---

## ❓ Troubleshooting

- **"API Key not found":** Make sure your `.env` file is named exactly `.env` (not `.env.txt`) and contains your key.
- **"File not found":** Ensure your files are in the correct input folders (e.g., `Audio-transcription/Audio/`).
- **Slow Processing:** Large files take time. The "Flash" models are faster but slightly less accurate than "Pro" models.

---

## 👤 About

**ZMO AI Pipelines** created by [Frédérick Madore](https://www.frederickmadore.com/)

Part of the [Leibniz-Zentrum Moderner Orient (ZMO)](https://www.zmo.de/en) research tools.

---

## 📄 License

This project uses AI services that are subject to their respective terms of service. Make sure your use complies with Google Gemini's usage policies.

---

**Happy Processing! 🎉**
