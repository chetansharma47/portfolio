"""Outbound mail through the Resend API."""

from __future__ import annotations

import html
from dataclasses import dataclass

import httpx

from app.config import settings

RESEND_ENDPOINT = "https://api.resend.com/emails"


class MailNotConfigured(RuntimeError):
    pass


class MailSendFailed(RuntimeError):
    pass


@dataclass(slots=True)
class EnquiryMail:
    brand: str
    email: str
    budget_amount: int
    currency: str
    billing_cycle: str
    message: str
    slot_name: str
    slot_size: str = ""
    placement: str = ""

    @property
    def subject(self) -> str:
        return (
            f"Ad enquiry: {self.slot_name} - {self.brand} "
            f"({self.budget_amount} {self.currency} {self.billing_cycle.lower()})"
        )

    @property
    def rows(self) -> list[tuple[str, str]]:
        return [
            ("Brand / Company", self.brand),
            ("Contact Email", self.email),
            ("Budget Offer", f"{self.budget_amount} {self.currency} ({self.billing_cycle})"),
            ("Slot Requested", self.slot_name),
            ("Slot Size", self.slot_size or "Not specified"),
            ("Placement", self.placement or "Not specified"),
            ("Message", self.message),
        ]

    def as_text(self) -> str:
        body = "\n".join(f"{key}: {value}" for key, value in self.rows)
        return body + "\n\nSent from the advertisement board on the portfolio site."

    def as_html(self) -> str:
        cells = "".join(
            "<tr>"
            f'<td style="padding:10px 0;border-bottom:1px solid #eef2f6;color:#64748b;width:150px;'
            f'vertical-align:top">{html.escape(key)}</td>'
            f'<td style="padding:10px 0;border-bottom:1px solid #eef2f6;font-weight:500">'
            f"{html.escape(str(value))}</td>"
            "</tr>"
            for key, value in self.rows
        )
        return (
            '<div style="margin:0;background:#f5f7fa;padding:24px;'
            "font-family:'Segoe UI',Arial,sans-serif;color:#0f172a\">"
            '<table role="presentation" cellpadding="0" cellspacing="0" '
            'style="max-width:620px;margin:0 auto;background:#ffffff;border:1px solid #e2e8f0;'
            'border-radius:10px;overflow:hidden">'
            '<tr><td style="padding:20px 24px;background:#0f172a;color:#ffffff">'
            '<div style="font-size:16px;font-weight:600">New advertisement slot enquiry</div>'
            f'<div style="font-size:13px;opacity:.75;margin-top:4px">{html.escape(self.slot_name)}'
            f" &middot; {self.budget_amount} {html.escape(self.currency)} "
            f'{html.escape(self.billing_cycle.lower())}</div></td></tr>'
            '<tr><td style="padding:8px 24px 20px">'
            '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" '
            f'style="font-size:14px;line-height:1.6">{cells}</table>'
            '<p style="margin:18px 0 0;font-size:13px;color:#64748b">Reply directly to this email '
            f"to reach {html.escape(self.brand)}.</p>"
            "</td></tr></table></div>"
        )


async def send_enquiry(mail: EnquiryMail) -> str:
    """Send the notification mail and return the provider message id."""
    if not settings.resend_api_key:
        raise MailNotConfigured("RESEND_API_KEY is not set")

    payload = {
        "from": settings.enquiry_from,
        "to": [settings.enquiry_to],
        "reply_to": mail.email,
        "subject": mail.subject,
        "text": mail.as_text(),
        "html": mail.as_html(),
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(
                RESEND_ENDPOINT,
                headers={"Authorization": f"Bearer {settings.resend_api_key}"},
                json=payload,
            )
        except httpx.HTTPError as exc:  # network level
            raise MailSendFailed(f"Mail service unreachable: {exc}") from exc

    if response.status_code >= 400:
        detail = ""
        try:
            detail = response.json().get("message", "")
        except ValueError:
            detail = response.text[:200]
        raise MailSendFailed(detail or f"Mail service returned {response.status_code}")

    try:
        return str(response.json().get("id", ""))
    except ValueError:
        return ""
