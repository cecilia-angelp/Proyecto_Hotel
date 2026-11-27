from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("habitaciones", "0003_alter_habitacion_options"),
    ]

    operations = [
        migrations.AlterField(
            model_name="habitacion",
            name="numero",
            field=models.IntegerField(
                unique=True,
                validators=[MinValueValidator(1), MaxValueValidator(9999)],
                verbose_name="Número de Habitación",
            ),
        ),
    ]
