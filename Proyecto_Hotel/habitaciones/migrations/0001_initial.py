# Generado automáticamente por Django 5.0.14 el 2026-10-03 10:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Habitacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('numero', models.IntegerField(unique=True, verbose_name='Número de Habitación')),
                ('tipo', models.CharField(max_length=50, verbose_name='Tipo de Habitación')),
                ('precio', models.IntegerField(verbose_name='Precio por Noche')),
                ('disponible', models.BooleanField(default=True, verbose_name='¿Está Disponible?')),
            ],
        ),
    ]
