import django.utils.timezone
import model_utils.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edx_solutions_organizations', '0002_remove_organization_workgroups'),
        ('mobileapps', '0003_auto_20171114_0212'),
    ]

    operations = [
        migrations.CreateModel(
            name='Theme',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('name', models.CharField(max_length=255, null=True, blank=True)),
                ('logo_image_uploaded_at', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('active', models.NullBooleanField(default=None)),
                ('organization', models.ForeignKey(related_name='theme', to='edx_solutions_organizations.Organization', on_delete=models.CASCADE)),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='theme',
            unique_together=set([('organization', 'active')]),
        ),
    ]
