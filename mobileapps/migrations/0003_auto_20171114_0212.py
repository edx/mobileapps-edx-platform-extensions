import mobileapps.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapps', '0002_auto_20171110_0149'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mobileapp',
            name='provider_key',
            field=mobileapps.models.EncryptedCharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='mobileapp',
            name='provider_secret',
            field=mobileapps.models.EncryptedCharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='mobileapphistory',
            name='provider_key',
            field=mobileapps.models.EncryptedCharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='mobileapphistory',
            name='provider_secret',
            field=mobileapps.models.EncryptedCharField(max_length=255, null=True, blank=True),
        ),
    ]
