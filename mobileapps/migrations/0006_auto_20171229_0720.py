from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapps', '0005_auto_20171219_0647'),
    ]

    operations = [
        migrations.AddField(
            model_name='mobileapp',
            name='ios_bundle_id',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mobileapphistory',
            name='ios_bundle_id',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='header_bg_image_uploaded_at',
            field=models.DateTimeField(db_index=True, null=True, blank=True),
        ),
    ]
