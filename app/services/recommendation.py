"""
recommendation.py
─────────────────
Generates actionable, specific optimization suggestions from the deduction results.
"""

SECTION_MESSAGES = {
    "80C": {
        "title": "Section 80C – Investments & Insurance",
        "tip": "You have ₹{remaining:,.0f} unused capacity. Invest in PPF, ELSS, NSC, or Tax-Saving FD to max the ₹1,50,000 limit.",
    },
    "80CCD(1B) NPS": {
        "title": "Section 80CCD(1B) – NPS Self Contribution",
        "tip": "You can claim up to ₹50,000 extra (beyond 80C) by contributing to NPS Tier-1. Current unused: ₹{remaining:,.0f}.",
    },
    "80D Self & Family Health Insurance": {
        "title": "Section 80D – Self & Family Health Insurance",
        "tip": "Your self/family health insurance is capped at ₹{remaining:,.0f} below the allowed limit. Consider increasing your cover.",
    },
    "80D Parents Health Insurance": {
        "title": "Section 80D – Parents Health Insurance",
        "tip": (
            "You have ₹{remaining:,.0f} unused deduction for parents' health insurance. "
            "Buy a health policy for your parents to claim this — "
            "limit is ₹25,000 (₹50,000 if they are senior citizens)."
        ),
    },
    "80D Health Insurance": {
        "title": "Section 80D – Health Insurance",
        "tip": (
            "You have ₹{remaining:,.0f} unused 80D limit. "
            "This could be your parents' health insurance (₹25,000 limit, or ₹50,000 if they are senior citizens). "
            "Consider buying a family floater to fully utilise this deduction."
        ),
    },
    "Sec 24B Home Loan Interest": {
        "title": "Section 24B – Home Loan Interest",
        "tip": "You have ₹{remaining:,.0f} unused capacity. The full ₹2,00,000 limit applies to self-occupied property interest.",
    },
    "80EEB EV Loan Interest": {
        "title": "Section 80EEB – Electric Vehicle Loan",
        "tip": "₹{remaining:,.0f} EV loan interest deduction is still available. Consider financing an EV to claim up to ₹1,50,000.",
    },
    "80TTB Senior Interest Income": {
        "title": "Section 80TTB – Senior Citizen Interest Income",
        "tip": "₹{remaining:,.0f} more interest income can be deducted (FD + savings account interest combined, up to ₹50,000).",
    },
    "80TTA Savings Interest": {
        "title": "Section 80TTA – Savings Account Interest",
        "tip": "You can deduct up to ₹10,000 of savings account interest. ₹{remaining:,.0f} is still available.",
    },
}

DEFAULT_TIP = "You can still invest ₹{remaining:,.0f} more under {section} to maximise your tax savings."


def generate_recommendations(deductions):
    recommendations = []

    for d in deductions:
        remaining = d.get("remaining")

        # Only recommend if there is meaningful unused capacity
        if not remaining or remaining < 500:
            continue

        section = d["section"]
        meta = SECTION_MESSAGES.get(section)

        if meta:
            message = meta["tip"].format(remaining=remaining, section=section)
            title = meta["title"]
        else:
            message = DEFAULT_TIP.format(remaining=remaining, section=section)
            title = section

        # Estimate potential tax savings (30% bracket as conservative upper bound)
        potential_savings = round(remaining * 0.30)

        recommendations.append({
            "section_code": title,
            "message": message,
            "potential_savings": potential_savings,
        })

    return recommendations