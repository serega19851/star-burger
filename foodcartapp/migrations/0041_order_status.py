# Generated by Django 3.2.15 on 2023-05-20 08:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('foodcartapp', '0040_orderelement_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('RA', 'Необработанный'), ('PO', 'Заказа собирается'), ('DL', 'Доставка'), ('OC', 'Заказ выполнен')], db_index=True, default='RA', max_length=2, verbose_name='статус'),
        ),
    ]
