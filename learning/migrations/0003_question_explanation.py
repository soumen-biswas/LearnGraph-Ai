from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [('learning', '0002_progress_user_userprogress_review_due_and_more')]
    operations = [migrations.AddField(model_name='question', name='explanation', field=models.TextField(blank=True))]
