import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('edx_solutions_organizations', '0002_remove_organization_workgroups'),
    ]

    operations = [
        migrations.CreateModel(
            name='MobileApp',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('identifier', models.CharField(unique=True, max_length=255, db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('operating_system', models.PositiveSmallIntegerField(choices=[(1, 'Android'), (2, 'iOS'), (3, 'Windows'), (4, 'Other')])),
                ('deployment_mechanism', models.PositiveSmallIntegerField(default=1, choices=[(1, 'Public app store'), (2, 'Enterprise'), (3, 'OTA'), (4, 'Other')])),
                ('download_url', models.CharField(max_length=255, null=True, blank=True)),
                ('analytics_url_dev', models.CharField(max_length=255, null=True, blank=True)),
                ('analytics_url_prod', models.CharField(max_length=255, null=True, blank=True)),
                ('provider_key', models.CharField(max_length=255, null=True, blank=True)),
                ('provider_secret', models.CharField(max_length=255, null=True, blank=True)),
                ('provider_dashboard_url', models.CharField(max_length=255, null=True, blank=True)),
                ('current_version', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MobileAppHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('identifier', models.CharField(max_length=255, db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('operating_system', models.PositiveSmallIntegerField(choices=[(1, 'Android'), (2, 'iOS'), (3, 'Windows'), (4, 'Other')])),
                ('deployment_mechanism', models.PositiveSmallIntegerField(choices=[(1, 'Public app store'), (2, 'Enterprise'), (3, 'OTA'), (4, 'Other')])),
                ('download_url', models.CharField(max_length=255, null=True, blank=True)),
                ('analytics_url_dev', models.CharField(max_length=255, null=True, blank=True)),
                ('analytics_url_prod', models.CharField(max_length=255, null=True, blank=True)),
                ('provider_key', models.CharField(max_length=255, null=True, blank=True)),
                ('provider_secret', models.CharField(max_length=255, null=True, blank=True)),
                ('provider_dashboard_url', models.CharField(max_length=255, null=True, blank=True)),
                ('current_version', models.CharField(max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False)),
            ],
        ),
        migrations.CreateModel(
            name='NotificationProvider',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=255)),
                ('api_url', models.CharField(max_length=255, null=True, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='mobileapphistory',
            name='notification_provider',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to='mobileapps.NotificationProvider', null=True),
        ),
        migrations.AddField(
            model_name='mobileapphistory',
            name='updated_by',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.PROTECT),
        ),
        migrations.AddField(
            model_name='mobileapp',
            name='notification_provider',
            field=models.ForeignKey(related_name='mobile_apps', blank=True, to='mobileapps.NotificationProvider', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='mobileapp',
            name='organizations',
            field=models.ManyToManyField(related_name='mobile_apps', to='edx_solutions_organizations.Organization', blank=True),
        ),
        migrations.AddField(
            model_name='mobileapp',
            name='updated_by',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, blank=True, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='mobileapp',
            name='users',
            field=models.ManyToManyField(related_name='mobile_apps', to=settings.AUTH_USER_MODEL, blank=True),
        ),
    ]
