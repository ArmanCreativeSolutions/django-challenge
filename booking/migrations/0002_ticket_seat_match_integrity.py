from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("booking", "0001_initial")]

    operations = [
        # Ticket.match supports UNIQUE(user, match). The composite FK prevents a
        # mismatched seat/match even in SQL or code that bypasses the service.
        migrations.RunSQL(
            sql="""
                ALTER TABLE booking_ticket
                ADD CONSTRAINT ticket_seat_match_fk
                FOREIGN KEY (seat_id, match_id)
                REFERENCES booking_matchseat (id, match_id);
            """,
            reverse_sql="ALTER TABLE booking_ticket DROP CONSTRAINT ticket_seat_match_fk;",
        )
    ]

