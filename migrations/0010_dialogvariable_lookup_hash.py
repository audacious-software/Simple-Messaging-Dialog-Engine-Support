# pylint: skip-file
# Generated by Django 3.2.16 on 2023-01-18 18:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simple_messaging_dialog_support', '0009_auto_20221006_1110'),
    ]

    operations = [
        migrations.AddField(
            model_name='dialogvariable',
            name='lookup_hash',
            field=models.CharField(blank=True, max_length=1024, null=True),
        ),
    ]
