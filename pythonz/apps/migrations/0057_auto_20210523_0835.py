# Generated by Django 3.2.3 on 2021-05-23 01:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0056_auto_20201119_1842'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='nofollow',
            field=models.BooleanField(default=False, verbose_name='Без перехода по ссылкам.'),
        ),
        migrations.AddField(
            model_name='historicalarticle',
            name='nofollow',
            field=models.BooleanField(default=False, verbose_name='Без перехода по ссылкам.'),
        ),
    ]
