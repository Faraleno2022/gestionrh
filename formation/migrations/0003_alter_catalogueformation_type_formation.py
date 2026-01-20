# Generated migration for type_formation field length increase

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('formation', '0002_catalogueformation_evaluationformation_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='catalogueformation',
            name='type_formation',
            field=models.CharField(max_length=500, help_text='Liste déroulante + saisie libre'),
        ),
    ]
