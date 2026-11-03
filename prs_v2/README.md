# Patient Record System (PRS) - Version 2 (corrected and refactored)

Python 3.9+, standard library only. Synthetic data only.

## Run
    cd prs_v2
    python main.py

Demo logins (synthetic): `nurse1 / staffpass` (staff), `itadmin / adminpass` (it_admin).
Data is stored in `prs_v2.db` (SQLite, created on first run) and persists across restarts.
Delete `prs_v2.db` to start fresh.

## AI categorization
- Set `ANTHROPIC_API_KEY` to use a real AI model (Claude API).
- Without it, a clearly labeled keyword fallback (NOT an AI model) is used.
- Suggestions are never saved without staff acceptance; AI failure never blocks saving a note.

## Layout (matches Assignment #3 Development View)
    prs/patient  prs/visit  prs/authentication  prs/ai_integration  prs/persistence  prs/ui

Dependency direction: ui -> authentication, patient, visit; visit -> patient (via PatientService),
ai_integration; patient and visit -> persistence.
