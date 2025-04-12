from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # Лише залежність від попередньої міграції reports
        ('reports', '0009_alter_report_fundraiser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='report',
            name='fundraiser',
            field=models.ForeignKey(
                on_delete=models.CASCADE,
                related_name='reports',
                to='fundraising.DonationCampaign',  # Залишаємо посилання на модель
                null=False,
            ),
        ),
    ]