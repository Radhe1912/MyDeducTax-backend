class SectionMapper:
    @staticmethod
    def map_category_to_section(category: str) -> str:
        # Dummy logic
        if category == "Life Insurance":
            return "80C"
        return "Other"
