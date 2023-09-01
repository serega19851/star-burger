from .models import Order, OrderElement, Product
from rest_framework.serializers import ModelSerializer, IntegerField


class OrderElementSerializer(ModelSerializer):

    class Meta:
        model = OrderElement
        fields = ['product', 'quantity']

    def create(self, validated_data):
        return OrderElement.objects.create(**validated_data)


class OrderSerializer(ModelSerializer):
    id = IntegerField(read_only=True)
    products = OrderElementSerializer(
            many=True,
            allow_empty=False,
            write_only=True
            )

    class Meta:
        model = Order
        fields = [
                'id',
                'address',
                'firstname',
                'lastname',
                'phonenumber',
                'products'
                ]

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            product = Product.objects.get(name=product_data['product'])
            OrderElement.objects.create(
                order=order,
                product=product,
                quantity=product_data['quantity'],
                product_price=product.price
            )
        return order
