# Lead to Client

Sarac Ramsay's internal sales process page: the six stages from Outreach to Onboarding, with calling scripts, intro and proposal decks, objection handling, contracts and the onboarding SOP.

The live version is a Claude Design canvas on claude.ai (the "Lead to Client" artifact). This repo is a copy of its source files, so the team has a backup and can see every change in the history.

## What's in here

| Folder | What it is |
|---|---|
| `project/Main.dc.html` | The Lead to Client page itself: timeline, scripts, decks, objections, onboarding. |
| `project/GAds*.dc.html` | The five Google Ads proposal decks (Real Estate), one per location, with speaker notes under each slide. |
| `project/InsTH*.dc.html` | The interactive Insurance intro deck for Thailand: the whole deck plus one file per slide. |
| `project/canvas.json` | How the boards are laid out on the canvas, and its three pages. |
| `project/gads-assets/`, `project/insth-assets/` | Images used by those decks. |
| `assets/` | Copies of the PDFs and slide pictures that were uploaded to the artifact. `assets/MANIFEST.md` lists which ones are here. |
| `tools/` | The scripts used to turn the PowerPoint exports into editable decks, PDFs and slide pictures. |

## Editing

The `.dc.html` files only render inside Claude Design. Opening them straight in a browser shows unstyled markup, not the page.

The simplest way to change wording, numbers or layout:

1. Open the Lead to Client artifact on claude.ai and switch to the canvas view.
2. Double-click the text you want to change on the right board.
3. Ask Claude to pull the updated files back into this repo and commit them.

You can also edit the files here and ask Claude to publish them to the artifact. Do one or the other at a time: if someone edits the canvas while someone else edits the repo, the two copies drift apart and one set of changes gets overwritten.

## Not in this repo

- About a third of the uploaded files (older intro deck pictures, the SOP PDFs, the jsPDF library) live only in the artifact. `assets/MANIFEST.md` marks them.
- The full-screen copy of the Insurance Thailand deck is a separate artifact.
