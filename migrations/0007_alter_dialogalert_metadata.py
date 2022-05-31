# pylint: skip-file
# Generated by Django 3.2.13 on 2022-05-31 15:39

from django.db import migrations, models
from django.utils import version

class Migration(migrations.Migration):

    dependencies = [
        ('simple_messaging_dialog_support', '0006_auto_20220505_1148'),
    ]

    if version.get_complete_version()[0] >= 3:
        operations = [
            migrations.AlterField(
                model_name='dialogalert',
                name='metadata',
                field=models.JSONField(blank=True, null=True),
            ),
        ]
    else:
        operations = []
