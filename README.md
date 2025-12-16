# ZMO AI Pipelines

A collection of easy-to-use AI tools designed for researchers and social scientists. These tools use Google's Gemini AI to automatically transcribe audio, extract text from documents (OCR/HTR), and generate summaries.

## ☁️ Easiest Way to Use (No Installation Required!)

We have created **Google Colab notebooks** that run entirely in your browser. You don't need to install anything on your computer.

**1. Audio Transcription**  
Convert interviews, meetings, and lectures into text.  
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Audio-transcription/Audio_Transcription_Colab.ipynb)

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
1. Click one of the "Open in Colab" badges above.
2. Sign in with your Google account.
3. Follow the simple step-by-step instructions in the notebook.
4. You will need a free [Gemini API key](https://aistudio.google.com/apikey).

---

## 🎯 What Can These Tools Do?

### 📝 Audio Transcription
Perfect for qualitative research:
- **Interviews:** Transcribe one-on-one interviews with speaker labels.
- **Focus Groups:** Identify different speakers (best with clear audio).
- **Lectures:** Create structured notes from recordings.
- **Meetings:** Generate minutes and action items.

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

**Pro Tip:** Save your API key in Colab Secrets (🔑 icon in sidebar) for automatic loading across sessions!

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
Image Quality:** For OCR/HTR, use high-resolution scans (300+ DPI recommended). The notebook uses Gemini's high-resolution mode automatically.
- **Handwriting:** HTR works best with clear handwriting. Use specialized prompts (French, Arabic, Multilingual) for better accuracy.
- **Enter your API key in the notebook or save it in Colab Secrets (🔑 icon in left sidebar) with name `GEMINI_API_KEY`.
- **"File not uploaded":** Click the upload button and select your files. Supported formats: PDF, JPG, PNG, WEBP, HEIC.
- **Slow Processing:** Large files take time. Gemini 2.5 Flash is faster but Gemini 3 Pro gives higher quality for complex handwriting.
- **Poor OCR Results:** Try using the specialized HTR prompts (French, Arabic, Multilingual) if working with handwritten document