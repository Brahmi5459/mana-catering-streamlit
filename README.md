# Mana Catering — free Streamlit pilot

Start with `DEPLOYMENT.md`. The app uses Streamlit Community Cloud for the website and Supabase for persistent PostgreSQL storage. No Docker or paid hosting subscription is required for the pilot, subject to free-tier limits.

Entrypoint: `streamlit_app.py`  
Database setup: `schema.sql`  
Python packages: `requirements.txt`  
Secrets template: `.streamlit/secrets.toml.example`

Never commit real secrets. Read the security and Android limitations in `DEPLOYMENT.md` before launch.
