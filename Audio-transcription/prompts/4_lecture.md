# Lecture

Begin with a concise checklist (3-7 bullets) outlining the transcription process: (1) listen to the audio carefully, (2) identify key concepts and main points, (3) structure transcript in paragraphs, (4) extract central ideas and supporting details, (5) note audience Q&A separately, (6) verify academic and technical terminology, (7) format output according to requirements.

Transcribe the educational content accurately, focusing strictly on the key concepts and main points. Structure the transcript in clear paragraphs, only including slide references or visual descriptions when explicitly mentioned in the material. Note audience questions and responses in a separate section. Preserve all academic terminology and technical language precisely; do not simplify unless specifically requested. Organize the material logically for educational clarity, and highlight major concepts and definitions.

Extract only the central ideas and supporting points emphasized by the speaker, such as the thesis, key claims, evidence/examples, methodologies, conclusions, and implications or limitations.

After completing each section, perform a brief validation to ensure all required components are present and requirements are met. If any critical section or required field is missing (e.g., Q&A, slide references, timestamps), output the section header with the note: `Not present in the audio.` If required information for a field (such as a timestamp) is missing, either omit the field or note `No timestamp available.` For Keywords/Tags, list as many as are present, or write `Less than 6 keywords identified.`

When producing the output, follow the exact Markdown structure below:

```
# Summary (≤ 200 words)
A single paragraph summarizing the core of the lecture.

## Core Takeaways
- 5–8 bullets capturing the lecture’s main points

## Key Points by Section
### [Section Title] (Start: hh:mm:ss or 'No timestamp available')
- 2–4 bullets summarizing the main ideas for each section
*Repeat as necessary for each section in the order presented in the lecture.*

## Definitions & Concepts
- Term — brief, precise definition (with first timestamp observed or 'No timestamp available')
*One bullet per unique term. If none, state `Not present in the audio.`*

## Evidence & Examples
- Brief list of case studies/data/examples used. If none, state `Not present in the audio.`

## Implications / Limitations
- Bullets concisely noting significance, constraints, or open questions. If none, state `Not present in the audio.`

## Q&A (if any)
- Q: [Audience question] (timestamp) → A: [Short answer]
*Group multiple Qs as separate bullets. If none, state `Not present in the audio.`*

## References Mentioned
- Author/Title (approx. timestamp). Use `[sp?]` if spelling is uncertain. If none, state `Not present in the audio.`

## Keywords/Tags
- List 6–10 concise keywords for indexing/search. If fewer than 6, list what is present and state `Less than 6 keywords identified.`

---

## Style Constraints
- Use clear, neutral academic prose.
- Avoid filler language, opinions, or extrapolation beyond the audio.
- Keep all bullets concise (1–2 lines maximum).
- Retain all technical or academic terminology exactly as used.
