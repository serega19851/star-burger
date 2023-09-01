from django.db import models
from django.core.validators import MinValueValidator
from phonenumber_field.modelfields import PhoneNumberField
from django.utils import timezone
from django.db.models import F, Sum


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def get_restaurants_able_fulfill_order(self, all_restaurants):
        menu_items = RestaurantMenuItem.objects.filter(
                availability=True
                ).select_related('restaurant', 'product')

        for order in self:
            avalable_restaurants = []
            for ordered_product in order.order_elements.all():
                avalable_restaurants.append(
                        [menu_item.restaurant for menu_item in menu_items
                         if ordered_product.product.id == menu_item.product.id]
                )

            capable_restaurants = []
            for restaurant in all_restaurants:
                amount = 0
                for avalable_restaurant in avalable_restaurants:
                    if restaurant in avalable_restaurant:
                        amount += 1
                if amount == len(avalable_restaurants):
                    capable_restaurants.append(restaurant)

            order.selected_restaurants = capable_restaurants
        return self

    def get_all_orders(self, all_restaurants):
        all_orders = self.objects.exclude(status='DELIVERED').select_related(
            'selected_restaurant'
        ).prefetch_related('order_elements__product').annotate(
            total_price=Sum(F('order_elements__price'))).order_by(
            '-status'
        ).get_restaurants_able_fulfill_order(all_restaurants)
        return all_orders


class Order(models.Model):
    RAW = 'RA'
    PREPARING_ORDER = 'PO'
    DELIVERY = 'DL'
    ORDER_COMPLETED = 'OC'

    CASH = 'CA'
    ELECTRONIC = 'EP'

    ORDER_STATUSES = [
            (RAW, 'Необработанный'),
            (PREPARING_ORDER, 'Заказа собирается'),
            (DELIVERY, 'Доставка'),
            (ORDER_COMPLETED, 'Заказ выполнен'),
            ]

    PAYMENT_CHOICES = [
            (CASH, 'Наличными'),
            (ELECTRONIC, 'Электронный')
            ]

    status = models.CharField(
            'статус',
            max_length=15,
            choices=ORDER_STATUSES,
            default=RAW,
            db_index=True,
            )
    payment = models.CharField(
            'Способ оплаты',
            max_length=15,
            choices=PAYMENT_CHOICES,
            default=ELECTRONIC,
            db_index=True,
            )
    address = models.CharField(
            'адрес',
            max_length=100,
            db_index=True,
            )
    firstname = models.CharField(
            'имя',
            max_length=50,
            db_index=True,
            )
    lastname = models.CharField(
            'фамилия',
            max_length=50,
            db_index=True,
            )
    phonenumber = PhoneNumberField(
            'телефон',
            db_index=True,
            )
    registration_at = models.DateTimeField(
            'зарегистрирован',
            default=timezone.now,
            db_index=True,
            )
    called_at = models.DateTimeField(
            'звонок заказчику',
            db_index=True,
            null=True,
            blank=True,
            )
    delivered_at = models.DateTimeField(
            'доставлен',
            db_index=True,
            null=True,
            blank=True,
            )
    comment = models.TextField(
            'комментарий',
            blank=True,
            )
    selected_restaurant = models.ForeignKey(
            Restaurant,
            related_name='orders',
            verbose_name="выбранный ресторан",
            on_delete=models.CASCADE,
            null=True,
            blank=True,
            )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f'{self.firstname} {self.lastname}, {self.address}'


class OrderElement(models.Model):
    order = models.ForeignKey(
            Order,
            verbose_name='заказ',
            related_name='order_elements',
            on_delete=models.CASCADE,
            )
    product = models.ForeignKey(
            Product,
            verbose_name='товар',
            related_name='order_elements',
            on_delete=models.CASCADE,
            )
    quantity = models.IntegerField(
            'количество',
            validators=[MinValueValidator(1)],
            )
    price = models.DecimalField(
            'стоимость продукта',
            max_digits=8,
            decimal_places=2,
            validators=[MinValueValidator(0)],
            )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return f'''
        {self.product.name}, {self.order.firstname}
        {self.order.lastname} {self.order.address}
        '''
