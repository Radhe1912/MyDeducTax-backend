def generate_recommendations(deductions):
    recommendations = []

    for d in deductions:
        remaining = d.get("remaining_limit")

        if remaining and remaining > 0:
            recommendations.append({
                "section_code": d["section_code"],
                "message": f"You can still claim {remaining} under {d['section_code']}",
                "potential_savings": remaining
            })

    return recommendations