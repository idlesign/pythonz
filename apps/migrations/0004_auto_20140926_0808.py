# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apps', '0003_auto_20140926_0529'),
    ]

    operations = [
        migrations.RenameField(
            model_name='place',
            old_name='user_title',
            new_name='title',
        ),
        migrations.AlterField(
            model_name='user',
            name='place',
            field=models.ForeignKey(related_name='users', on_delete=models.CASCADE, blank=True, verbose_name='Место', to='apps.Place', help_text='Место вашего пребывания (страна, город, село).<br>Например: «Россия, Новосибирск» или «Новосибирск», но не «Нск».', null=True),
        ),
    ]
