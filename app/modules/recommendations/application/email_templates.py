"""HTML email templates for auto-matching notifications."""

from __future__ import annotations

from typing import Any

GOLD = "#c9a84c"
GOLD_BRIGHT = "#e8d48b"
BG = "#090807"
FG = "#f3ead8"
MUTED = "#9a8f7c"


def render_matches_email(
    *,
    company_name: str,
    items: list[dict[str, Any]],
    site_url: str = "https://trc-cmep.sk",
) -> tuple[str, str]:
    """Return (subject, html_body) for the daily matches email."""

    subject = f"CMEP: {len(items)} nové zhody pre {company_name}"

    rows = []
    for it in items:
        listing_title = it.get("listingTitle") or "Ponuka"
        material = it.get("materialType") or "—"
        location = it.get("location") or "—"
        score = it.get("score", 0)
        listing_id = it.get("listingId", "")
        listing_url = f"{site_url}/dashboard/listings/{listing_id}" if listing_id else site_url

        rows.append(
            f"""
            <tr>
              <td style="padding:16px 20px;border-bottom:1px solid rgba(201,168,76,0.15);">
                <a href="{listing_url}" style="color:{GOLD_BRIGHT};font-family:Georgia,serif;font-size:18px;text-decoration:none;">
                  {listing_title}
                </a>
                <div style="margin-top:6px;color:{MUTED};font-size:13px;">
                  {material} · {location} · zhoda {score}%
                </div>
                <div style="margin-top:10px;">
                  <a href="{listing_url}" style="display:inline-block;background:{GOLD};color:{BG};padding:8px 16px;border-radius:999px;font-size:13px;font-weight:600;text-decoration:none;">
                    Zobraziť ponuku
                  </a>
                </div>
              </td>
            </tr>
            """
        )

    body = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"></head>
<body style="margin:0;padding:0;background:{BG};color:{FG};font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:{BG};">
    <tr><td align="center" style="padding:32px 16px;">
      <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#0d0c09;border:1px solid rgba(201,168,76,0.25);border-radius:16px;">
        <tr>
          <td style="padding:28px 32px 12px 32px;">
            <div style="color:{GOLD};font-size:11px;letter-spacing:0.25em;text-transform:uppercase;">CMEP · denný prehľad</div>
            <h1 style="margin:8px 0 0 0;color:{GOLD_BRIGHT};font-family:Georgia,serif;font-size:26px;font-weight:normal;">
              Máte {len(items)} nové zhody
            </h1>
            <p style="margin:10px 0 0 0;color:{MUTED};font-size:14px;line-height:1.6;">
              Našli sme ponuky, ktoré zodpovedajú profilu firmy <strong style="color:{FG};">{company_name}</strong>.
            </p>
          </td>
        </tr>
        <tr><td>
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
            {"".join(rows)}
          </table>
        </td></tr>
        <tr>
          <td style="padding:24px 32px 32px 32px;border-top:1px solid rgba(201,168,76,0.15);">
            <p style="margin:0;color:{MUTED};font-size:12px;line-height:1.6;">
              Toto je automatická notifikácia z CMEP.
              <a href="{site_url}/dashboard" style="color:{GOLD_BRIGHT};">Otvoriť dashboard</a>
            </p>
            <p style="margin:12px 0 0 0;color:#6e6658;font-size:11px;">
              © CMEP · Circular Materials Exchange Platform · trc-cmep.sk
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    return subject, body
