# StudyPath — Personalized Learning Planner (Minimal Offline Edition)

**StudyPath** creates a **smart, adjustable study plan** from your subjects, target exam date, daily study time, and areas of weakness.
It runs locally with **Flask** (no external APIs) and stores data in a simple JSON file.

## Features
- ✍️ Input subjects, strengths/weaknesses, exam date, hours/day
- 🗓️ Auto‑generate a **daily plan** (weighted toward weak topics)
- 🔁 Plan **adapts** when you mark tasks done or change inputs
- 📈 Simple **progress charts** (per subject & overall)
- 💾 Local JSON storage (no accounts needed)

## Quick Start
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
# then open http://127.0.0.1:5000
```

## Project Structure
```
studypath/
  app.py
  requirements.txt
  README.md
  data/
    studypath.json
  templates/
    index.html
  static/
    styles.css
    app.js
```
