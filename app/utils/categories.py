def get_categories_str(categories: dict[str, dict | None]) -> str:
    def _get_subcategories_str(
        categories: dict[str, dict | None], indent: int = 0
    ) -> list[str]:
        lines = []
        for category, subcategories in categories.items():
            lines.append(f"{indent * '  '}- {category}")
            if subcategories:
                lines.extend(_get_subcategories_str(subcategories, indent + 1))
        return lines

    return "\n".join(_get_subcategories_str(categories))
