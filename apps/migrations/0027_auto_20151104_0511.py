# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0026_auto_20150917_1619'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='externalresource',
            options={'verbose_name_plural': 'Внешние ресурсы', 'verbose_name': 'Внешний ресурс', 'ordering': ('-time_created',)},
        ),
        migrations.RemoveField(
            model_name='user',
            name='digest_enabled',
        ),
    ]
