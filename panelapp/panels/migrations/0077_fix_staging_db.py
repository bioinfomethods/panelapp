# One-off migration to fix staging DB where migrations from an upstream branch
# were applied but the code doesn't have those changes.
# Drops the original_panel column and cleans up migration records.
# Remove this migration once staging DB is refreshed from prod.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("panels", "0076_auto_20191206_1041"),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
                ALTER TABLE panels_evaluation DROP COLUMN IF EXISTS original_panel;
                DELETE FROM django_migrations WHERE name IN (
                    '0077_evaluation_original_panel',
                    '0078_super_panel_entities_fix',
                    '0079_django_4_2_changes'
                );
            """,
            reverse_sql=migrations.RunSQL.noop,
        ),
    ]
