# Generated by Django 3.2.15 on 2023-05-20 17:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0043_auto_20230520_1928'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='payment',
            field=models.CharField(choices=[('CA', 'Наличными'), ('EP', 'Электронный')], db_index=True, default='EP', max_length=2, verbose_name='Способ оплаты'),
        ),
    ]
