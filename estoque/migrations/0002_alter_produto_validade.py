# Generated by Django 5.2 on 2025-05-17 15:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='produto',
            name='validade',
            field=models.DateField(blank=True, null=True, verbose_name='Validade'),
        ),
    ]
