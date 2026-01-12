"""Email template defaults and helpers (Django version)."""

from __future__ import annotations

from typing import Dict

from django.db import transaction

from .models import EmailTemplateConfig

DEFAULT_EMAIL_TEMPLATES: Dict[str, Dict[str, str]] = {
    "payment_link": {
        "subject": "Braselton Water/Sewer - Online Payment Link",
        "body": """Hello,

Thank you for contacting the Town of Braselton Water/Sewer Department.

To pay your utility bill online, please visit:
https://braselton.net/pay

Payment options:
- Credit/debit card
- E-check

You can also pay in person at Town Hall (cash, check, or money order).

Hours: Monday-Friday, 8:00 AM - 5:00 PM
Address: 6111 Winder Highway, Braselton, GA 30517

Questions? Call (770) 867-4488

Town of Braselton Water/Sewer
""",
    },
    "adjustment_form": {
        "subject": "Braselton Water/Sewer - Request for Adjustment Form",
        "body": """Hello,

Please find the Request for Adjustment form here:
https://braselton.net/utilities/adjustment-form

Complete and return to:
- Email: utilitybilling@braselton.net
- In person: Braselton Town Hall

We'll review your request within 3-5 business days.

Questions? Call (770) 867-4488

Town of Braselton Water/Sewer
""",
    },
    "general_info": {
        "subject": "Braselton Water/Sewer - Contact Information",
        "body": """Hello,

Thank you for contacting the Town of Braselton Water/Sewer Department.

For more information, please visit our website:
https://braselton.net

Contact Us:
Phone: (770) 867-4488
Email: utilitybilling@braselton.net
Address: 6111 Winder Highway, Braselton, GA 30517

Hours: Monday-Friday, 8:00 AM - 5:00 PM

Town of Braselton Water/Sewer
""",
    },
}


def _default_for(template_type: str) -> Dict[str, str]:
    return DEFAULT_EMAIL_TEMPLATES.get(template_type, DEFAULT_EMAIL_TEMPLATES["general_info"])


def ensure_email_template(template_type: str) -> EmailTemplateConfig:
    """Return template from DB, creating with defaults if missing."""

    template = EmailTemplateConfig.objects.filter(template_type=template_type).first()
    if template:
        return template

    defaults = _default_for(template_type)
    template = EmailTemplateConfig.objects.create(
        template_type=template_type,
        subject=defaults["subject"],
        body=defaults["body"],
    )
    return template


def ensure_all_email_templates() -> None:
    """Make sure all templates exist in the database."""

    with transaction.atomic():
        for template_type in DEFAULT_EMAIL_TEMPLATES:
            if not EmailTemplateConfig.objects.filter(template_type=template_type).exists():
                defaults = _default_for(template_type)
                EmailTemplateConfig.objects.create(
                    template_type=template_type,
                    subject=defaults["subject"],
                    body=defaults["body"],
                )

