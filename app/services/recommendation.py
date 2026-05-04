def generate_recommendations(deductions):
    recommendations = []

    for d in deductions:
        remaining = d.get("remaining")

        if remaining and remaining > 0:
            recommendations.append({
                "section_code": d["section"],
                "message": f"You can still claim {remaining} under {d['section']}",
                "potential_savings": remaining
            })

    return recommendations