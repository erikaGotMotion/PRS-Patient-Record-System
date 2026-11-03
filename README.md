# Patient Record System (PRS) - Version 1 (original GenAI output)

Python 3.9+, standard library only. Synthetic data only.

## Run
    python main.py

Demo logins (synthetic): `nurse1 / staffpass` (staff), `itadmin / adminpass` (it_admin).
Data is stored in `prs.db` (SQLite) and persists across restarts.

## AI categorization
- Set `ANTHROPIC_API_KEY` to use a real AI model (Claude API).
- Without it, a clearly labeled keyword fallback (NOT an AI model) is used.
- Suggestions are never saved without staff acceptance; AI failure never blocks saving a note.

## Layout (matches Assignment #3 Development View)
    prs/patient  prs/visit  prs/authentication  prs/ai_integration  prs/persistence  prs/ui
