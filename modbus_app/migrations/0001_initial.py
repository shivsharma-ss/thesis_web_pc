# Generated by Django 5.0.6 on 2024-07-09 13:00

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Signal',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('port', models.IntegerField()),
                ('direction', models.CharField(max_length=3)),
                ('state', models.IntegerField(default=0)),
            ],
        ),
    ]
