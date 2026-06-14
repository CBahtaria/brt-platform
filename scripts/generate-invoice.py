#!/usr/bin/env python3
"""Generate a professional Markdown invoice for BRT Inc. consulting services."""
import sys
import datetime
import os

def generate(client_name: str, services: list[tuple[str, float]], invoice_num: str | None = None):
    today = datetime.date.today()
    due = today + datetime.timedelta(days=14)
    num = invoice_num or f"BRT-{today.strftime('%Y%m')}-001"
    total = sum(amount for _, amount in services)

    lines = [
        f"# Invoice {num}",
        f"",
        f"**Date:** {today.strftime('%d %B %Y')}  ",
        f"**Due:** {due.strftime('%d %B %Y')}",
        f"",
        f"## From",
        f"BRT Inc. (Pre-Incorporation)  ",
        f"Mbabane, Eswatini  ",
        f"info@brtinc.dev",
        f"",
        f"## To",
        f"{client_name}",
        f"",
        f"## Services",
        f"",
        f"| Description | Amount (ZAR) |",
        f"|-------------|-------------|",
    ]
    for desc, amount in services:
        lines.append(f"| {desc} | R {amount:,.2f} |")
    lines += [
        f"| **Total** | **R {total:,.2f}** |",
        f"",
        f"## Payment",
        f"",
        f"**Bank Transfer (FNB Eswatini):** Account details on request  ",
        f"**PayPal:** paypal.me/brtinc  ",
        f"**MTN MoMo:** Available on request  ",
        f"",
        f"Payment due within 14 days. Thank you for your business.",
    ]

    os.makedirs("invoicing", exist_ok=True)
    filename = f"invoicing/{num}-{client_name.lower().replace(' ', '-')}.md"
    with open(filename, "w") as f:
        f.write("\n".join(lines))
    print(f"Invoice written: {filename}")
    return filename


if __name__ == "__main__":
    generate(
        client_name=sys.argv[1] if len(sys.argv) > 1 else "Client Name",
        services=[("RAG System Setup", 15000), ("Monthly Maintenance (Month 1)", 5000)],
    )
