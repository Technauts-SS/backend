from django.db import migrations
from django.conf import settings

def set_default_creator(apps, schema_editor):
    # Отримуємо моделі з історичних версій
    User = apps.get_model(settings.AUTH_USER_MODEL.split('.')[0], settings.AUTH_USER_MODEL.split('.')[1])
    DonationCampaign = apps.get_model('fundraising', 'DonationCampaign')
    
    # Знаходимо першого користувача (або адміна)
    default_user = User.objects.order_by('id').first()
    
    # Заповнюємо NULL-значення
    DonationCampaign.objects.filter(creator__isnull=True).update(creator=default_user)

class Migration(migrations.Migration):
    dependencies = [
        ('fundraising', '0009_alter_donationcampaign_creator'),  # Замініть на реальну назву попередньої міграції
    ]

    operations = [
        migrations.RunPython(set_default_creator),
    ]