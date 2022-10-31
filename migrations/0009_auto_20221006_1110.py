# pylint: skip-file
# Generated by Django 3.2.15 on 2022-10-06 16:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simple_messaging_dialog_support', '0008_auto_20221006_1035'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dialogvariable',
            name='date_set',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='dialogvariable',
            name='dialog_key',
            field=models.CharField(blank=True, db_index=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='dialogvariable',
            name='key',
            field=models.CharField(db_index=True, max_length=1024),
        ),
    ]