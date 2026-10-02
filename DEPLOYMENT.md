# Mana Catering — no-subscription pilot deployment

This package is a Streamlit rewrite of the supplied FastAPI web experience. It is intended for a free pilot using **Streamlit Community Cloud + Supabase Free**. It does not require Docker, PostgreSQL installed on your computer, PythonAnywhere, or a paid subscription. Both providers may change free-plan limits; Supabase can pause inactive free projects and Streamlit apps hibernate after inactivity. This is not a promise of always-on production hosting.

## What is included

- Public directory filtered by village and catering category; only approved listings appear.
- Provider registration with explicit phone-publication consent; new listings start pending.
- Admin sign-in and approve/reject workflow.
- Customer enquiry form for approved providers.
- Optional SMTP email notifications; app still saves records if email is not configured.
- Supabase-hosted PostgreSQL storage, so app restarts do not rely on Streamlit's local filesystem.
- No seeded/fake providers or phone numbers.

## 1. Create the database (free tier)

1. Create an account at https://supabase.com and create a project on the Free plan.
2. Open **SQL Editor** in the Supabase dashboard.
3. Open `schema.sql` from this folder, paste its contents into SQL Editor, and run it.
4. Open **Project Settings → API** (or the API keys page). Copy the Project URL and the `service_role` key. Treat the service-role key as a password. Never put it in source code, GitHub, or a browser/mobile app.

The SQL enables Row Level Security and revokes access for `anon` and `authenticated`. This Streamlit server uses the service-role key privately. Anyone with that key can bypass those policies, so store it only in Streamlit Secrets and rotate it if exposed.

## 2. Upload this folder to GitHub

1. Create a GitHub repository, for example `mana-catering-streamlit`.
2. Upload the contents of this folder (not the parent folder) to the repository root.
3. Do not upload `.streamlit/secrets.toml`; `.gitignore` excludes it. `secrets.toml.example` is a template only.

## 3. Deploy free on Streamlit Community Cloud

1. Sign in at https://share.streamlit.io using GitHub.
2. Select **Create app**.
3. Choose your repository, branch `main`, and entrypoint `streamlit_app.py`.
4. Open **Advanced settings → Secrets** and paste the following, replacing the placeholders with your own values:

```toml
SUPABASE_URL = "https://YOUR_PROJECT.supabase.co"
SUPABASE_SERVICE_ROLE_KEY = "YOUR_SERVICE_ROLE_KEY"
ADMIN_USERNAME = "your-admin-username"
ADMIN_PASSWORD = "a-long-unique-password"
LOCATIONS = "Narasaraopet Town,Narasaraopet Rural,Ravipadu,Petta,Yellamanda,Other nearby village"
```

5. Select Python 3.12 if the UI asks, then deploy. Streamlit installs packages from `requirements.txt`.
6. When it starts, open the app URL and test provider registration, admin approval, browsing, and enquiry submission.

Streamlit will provide a URL ending in `streamlit.app`. The free service may hibernate after inactivity; a visitor can wake it. The Supabase free project may pause after low database activity. Review both providers' current terms and limits before inviting the public.

## 4. Optional email notifications

Email is not required for the app to run. To enable it, add SMTP values to the same Streamlit Secrets area:

```toml
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = "587"
SMTP_USER = "your-email@gmail.com"
SMTP_PASSWORD = "YOUR_GOOGLE_APP_PASSWORD"
SMTP_FROM = "your-email@gmail.com"
ADMIN_EMAIL = "your-email@gmail.com"
```

For Gmail, use an App Password if your account is eligible; never use your normal Google password. Email failures do not undo a saved registration/enquiry. Check logs and test with your own address first.

## 5. Local test (optional)

Python 3.10+ recommended:

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Add secrets in `.streamlit/secrets.toml` locally, using the same format as the deployment secrets. Do not commit that file.

## Important security and launch limitations

- This is a pilot implementation, not a security-audited production system. The admin password is a shared secret, not individual accounts/MFA; add stronger authentication and audit logging before operating at scale.
- The Supabase service-role key is highly privileged. It is used only server-side in Streamlit Secrets. Never expose it in Android or public source.
- Public forms need stronger abuse protection (rate limiting/CAPTCHA, phone verification, monitoring) before broad public launch.
- Confirm provider ownership and consent before publishing contact details. Provide a way to request corrections/removal and publish privacy/terms/contact information appropriate to your operation.
- Email is best-effort SMTP, with no durable retry queue or delivery guarantee.
- The original Flutter Android code is not wired to this Streamlit app: it expects the old FastAPI JSON API. This ZIP focuses on a working deployable web pilot. Android needs a separate API/backend integration and Android build/signing/testing; it is not a deployable Android release.
- Free tiers are subject to provider rules, quotas, sleep/pausing, and change. No custom domain, always-on guarantee, or Play Store publication is included.
- Before using the app commercially, check your employer's outside-work/IP policy and obtain any needed approvals.

## Uploaded archive security note

The source ZIP supplied for conversion contained a `.env` file and a bundled virtual environment. This new ZIP intentionally excludes both. If the old `.env` contained real credentials and that archive was shared or uploaded anywhere, rotate those passwords/API credentials (including admin, SMTP, and database credentials) before deployment.
