# Generated by Django 5.1.6 on 2025-03-05 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clinic_app_service', '0008_alter_patient_gender'),
    ]

    operations = [
        migrations.AlterField(
            model_name='patient',
            name='middle_name',
            field=models.CharField(blank=True, default='', max_length=255, null=True, verbose_name='По батькові'),
        ),
    ]
