"""
Serviciu email – Resend API. Folosit pentru Magic Link.

Setup: în backend/.env adaugă:
  RESEND_API_KEY=re_xxxxxxxxx   (înlocuiește re_xxxxxxxxx cu cheia ta reală de la resend.com)
  RESEND_FROM_EMAIL=onboarding@resend.dev   (opțional; acesta e default-ul)
"""
from config import get_settings


def send_magic_link_email(to_email: str, magic_link_url: str) -> bool:
    """
    Trimite email cu link-ul magic către utilizatorul care a solicitat autentificarea.
    to_email = adresa la care se trimite (cine a apăsat „Trimite link magic”).
    Dacă RESEND_API_KEY nu e setat: nu trimite email, linkul apare doar în consolă (dev).
    """
    settings = get_settings()
    if not settings.resend_api_key:
        print("[VitaBalance] RESEND_API_KEY lipsă – emailul NU este trimis.")
        print("[VitaBalance] Link magic (copiază și deschide în browser):")
        print(magic_link_url)
        return True
    try:
        import resend
        resend.api_key = settings.resend_api_key
        r = resend.Emails.send({
            "from": settings.resend_from_email,
            "to": [to_email],
            "subject": "VitaBalance – Autentificare",
            "html": f"""
            <p>Bună,</p>
            <p>Apasă link-ul de mai jos pentru a te conecta în VitaBalance:</p>
            <p><a href="{magic_link_url}" style="color:#00f5ff; font-weight: bold;">Conectare</a></p>
            <p>Dacă nu ai cont, acesta va fi creat automat la prima utilizare. Link-ul expiră în {settings.magic_link_expire_hours} ore și poate fi folosit o singură dată.</p>
            <p>Dacă nu ai cerut acest email, poți să îl ignori.</p>
            <p>— VitaBalance</p>
            """,
        })
        return bool(getattr(r, "id", None))
    except Exception as e:
        print("Eroare la trimitere email magic link:", e)
        return False
