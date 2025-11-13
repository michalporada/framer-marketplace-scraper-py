"""Category mapping utility for grouping subcategories into parent categories.

This module provides mapping from subcategories to parent categories based on
Framer Marketplace category structure. This allows us to group products correctly
without needing to scrape category pages.
"""

from typing import Dict, List, Set

# Mapowanie podkategorii -> nadrzędne kategorie
# Na podstawie analizy stron kategorii w Framer Marketplace
CATEGORY_MAPPING: Dict[str, List[str]] = {
    "Community": [
        "Education",
        "Social & Recreational",
        "Social",
        "Wedding",
        "Conference",
        "Environmental",
        "Non-profit",
        "Membership",
        "Political",
        "Church & Religious",
        "Religious",
        "Entertainment",
    ],
    "Business": [
        "Agency",
        "Consulting",
        "SaaS",
        "Startup",
        "Enterprise",
        "Ecommerce",
        "Finance",
        "Coaching",
        "Business Blog",
    ],
    "Portfolio": [
        "Personal",
        "Creative",
        "Artist",
        "Photography",
        "Fashion",
        "Personal Blog",
        "Arts & Crafts",
    ],
}

# Odwrotne mapowanie dla szybkiego wyszukiwania
_SUBCATEGORY_TO_PARENT: Dict[str, List[str]] = {}


def _build_reverse_mapping() -> None:
    """Build reverse mapping from subcategory to parent categories."""
    global _SUBCATEGORY_TO_PARENT
    _SUBCATEGORY_TO_PARENT = {}
    
    for parent, subcategories in CATEGORY_MAPPING.items():
        for subcat in subcategories:
            if subcat not in _SUBCATEGORY_TO_PARENT:
                _SUBCATEGORY_TO_PARENT[subcat] = []
            _SUBCATEGORY_TO_PARENT[subcat].append(parent)


# Initialize reverse mapping on import
_build_reverse_mapping()


def expand_categories(categories: List[str]) -> List[str]:
    """Expand categories list to include parent categories.
    
    Args:
        categories: List of category names
        
    Returns:
        Expanded list with parent categories added
    """
    expanded = set(categories)  # Use set to avoid duplicates
    
    # Add parent categories for each subcategory
    for category in categories:
        if category in _SUBCATEGORY_TO_PARENT:
            expanded.update(_SUBCATEGORY_TO_PARENT[category])
    
    # Return as list, preserving original order, then adding new ones
    result = list(categories)
    for parent in sorted(expanded - set(categories)):
        result.append(parent)
    
    return result


def get_parent_categories(category: str) -> List[str]:
    """Get parent categories for a given category.
    
    Args:
        category: Category name
        
    Returns:
        List of parent category names (empty if category has no parents)
    """
    return _SUBCATEGORY_TO_PARENT.get(category, [])


def get_subcategories(parent_category: str) -> List[str]:
    """Get subcategories for a given parent category.
    
    Args:
        parent_category: Parent category name
        
    Returns:
        List of subcategory names (empty if category has no subcategories)
    """
    return CATEGORY_MAPPING.get(parent_category, [])


def has_category_mapping(category: str) -> bool:
    """Check if a category has any mapping (is a parent or subcategory).
    
    Args:
        category: Category name
        
    Returns:
        True if category is in mapping, False otherwise
    """
    return category in CATEGORY_MAPPING or category in _SUBCATEGORY_TO_PARENT

