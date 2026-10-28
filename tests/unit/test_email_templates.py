from app.modules.recommendations.application.email_templates import render_matches_email


def test_render_matches_email_empty():
    subject, html = render_matches_email(company_name="ACME", items=[])
    assert "0 nové zhody" in subject
    assert "ACME" in html


def test_render_matches_email_with_items():
    items = [
        {
            "listingTitle": "Ponuka 1",
            "materialType": "Kov",
            "location": "BA",
            "score": 90,
            "listingId": "abc",
        }
    ]
    subject, html = render_matches_email(company_name="ACME", items=items, site_url="https://x.sk")
    assert "1 nové zhody" in subject
    assert "Ponuka 1" in html
    assert "https://x.sk/dashboard/listings/abc" in html
