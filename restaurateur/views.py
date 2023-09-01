from django import forms
from django.shortcuts import redirect, render
from django.views import View
from django.urls import reverse_lazy
from django.contrib.auth.decorators import user_passes_test

from django.contrib.auth import authenticate, login
from django.contrib.auth import views as auth_views

from foodcartapp.models import Product, Restaurant, Order

from location.models import Location
from location.utils import get_or_create_coordinates
from geopy.distance import distance


class Login(forms.Form):
    username = forms.CharField(
            label='Логин', max_length=75, required=True,
            widget=forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Укажите имя пользователя'
                })
            )
    password = forms.CharField(
            label='Пароль', max_length=75, required=True,
            widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Введите пароль'
                })
            )


class LoginView(View):
    def get(self, request, *args, **kwargs):
        form = Login()
        return render(request, "login.html", context={
            'form': form
            })

    def post(self, request):
        form = Login(request.POST)

        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                if user.is_staff:  # FIXME replace with specific permission
                    return redirect("restaurateur:RestaurantView")
                return redirect("start_page")

        return render(request, "login.html", context={
            'form': form,
            'ivalid': True,
            })


class LogoutView(auth_views.LogoutView):
    next_page = reverse_lazy('restaurateur:login')


def is_manager(user):
    return user.is_staff  # FIXME replace with specific permission


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_products(request):
    restaurants = list(Restaurant.objects.order_by('name'))
    products = list(Product.objects.prefetch_related('menu_items'))

    products_with_restaurant_availability = []
    for product in products:
        availability = {
                item.restaurant_id: item.availability
                for item in product.menu_items.all()
                }
        ordered_availability = [
                availability.get(restaurant.id, False)
                for restaurant in restaurants
                ]
        products_with_restaurant_availability.append(
                (product, ordered_availability)
                )

    return render(
            request,
            template_name="products_list.html",
            context={
                'products_with_restaurant_availability': products_with_restaurant_availability,
                'restaurants': restaurants,
                }
            )


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_restaurants(request):
    return render(request, template_name="restaurants_list.html", context={
        'restaurants': Restaurant.objects.all(),
        })


@user_passes_test(is_manager, login_url='restaurateur:login')
def view_orders(request):
    all_restaurants = Restaurant.objects.all()
    all_locations = Location.objects.all()
    all_orders = Order.objects.get_all_orders(all_restaurants)
    restaurants_with_coords = {}

    for restaurant in all_restaurants:
        coords = get_or_create_coordinates(restaurant.address, all_locations)
        restaurants_with_coords[restaurant] = coords

    for order in all_orders:
        order_coords = get_or_create_coordinates(order.address, all_locations)
        suitable_restaurants = []

        for selected_restaurant in order.selected_restaurants:
            restaurant_coords = restaurants_with_coords.get(
                    selected_restaurant
                    )
            if order_coords[0] is None or restaurant_coords[0] is None:
                order.selected_restaurants = None
                break
            distance_between = distance(order_coords, restaurant_coords).km
            suitable_restaurant = {
                    'restaurant': selected_restaurant.name,
                    'distance': round(distance_between, 3)
                    }
            suitable_restaurants.append(suitable_restaurant)

        order.selected_restaurants = sorted(
            suitable_restaurants,
            key=lambda x: x['distance']
            )
        if order.selected_restaurant and order.status == 'RAW':
            order.status = 'ASSEMBLY'
            order.save()

    return render(request, template_name='order_items.html', context={
        'order_items': all_orders
        })
