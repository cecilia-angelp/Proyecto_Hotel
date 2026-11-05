# Generado automáticamente por Django 5.0.14 el 2026-11-05 03:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('habitaciones', '0002_alter_habitacion_tipo'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='habitacion',
            options={'ordering': ['numero'], 'verbose_name': 'Habitación', 'verbose_name_plural': 'Habitaciones'},
        ),
    ]
