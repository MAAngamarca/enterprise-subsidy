# Generated by Django 3.2.17 on 2023-02-08 00:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subsidy', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='learnercreditaccesspolicy',
            name='subsidy',
        ),
        migrations.RemoveField(
            model_name='subscriptionaccesspolicy',
            name='subsidy',
        ),
    ]
