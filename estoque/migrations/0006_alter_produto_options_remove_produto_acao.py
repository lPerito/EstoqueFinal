# Generated by Django 5.2 on 2025-05-19 01:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('estoque', '0005_alter_produto_pn_alter_produto_unique_together'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='produto',
            options={'ordering': ['nome']},
        ),
        migrations.RemoveField(
            model_name='produto',
            name='acao',
        ),
    ]
