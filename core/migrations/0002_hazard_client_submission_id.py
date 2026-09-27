from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='hazard',
            name='client_submission_id',
            field=models.UUIDField(blank=True, editable=False, null=True, unique=True),
        ),
    ]