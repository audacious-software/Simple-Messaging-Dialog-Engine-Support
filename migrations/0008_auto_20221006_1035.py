# pylint: skip-file
# Generated by Django 3.2.15 on 2022-10-06 15:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('simple_messaging_dialog_support', '0007_alter_dialogalert_metadata'),
    ]

    operations = [
        migrations.AddField(
            model_name='dialogsession',
            name='last_variable_update',
            field=models.DateTimeField(blank=True, null=True),
        )
    ]

    try:
        from django.db.models import JSONField

        operations.append(migrations.AddField(
            model_name='dialogsession',
            name='latest_variables',
            field=JSONField(default=dict),
        ))
    except ImportError:
        from django.contrib.postgres.fields import JSONField

        operations.append(migrations.AddField(
            model_name='dialogsession',
            name='latest_variables',
            field=JSONField(default=dict),
        ))
