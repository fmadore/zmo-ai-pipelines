# ZMO AI Pipelines

Three Google Colab notebooks that use Google's Gemini to transcribe recordings, read text
off scans, and summarise documents. Built for researchers, not programmers — everything
runs in a browser tab, and there is nothing to install.

| Notebook | What it does | Open |
|---|---|---|
| **Audio & video transcription** | Interviews, focus groups, lectures, meetings → text | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Audio_Transcription_Colab.ipynb) |
| **OCR / HTR** | Scanned PDFs and photographs → text, printed or handwritten | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/OCR_HTR_Colab.ipynb) |
| **Summaries & keywords** | Long texts or whole spreadsheets → summaries and keywords | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/fmadore/zmo-ai-pipelines/blob/main/Summary_Colab.ipynb) |

---

## ⚠️ Read this before uploading research material

On the **free** Gemini tier, [Google's API terms](https://ai.google.dev/gemini-api/terms)
state that Google uses what you send to improve its products, and that *"human reviewers
may read, annotate, and process your API input and output."*

On the **paid** tier — billing enabled on your Google Cloud project — Google does not use
your prompts or responses to improve its products.

If your recordings, documents or transcripts are covered by an ethics approval, a consent
form, an archive agreement or a data-protection undertaking, check whether free-tier
handling is compatible with it **before** you upload anything. For interview data the
usual answer is to enable billing first.

---

## Getting started

1. Click one of the **Open in Colab** badges above.
2. Sign in with your Google account.
3. Get a free API key at **[aistudio.google.com/apikey](https://aistudio.google.com/apikey)**.
4. Store it in **Colab Secrets** (see below) — this takes a minute, once, and then every
   notebook you open picks it up automatically.
5. Run the steps in the notebook from top to bottom.

### Storing your key in Colab Secrets

1. Click the 🔑 **Secrets** icon in the left sidebar of Colab
2. **+ Add new secret**
3. Name: `GEMINI_API_KEY`
4. Value: your key
5. Switch **Notebook access** ON

Do this rather than typing the key into the notebook. Colab saves widget contents into the
notebook file when you save a copy, so a key typed into a box can travel with the file to
Drive or GitHub. A secret never touches the notebook.

> **Keys created before 2026 are being retired.** Google now rejects unrestricted
> old-style keys, and will reject all of them from **September 2026**. Any key you create
> today is the new kind. If a key that used to work suddenly stops, make a fresh one.

### Connect Google Drive (recommended)

Step 2.5 in each notebook. It is worth the extra click:

- Load large files straight from Drive instead of uploading them through the browser
- **Results are written as they are produced** — each page, each segment, every few
  spreadsheet rows. If your browser disconnects halfway through a long job, the finished
  work is already saved.

---

## What each notebook does

### 🎙️ Audio & video transcription

- **Audio:** MP3, WAV, M4A, FLAC, OGG, AAC · **Video:** MP4, MOV, AVI, MKV, WEBM
- Video files have their soundtrack extracted first, so you are never billed for the
  picture — a 1 GB video usually becomes about 30 MB of audio.
- Long recordings are split into segments, and **timestamps are corrected back to their
  real position in the full recording**. A quotation marked `[00:34:12]` is at 00:34:12 of
  your original file.
- Each segment is shown how the previous one ended, so speaker numbering stays consistent
  across the whole transcript.
- Seven styles, all editable: clean-read transcription, **strict verbatim** (keeps every
  hesitation, for conversation and discourse analysis), interview, meeting minutes,
  lecture notes, Q&A summary, and translation into English.

### 📜 OCR / HTR

- **PDF, JPG, PNG, WEBP, HEIC**
- Printed text in any language, plus specialised prompts for handwritten French, Arabic,
  and mixed-script manuscripts
- Reads at Gemini's highest detail setting; scan at 300 DPI or better
- Choose a page range — try three pages before committing to a 400-page book
- Read several pages at once for speed, and every page is saved the moment it is done

### 📊 Summaries & keywords

- Plain text files, or a whole spreadsheet column
- Adds **Summary** and **Keywords** columns; your original columns are untouched
- Pick which column holds your text — it does not have to be called `OCR`
- Saves every few rows, and **an interrupted run continues where it stopped** instead of
  paying for the same rows twice

Text files from the OCR notebook can be fed straight into the summary notebook.

---

## Tips

- **Try a small batch first.** Three pages, or one short recording. Check the output before
  committing to a long job.
- **Scan quality beats every setting.** 300 DPI or more for OCR.
- **Choose the model to match the material.** Best-quality for handwriting, difficult
  audio, or several speakers; faster-and-cheaper for clean printed text and clear
  recordings.
- **Verbatim is a methodological choice.** The default transcription style tidies text up:
  hesitations removed, numbers standardised. If your method needs every "um", pick *Strict
  verbatim*.
- **Always check the output.** These models are good and still wrong sometimes — names,
  dates and direct quotations especially.

---

## Troubleshooting

**"No API key found"** — add the `GEMINI_API_KEY` secret as described above and switch
*Notebook access* on, then press *Check Secrets again* in Step 2.

**A key that used to work now fails** — see the note about key retirement above; create a
new key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

**"Could not download the shared helper file"** — Step 1 fetches `zmo_common.py` from this
repository. Check your connection and run the cell again.

**"hit the output limit and was CUT SHORT"** — one reply was too long. For audio, turn
splitting on or shorten the segments. For OCR this is rare and the partial text is kept
and flagged.

**Rate limit errors** — the free tier has limits. The notebooks retry automatically with
backoff. If they still fail: reduce *Pages at once* to 1 in the OCR notebook, wait a few
minutes, or enable billing.

**The Google Drive tab says "not connected" after I connected it** — press **Refresh** in
that tab.

**Uploads fail or stall on a big file** — browser uploads become unreliable above a few
hundred megabytes. Put the file in Google Drive and load it from the Drive tab instead.

**Only some files downloaded** — browsers block long runs of separate downloads. Use
**Download all as ZIP**.

---

## For maintainers

`zmo_common.py` holds everything the three notebooks share: the Gemini client and retry
policy, response handling, the API-key panel, the file picker, Drive mirroring, incremental
saving, and the audio helpers. Each notebook downloads it in Step 1:

```bash
wget -q -O zmo_common.py https://raw.githubusercontent.com/fmadore/zmo-ai-pipelines/main/zmo_common.py
```

A fix therefore lands in all three notebooks at once. It is fetched from `main`, so
anything pushed there reaches users immediately — including mistakes.

Two deliberate choices worth knowing about:

- **No `temperature`, `top_p` or `top_k`.** Google deprecated these sampling parameters in
  July 2026, and the Gemini 3 guide warns that lowering temperature can cause looping or
  degraded output — the worst possible failure for a long transcription.
- **Model IDs are the `-latest` aliases.** `gemini-pro-latest` and `gemini-flash-latest`
  are hot-swapped by Google as new models ship, so the notebooks follow along without
  edits. The trade-off is that an alias can be repointed at a model with different
  behaviour; each run prints what the alias actually resolved to.

---

## About

**ZMO AI Pipelines**, created by [Frédérick Madore](https://www.frederickmadore.com/).

Part of the [Leibniz-Zentrum Moderner Orient (ZMO)](https://www.zmo.de/en) research tools.

Use of these notebooks is subject to the
[Gemini API terms](https://ai.google.dev/gemini-api/terms) and Google's usage policies.
