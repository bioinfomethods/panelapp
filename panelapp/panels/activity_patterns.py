"""
Activity text pattern matching constants.

The Activity model stores human-readable text descriptions instead of structured
event types. This was expedient initially but makes filtering and analysis difficult.

The proper fix would be to:
1. Add an event_type field to the Activity model
2. Update all ~30 add_activity() call sites to pass event types
3. Generate display text at render time instead of storing it

Until that refactoring happens, we use text pattern matching to identify event types.
This is fragile and depends on the exact wording used throughout the codebase.
"""

from django.db.models import Q


class ActivityPattern:
    """
    Constants for matching activity event types via text patterns.

    These patterns match the freeform text stored in Activity.text field.
    Each pattern list contains text fragments that indicate a specific event type.
    """

    # Patterns indicating entity (gene/STR/region) additions
    # Matches: "BRCA1 was added to Breast Cancer Panel"
    #          "gene: TP53 was added"
    #          "removed gene:BRCA2 from the panel" (note: "removed" is its own category)
    ENTITY_ADDED = [
        "was added to",
        "was added",
    ]

    # Patterns indicating rating/classification changes
    # Matches: "BRCA1 has been classified as Green List"
    #          "Classified BRCA1 as Amber"
    #          "Rating Changed from RED to GREEN"
    RATING_CHANGED = [
        "has been classified as",
        "Classified ",
        "Rating Changed from",
    ]

    @classmethod
    def build_entity_added_filter(cls):
        """
        Build a Django Q filter for entity addition activities.

        Returns:
            Q: A Django Q object that can be used in queryset.filter()
        """
        q_objects = Q()
        for pattern in cls.ENTITY_ADDED:
            q_objects |= Q(text__icontains=pattern)
        return q_objects

    @classmethod
    def build_rating_changed_filter(cls):
        """
        Build a Django Q filter for rating/classification change activities.

        Returns:
            Q: A Django Q object that can be used in queryset.filter()
        """
        q_objects = Q()
        for pattern in cls.RATING_CHANGED:
            q_objects |= Q(text__icontains=pattern)
        return q_objects
