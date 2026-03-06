# README writing guide

A short, app-agnostic guide for writing clear, consistent READMEs.

---

## 1. Opening (title + one paragraph)

- **Title:** Clear product or project name. Avoid stuffing "&" between every word.
- **First paragraph:** In one or two sentences, state **what the app does** and **why someone would use it**. Include every main function; mention the main benefit.
- **Screenshot:** If the app has a UI, put a screenshot right after this paragraph so readers see it before Install.

---

## 2. Requirements

Put this **before Install** so readers know what they need up front.

- **System requirements**
  - Supported OS (e.g. Windows 10+, Linux, macOS).
  - Runtime or language version (e.g. Python 3.10+, Node 18+).
  - Optional: minimum RAM, disk, or GPU if it matters.
  - Optional: system tools or binaries the app uses (e.g. `tar`, `ffmpeg`), and when they’re required vs optional.

- **API keys, access, and permissions**
  - If the app calls external APIs: which services, where to get keys, and where to set them (env vars, config file). Do not paste keys in the README.
  - If no API keys: say so (e.g. “No API keys or online accounts.”).
  - Permissions: what the app needs (e.g. read/write to chosen folders, network, camera, location). Be explicit so users can decide before installing.

---

## 3. Install

- **Prerequisites:** One short bullet list (language/runtime version, optional system deps). Can refer back to Requirements.
- **Commands:** One block per platform. Only the commands people actually run; no long prose. Keep it minimal: clone or download, install deps if any, how to run.

---

## 4. Use (main flow)

- **Split into clear subsections** (e.g. primary flow, then secondary flows) instead of one long list.
- **Numbered steps** for the primary flow. One line per step: label + short explanation.
- **“When to use what”:** One short paragraph with **real-world scenarios**. Tie each feature or mode to a concrete situation (e.g. “For X, do Y; for Z, use …”).
- **Secondary flows** as their own subsections: what to click or run, what the app does, and that it behaves the same on all supported platforms if that’s true.

---

## 5. Output / reference

- Use a **small table** or **short bullets** for output formats, file names, or key options. No long sentences.
- Optional: a short “Advanced / diagnostics” subsection for power users (e.g. fallbacks, what the log shows).

---

## 6. “After you’re done” / next steps

- **In-app path first:** If the app has a clear “done” step (e.g. export, merge, extract), describe that first, then how to use the result (e.g. open in another tool).
- **Manual alternative:** If there’s a way to do the same thing without the app (e.g. CLI one-liners), one line per platform is enough.

---

## 7. Optional sections

- **Packaging / distribution:** Only if relevant. One line per platform or tool.
- **License:** One line: license name + link to `LICENSE` file.
- **Developer / credits:** At the very end, after a separator (e.g. `---`): name and role or link.

---

## 8. What to avoid

- **Diagrams** unless they add real clarity; prefer short paragraphs and lists.
- **Repeating the same block** in multiple sections; explain once, then reference (e.g. “see Merge parts above”).
- **Sensitive details:** No API keys, no internal paths or filenames that could expose secrets.
- **Vague pitch:** Lead with what the app does and when it’s useful, not generic claims (e.g. “works everywhere”).

---

## 9. Tone and style

- **Short sentences.** One idea per sentence where possible.
- **Active voice:** “Click Save” not “The Save button can be clicked.”
- **Concrete examples:** Real names (e.g. filenames, sample values) and situations (e.g. “when moving to a FAT32 USB”).
- **Scannable:** Headings, numbered steps, bullets, one table. A reader skimming should see: what it is → requirements → install → use → output → next steps → license.

---

## Checklist for a new README

- [ ] Title + one paragraph with all main functions and the main benefit.
- [ ] Screenshot near the top (if the app has a UI).
- [ ] **Requirements:** system requirements (OS, runtime, optional tools) and API keys / access / permissions (or “None”).
- [ ] Install: prerequisites + one command block per platform.
- [ ] Use: primary flow as numbered steps; “when to use what” with real-world scenarios; secondary flows as clear subsections.
- [ ] Output/reference: table or short bullets.
- [ ] Next steps: in-app path first, then manual alternative if any.
- [ ] License + developer at the end.
- [ ] No redundant sections; no sensitive paths or keys; short, scannable prose.
