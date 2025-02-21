# Generated by Django 5.1.6 on 2025-02-21 19:40

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DonationCampaign',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('creator_name', models.CharField(max_length=100)),
                ('contact_info', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('goal_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('donation_link', models.URLField(blank=True, null=True)),
                ('evidence', models.TextField(blank=True, null=True)),
                ('evidence_file', models.FileField(blank=True, null=True, upload_to='evidence/')),
                ('evidence_link', models.URLField(blank=True, null=True)),
            ],
        ),
    ]
