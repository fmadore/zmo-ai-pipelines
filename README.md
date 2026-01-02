# ZMO AI Pipelines

A collection of easy-to-use AI tools designed for researchers and social scientists. These tools use Google's Gemini AI to automatically transcribe audio, extract text from documents (OCR/HTR), and generate summaries.

## ☁️ Easiest Way to Use (No Installation Required!)

We have created **Google Colab notebooks** that run entirely in your browser. You don't need to install anything on your computer.

**1. Audio & Video Transcription**  
Convert audio and video files (interviews, meetings, lectures) into text.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Audio_Transcription_Colab.ipynb)

**2. OCR/HTR (Printed & Handwritten Text)**  
Extract text from PDFs and images - works with both printed and handwritten documents!  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/OCR_HTR_Colab.ipynb)
- **OCR:** Printed documents, books, newspapers
- **HTR:** Handwritten manuscripts (French, Arabic, Multilingual)
- **Formats:** PDF, JPG, PNG, WEBP, HEIC

**3. Text Summarization**  
Generate summaries and keywords from your texts.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Summary/Summary_Colab.ipynb)

**How to use:**
1. Click one of the "Open in Colab" badges above
2. Sign in with your Google account
3. Get a free [Gemini API key](https://aistudio.google.com/api-keys)
4. **Recommended:** Connect Google Drive (Step 2.5) to:
   - Load files directly from your Drive
   - Auto-save results to Drive (survives browser disconnection!)
5. Follow the step-by-step instructions in each notebook

---

## 🎯 What Can These Tools Do?

### 📝 Audio & Video Transcription
Perfect for qualitative research:
- **Audio formats:** MP3, WAV, M4A, FLAC, OGG, WEBM, AAC
- **Video formats:** MP4, MOV, AVI, MKV, WEBM
- **Interviews:** Transcribe one-on-one interviews with speaker labels
- **Focus Groups:** Identify different speakers (best with clear audio)
- **Lectures:** Create structured notes from recordings
- **Meetings:** Generate minutes and action items
- **Video content:** Extract speech from video files automatically

### 📄 OCR/HTR (Optical & Handwritten Text Recognition)
Digitize your archives - both printed and handwritten:
- **OCR:** Extract text from scanned PDFs, images, books, and newspapers.
- **HTR:** Transcribe handwritten letters, manuscripts, and field notes.
- **Languages:** Works with any language - specialized prompts for French and Arabic handwriting.
- **Formats:** Supports PDF files and images (JPG, PNG, WEBP, HEIC).
- **High Resolution:** Uses Gemini's high-resolution mode for optimal accuracy.

### 📊 Text Summarization
Analyze large amounts of text:
- Generate concise summaries of long documents.
- Automatically extract keywords for tagging and organization.
- Process hundreds of documents at once using Excel sheets.

---

## 💻 Why Use Google Colab?

All notebooks run in **Google Colab**, which provides:
- ✅ **No Installation:** Everything runs in your browser
- ✅ **Free GPU Access:** Faster processing for large files
- ✅ **Easy Sharing:** Share notebooks with colleagues
- ✅ **Secure:** API keys can be stored in Colab Secrets
- ✅ **Always Updated:** Latest Gemini AI features

### ☁️ Google Drive Integration (Recommended)

Both the **Audio Transcription** and **OCR/HTR** notebooks support **Google Drive integration**:

| Feature | Benefit |
|---------|--------|
| 📂 **Load from Drive** | No need to re-upload files each session |
| 💾 **Auto-save to Drive** | Results saved automatically—never lose work if disconnected! |
| 🔄 **Persistent storage** | Access your files and results across sessions |
| 📁 **Visual file browser** | Navigate your Drive folders with ipyfilechooser |

**How to enable:** Run Step 2.5 in either notebook and click "☁️ Connect Google Drive"

**Pro Tips:**
- Save your API key in Colab Secrets (🔑 icon in sidebar) for automatic loading
- Connect Google Drive to prevent data loss if your browser disconnects

---

## 💡 Tips for Researchers

- **Use Google Drive:** Connect your Drive (Step 2.5) to auto-save results and prevent data loss from browser disconnections.
- **Audio/Video Quality:** The better the recording, the better the transcript. Try to minimize background noise.
- **Image Quality:** For OCR/HTR, use high-resolution scans (300+ DPI recommended). The notebook uses Gemini's high-resolution mode automatically.
- **Handwriting:** HTR works best with clear handwriting. Use specialized prompts (French, Arabic, Multilingual) for better accuracy.
- **Long Sessions:** For processing many files, always connect Google Drive first—results are saved continuously.
- **Privacy:** Your data is sent to Google's servers for processing but is not used to train their public models (when using the paid API or specific enterprise settings). Always check the latest privacy terms if working with sensitive data.
- **Verification:** AI is powerful but not perfect. Always review the transcripts and OCR results, especially for critical quotes or names.

---

## ❓ Troubleshooting

**Audio/Video Transcription:**
- **"API Key not valid":** Make sure you copied the entire API key or add `GEMINI_API_KEY` to Colab Secrets
- **"File not uploaded":** Click the upload button and select your files. Supported: MP3, WAV, M4A, FLAC, OGG, WEBM, AAC (audio) and MP4, MOV, AVI, MKV, WEBM (video)
- **Slow Processing:** Large files take time. Gemini 3 Flash is faster but Gemini 3 Pro gives higher quality

**OCR/HTR:**
- **"File not uploaded":** Click the upload button and select your files. Supported: PDF, JPG, PNG, WEBP, HEIC
- **Slow Processing:** Gemini 3 Flash is faster but Gemini 3 Pro gives higher quality for complex handwriting
- **Poor Results:** Try using the specialized HTR prompts (French, Arabic, Multilingual) if working with handwritten documents

---

## 👤 About

**ZMO AI Pipelines** created by [Frédérick Madore](https://www.frederickmadore.com/)

Part of the [Leibniz-Zentrum Moderner Orient (ZMO)](https://www.zmo.de/en) research tools.

---

## 📄 License

This project uses AI services that are subject to their respective terms of service. Make sure your use complies with Google Gemini's usage policies.

---

**Happy Processing! 🎉**