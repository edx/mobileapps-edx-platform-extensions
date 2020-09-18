from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mobileapps', '0004_auto_20171128_0541'),
    ]

    operations = [
        migrations.AddField(
            model_name='theme',
            name='completed_course_tint',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='header_background_color',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='lesson_navigation_color',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='navigation_icon_color',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='theme',
            name='navigation_text_color',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
