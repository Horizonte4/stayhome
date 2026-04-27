from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("properties", "0008_alter_property_options_savedproperty"),
    ]

    operations = [
        migrations.AlterField(
            model_name="property",
            name="image_url",
            field=models.URLField(blank=True, max_length=1000),
        ),
    ]
