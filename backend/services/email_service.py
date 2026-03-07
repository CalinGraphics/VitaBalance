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
    Comportament:
      - dacă RESEND_API_KEY NU este setat:
          * în modul debug: NU trimite email real, dar afișează linkul în consolă și întoarce True (fallback dev)
          * în producție: ridică RuntimeError cu mesaj clar pentru a fi propagat în API.
      - dacă RESEND_API_KEY este setat:
          * ridică RuntimeError cu mesajul original în caz de eroare Resend,
            astfel încât detaliul să fie vizibil în răspunsul HTTP 500.
    """
    settings = get_settings()

    if not settings.resend_api_key:
        msg = (
            "Configurația de email lipsește pe server: RESEND_API_KEY nu este setată. "
            "Adaugă RESEND_API_KEY în environment-ul serviciului backend (Render) și redeployează aplicația."
        )
        print("[VitaBalance] RESEND_API_KEY lipsă – emailul NU este trimis.")
        print(f"[VitaBalance] To: {to_email}")
        print("[VitaBalance] Link magic (copiază și deschide în browser):")
        print(magic_link_url)
        # În dezvoltare permitem fallback-ul în consolă.
        if settings.debug:
            return True
        # În producție tratăm lipsa cheii ca eroare clară.
        raise RuntimeError(msg)

    # Dacă suntem în modul de test Resend (cont nou, fără domeniu verificat),
    # putem trimite doar către o singură adresă – de obicei adresa de cont.
    # Dacă este setat RESEND_TEST_RECIPIENT, trimitem acolo, indiferent de to_email.
    to_addr = to_email
    test_recipient = getattr(settings, "resend_test_recipient", None)
    if test_recipient:
        print(
            "[VitaBalance] RESEND_TEST_RECIPIENT activ – "
            f"trimit către {test_recipient} (token pentru {to_email})."
        )
        to_addr = test_recipient

    try:
        import resend

        resend.api_key = settings.resend_api_key
        r = resend.Emails.send(
            {
                "from": settings.resend_from_email,
                "to": [to_addr],
                "subject": "VitaBalance – Autentificare",
                "html": f"""
            <p>Bună,</p>
            <p>Apasă link-ul de mai jos pentru a te conecta în VitaBalance:</p>
            <p><a href="{magic_link_url}" style="color:#00f5ff; font-weight: bold;">Conectare</a></p>
            <p>Dacă nu ai cont, acesta va fi creat automat la prima utilizare. Link-ul expiră în {settings.magic_link_expire_hours} ore și poate fi folosit o singură dată.</p>
            <p>Dacă nu ai cerut acest email, poți să îl ignori.</p>
            <p>— VitaBalance</p>
            """,
            }
        )
        if not getattr(r, "id", None):
            raise RuntimeError(
                f"Resend nu a returnat un ID pentru emailul trimis. "
                f"(from={settings.resend_from_email}, to={to_addr}, original_to={to_email})"
            )
        return True
    except Exception as e:
        error_msg = (
            "Eroare la trimitere email magic link: "
            f"{e} "
            f"(from={settings.resend_from_email}, to={to_addr}, original_to={to_email}, "
            f"RESEND_TEST_RECIPIENT={test_recipient})"
        )
        print(error_msg)
        # Ridicăm eroarea pentru a fi prinsă în endpoint și afișată în frontend.
        raise RuntimeError(error_msg)
