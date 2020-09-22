from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapps', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='mobileapp',
            old_name='analytics_url_dev',
            new_name='analytics_url',
        ),
        migrations.RenameField(
            model_name='mobileapp',
            old_name='analytics_url_prod',
            new_name='android_download_url',
        ),
        migrations.RenameField(
            model_name='mobileapp',
            old_name='download_url',
            new_name='ios_download_url',
        ),
        migrations.RenameField(
            model_name='mobileapphistory',
            old_name='analytics_url_dev',
            new_name='analytics_url',
        ),
        migrations.RenameField(
            model_name='mobileapphistory',
            old_name='analytics_url_prod',
            new_name='android_download_url',
        ),
        migrations.RenameField(
            model_name='mobileapphistory',
            old_name='download_url',
            new_name='ios_download_url',
        ),
        migrations.RemoveField(
            model_name='mobileapp',
            name='identifier',
        ),
        migrations.RemoveField(
            model_name='mobileapp',
            name='operating_system',
        ),
        migrations.RemoveField(
            model_name='mobileapphistory',
            name='identifier',
        ),
        migrations.RemoveField(
            model_name='mobileapphistory',
            name='operating_system',
        ),
        migrations.AddField(
            model_name='mobileapp',
            name='android_app_id',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mobileapp',
            name='ios_app_id',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mobileapphistory',
            name='android_app_id',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='mobileapphistory',
            name='ios_app_id',
            field=models.CharField(db_index=True, max_length=255, null=True, blank=True),
        ),
    ]
