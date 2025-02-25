# Generated by Django 5.1.6 on 2025-02-25 23:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fundraising', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='donationcampaign',
            name='category',
            field=models.CharField(choices=[('health', "Здоров'я"), ('social', 'Соціальна допомога'), ('education', 'Освіта та наука'), ('ecology', 'Екологія та тварини'), ('other', 'Інше')], default='other', max_length=50),
        ),
        migrations.AddField(
            model_name='donationcampaign',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='campaign_images/'),
        ),
    ]
