from django.utils.timezone import localtime
from django.db import models
from django.http import JsonResponse
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.urls import reverse

from django.core.exceptions import ObjectDoesNotExist

from shophubapp.forms import ProfileForm, ProductForm, ListOfProductsForm, URLForm

from .models import Profile, Product, ListOfProducts, OutgoingLinkClick, Notifications, CollaborationRequest
from django.contrib.contenttypes.models import ContentType

import json
from decimal import Decimal
from bs4 import BeautifulSoup
import requests

from pathlib import Path
from configparser import ConfigParser
import re

BASE_DIR = Path(__file__).resolve().parent.parent

CONFIG = ConfigParser()
CONFIG.read(BASE_DIR / "config.ini")

def landing_action(request):
    if request.user.is_authenticated:
        return redirect('explore')
    return render(request, 'landingpage.html', {})

@login_required
def logout_action(request):
    logout(request)
    return redirect('landing')

@login_required
def view_explore(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    context = {}
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    user_lists = ListOfProducts.objects.all()  # view all lists

    form = ListOfProductsForm()
    context['form'] = form
    context['user_lists'] = user_lists

    return render(request, "explore.html", context)

@login_required
def delete_list(request, list_id):
    user_list = get_object_or_404(
        ListOfProducts, id=list_id, user=request.user)

    profile = Profile.objects.get(user=request.user)

    if user_list in profile.starred_lists.all():
        profile.starred_lists.remove(user_list)

    user_list.delete()

    source = request.META.get('HTTP_REFERER', '')

    return HttpResponseRedirect(source)


@login_required
def star_list(request, list_id):
    try:
        current_list = ListOfProducts.objects.get(id=list_id)
    except ListOfProducts.DoesNotExist:
        return JsonResponse({"error": "List not found"}, status=404)

    profile, created = Profile.objects.get_or_create(user=request.user)

    profile.starred_lists.add(current_list)
    return JsonResponse({"success": True})


@login_required
def remove_star_list(request, list_id):
    try:
        current_list = ListOfProducts.objects.get(id=list_id)
    except ListOfProducts.DoesNotExist:
        return JsonResponse({"error": "List not found"}, status=404)

    profile, created = Profile.objects.get_or_create(user=request.user)

    profile.starred_lists.remove(current_list)

    return JsonResponse({"success": True})


def delete_item(request, item_id):
    if not request.user.is_authenticated:
        return _my_json_error_response("You must be logged in to do this operation", status=401)

    if request.method != 'POST':
        return _my_json_error_response("You must use a POST request for this operation", status=405)

    try:
        print(Product.objects.all())
        item = Product.objects.get(id=item_id)
    except ObjectDoesNotExist:
        return _my_json_error_response(f"Item with id={item_id} does not exist.", status=404)

    item.delete()

    list_id = item.list_of_products.id

    return get_products(request, list_id)


def get_products(request, list_id):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    response_data = []

    list = ListOfProducts.objects.get(id=list_id)
    try:
        for product in Product.objects.all().filter(list_of_products=list):
            product_item = {
                'user': {
                    'id': product.id,
                    'username': product.user.username,
                    'first_name': product.user.first_name,
                    'last_name': product.user.last_name
                },
                'name': product.name,
                'price': float(Decimal(product.price)),
                'brand': product.brand,
                'image_url': product.image_url,
                'product_url': product.product_url,
                'added_at': localtime(product.added_at).strftime('%Y-%m-%d %H:%M:%S'),
                'is_locked': product.is_locked,
                'cooldown_hours': product.remaining_cooldown_hours
            }
            response_data.insert(0, product_item)

        response_json = json.dumps(response_data)
    except Exception as e:
        print(f"Error in get_products view: {e}")
        return JsonResponse({'error': 'Something went wrong.'}, status=500)

    return HttpResponse(response_json, content_type='application/json')


@login_required
def view_list(request, id):
    context = {}
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    user_list = get_object_or_404(ListOfProducts, id=id)

    sort_by = request.GET.get('sort', 'added_at')
    valid_sort_options = ['added_at', '-added_at',
                          'name', '-name', 'price', '-price']

    if sort_by not in valid_sort_options:
        sort_by = 'added_at'

    context['user_list'] = user_list
    context['list_name'] = user_list.name

    products = Product.objects.order_by(sort_by)
    context['current_sort'] = sort_by
    context['products'] = products
    print('sorted products: ', products)

    pending_request = Notifications.objects.filter(
        sender=request.user,
        recipient=user_list.user,
        content_type=ContentType.objects.get_for_model(ListOfProducts),
        object_id=id
    ).exists()
    context['pending_request'] = pending_request

    if request.method == 'POST':
        formProduct = ProductForm(request.POST)

        if formProduct.is_valid() and "image_url" in request.POST:
            print("using manual")
            product = formProduct.save(commit=False)
            product.user = request.user

            try:
                list_of_products = ListOfProducts.objects.get(id=id)
                product.list_of_products = list_of_products 
            except ListOfProducts.DoesNotExist:
                messages.error(request, "List with ID does not exist.")

            product.save()

        elif "image_url" not in request.POST:
            print("using chat")
            formURL = URLForm(request.POST)
            if formURL.is_valid():
                product_url = formURL.cleaned_data['product_url']

                try:
                    response = requests.get(product_url)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    image_url = add_product(
                        formURL.cleaned_data['product_url'])
                    name = soup.find(
                        'h1', class_="product-name name-above-price")
                    price_div = soup.find('div', class_="product-price")
                    price = price_div.find('label', class_='visually-hidden')

                    price_fixed = re.search(r'[\d.]+', price.text)

                    match = re.search(
                        r'https://([a-zA-Z0-9-]+)\.com', product_url)

                    product = Product(
                        name=name.text.strip(),
                        price=price_fixed.group(),
                        brand=match.group(1),
                        image_url=image_url,
                        product_url=product_url,
                    )
                    product.user = request.user
                    try:
                        list_of_products = ListOfProducts.objects.get(id=id)
                        product.list_of_products = list_of_products  # Assign the list to the product
                        product.save()
                    except ListOfProducts.DoesNotExist:
                        messages.error(request, "List with ID does not exist.")

                except Exception:
                    messages.error(
                        request, "Form submission failed. Please try again.")
        else:
            messages.error(
                request, "Form submission failed. Please enter a valid URL.")

        context['form'] = ProductForm()
        context['form1'] = URLForm()

        return redirect('list', id=id)

    else:
        formProduct = ProductForm()
        formURL = URLForm()
        context['form'] = formProduct
        context['form1'] = formURL

    gm_key = CONFIG.get("GoogleMaps", "api_key")
    context['googlemaps_api'] = gm_key
    context['list_id'] = id

    if request.user in user_list.collaborators.all() or (request.user == user_list.user):
        print("this is my list")
        return render(request, 'list.html', context)
    else:
        return render(request, 'otheruserlist.html', context)


@csrf_exempt
@login_required
def track_click(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            url = data.get('url')
            if url:
                OutgoingLinkClick.objects.create(user=request.user, url=url)
                return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'invalid request'}, status=400)


@login_required
def create_list(request):
    if request.method == "POST":
        form = ListOfProductsForm(request.POST)

        source = request.META.get('HTTP_REFERER', '')

        if form.is_valid():
            new_list = form.save(commit=False)
            new_list.user = request.user
            new_list.save()
            return HttpResponseRedirect(source)

    else:
        form = ListOfProductsForm()

    return render(request, "create_list.html", {"form": form})


def get_lists(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    all_lists = ListOfProducts.objects.filter(
        user=request.user).order_by('-created_at')

    profile = Profile.objects.get(user=request.user)

    starred_lists = profile.starred_lists.all()

    response_data = []
    try:
        starred_data = []
        non_starred_data = []

        for list in all_lists:
            list_item = {
                'id': list.id,
                'name': list.name,
                'created_at': localtime(list.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                'user': list.user.username,
                'user_id': list.get_user_id(),
                'image_url': list.get_first_product_image_url(),
                'is_starred': list in starred_lists,
            }
            if list in starred_lists:
                starred_data.append(list_item)
            else:
                non_starred_data.append(list_item)

        response_data = starred_data + non_starred_data
        response_json = json.dumps(response_data)

    except Exception as e:
        print(f"Error in get_lists view: {e}")
        return JsonResponse({'error': 'Something went wrong.'}, status=500)

    return HttpResponse(response_json, content_type='application/json')


def get_all_lists(request):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    profile = Profile.objects.get(user=request.user)
    starred_lists = profile.starred_lists.all()

    all_lists = ListOfProducts.objects.filter(
        private=False).order_by('-created_at')

    response_data = []
    try:
        starred_data = []
        non_starred_data = []

        for list in all_lists:
            list_item = {
                'id': list.id,
                'name': list.name,
                'created_at': localtime(list.created_at).strftime('%Y-%m-%d %H:%M:%S'),
                'user': list.user.username,
                'user_id': list.get_user_id(),
                'image_url': list.get_first_product_image_url(),
                'is_starred': list in starred_lists,
            }
            if list in starred_lists:
                starred_data.append(list_item)
            else:
                non_starred_data.append(list_item)

        response_data = starred_data + non_starred_data
        response_json = json.dumps(response_data)

    except Exception as e:
        print(f"Error in get_all_lists view: {e}")
        return JsonResponse({'error': 'Something went wrong.'}, status=500)

    return HttpResponse(response_json, content_type='application/json')


@login_required
def profile_action(request):
    profile, created = Profile.objects.get_or_create(user=request.user)

    if not request.user.is_authenticated:
        return JsonResponse({"error": "User not authenticated"}, status=401)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile)

    if 'picture' not in request.session:
        request.session['picture'] = request.user.social_auth.get(
            provider='google-oauth2').extra_data['picture']

    click_stats = OutgoingLinkClick.objects.filter(
        user=request.user).values('url').annotate(total=models.Count('url'))
    context = {
        'form': form,
        'profile': profile,
        'click_stats': click_stats
    }

    user_lists = ListOfProducts.objects.filter(
        user=request.user)

    form = ListOfProductsForm()
    context['form'] = form
    context['user_lists'] = user_lists

    return render(request, 'my_profile.html', context)


@login_required
def other_profile_action(request, user_id):
    other_user = get_object_or_404(User, id=user_id)
    profile, created = Profile.objects.get_or_create(user=other_user)
    my_profile = Profile.objects.get(user=request.user)

    if profile in my_profile.followers.all() and my_profile in profile.followers.all():
        is_friends = True
    else:
        is_friends = False

    lists = ListOfProducts.objects.filter(user=other_user)

    context = {
        'other_user': other_user,
        'profile': profile,
        'is_friends': is_friends,
        'user': request.user,
        'lists': lists
    }
    return render(request, 'other_profile.html', context)


@login_required
def follower_action(request):
    context = {}
    return render(request, 'follower_stream.html', context)


def _my_json_error_response(message, status=200):
    response_json = '{"error": "' + message + '"}'
    return HttpResponse(response_json, content_type='application/json', status=status)


def add_product(URL):
    key = CONFIG.get("ChatGPT", "api_key")

    response = requests.get(URL)

    soup = BeautifulSoup(response.text, 'html.parser')
    images = soup.find_all('img')

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}"
    }

    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "You are given the HTML of all the images on a shopping website. Determine the product image and output the image source. You will output only plain text."
                    },
                    {
                        "type": "text",
                        "text": f"{images}"
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    response = requests.post(
        "https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    return response.json()['choices'][0]['message']['content']


def search_profiles(request):
    query = request.GET.get('q', '')
    if query:
        profiles = Profile.objects.filter(
            user__username__icontains=query).exclude(user=request.user)
        user_lists = ListOfProducts.objects.filter(
            name__icontains=query).exclude(user=request.user)

        result = [{'username': profile.user.username,
                   'user_id': profile.user.id} for profile in profiles]
        lists = [{'name': list.name, 'list_id': list.id}
                 for list in user_lists]
        return JsonResponse({'results': result, 'lists': lists})
    return JsonResponse({'results': [], 'lists': []})


def send_friend_requests(request, to_friend):
    profile = Profile.objects.get(user=request.user)
    to_befriend = Profile.objects.get(user__username=to_friend)

    if profile.user == to_befriend.user:
        return JsonResponse({'failure': 'Cannot send friend request to self'})

    if to_befriend in profile.sentrequests.all():
        return JsonResponse({'failure': 'Already sent request'})

    if profile in to_befriend.friendrequests.all():
        return JsonResponse({'failure': 'Already sent request'})

    if profile in to_befriend.sentrequests.all():
        return JsonResponse({'failure': 'Other user has sent you a request'})

    if to_befriend in profile.friendrequests.all():
        return JsonResponse({'failure': 'Other user has sent you a request'})

    profile.sentrequests.add(to_befriend)
    to_befriend.friendrequests.add(profile)

    profile.save()
    to_befriend.save()
    return JsonResponse({'success': 'Friend request sent successfully!'})


def get_friend_requests(request):
    profile = Profile.objects.get(user=request.user)
    friend_requests = profile.friendrequests.all()
    friend_requests_data = [req.user.username for req in friend_requests]
    return JsonResponse({'friend_requests': friend_requests_data})


def get_friend_list(request):
    profile = Profile.objects.get(user=request.user)
    friend_requests = profile.followers.all()

    result = [{'username': profile.user.username, 'user_id': profile.user.id}
              for profile in friend_requests]

    return JsonResponse({'friend_requests': result})


def get_sent_requests(request):
    profile = Profile.objects.get(user=request.user)
    friend_requests = profile.sentrequests.all()
    friend_requests_data = [req.user.username for req in friend_requests]
    return JsonResponse({'friend_requests': friend_requests_data})


def accept_request(request, to_friend):
    profile = Profile.objects.get(user=request.user)
    to_befriend = Profile.objects.get(user__username=to_friend)

    to_befriend.sentrequests.remove(profile)
    profile.friendrequests.remove(to_befriend)

    profile.followers.add(to_befriend)
    to_befriend.followers.add(profile)

    profile.save()
    to_befriend.save()
    return JsonResponse({'success': 'Friend request sent successfully!'})


def decline_request(request, to_friend):
    profile = Profile.objects.get(user=request.user)
    to_befriend = Profile.objects.get(user__username=to_friend)

    to_befriend.sentrequests.remove(profile)
    profile.friendrequests.remove(to_befriend)

    profile.save()
    to_befriend.save()
    return JsonResponse({'success': 'Friend request sent successfully!'})


def unfriend_action(request, to_friend):
    profile = Profile.objects.get(user=request.user)
    to_befriend = Profile.objects.get(user__username=to_friend)

    profile.followers.remove(to_befriend)
    to_befriend.followers.remove(profile)

    profile.save()
    to_befriend.save()

    return JsonResponse({'success': 'Unfriended successfully!'})


def is_friend_action(request, to_friend):
    profile = Profile.objects.get(user=request.user)
    to_befriend = Profile.objects.get(user__username=to_friend)

    if to_befriend in profile.followers.all() and profile in to_befriend.followers.all():
        return JsonResponse({'friends': True})
    elif to_befriend in profile.sentrequests.all() and profile in to_befriend.friendrequests.all():
        return JsonResponse({'sent': True})
    elif to_befriend in profile.friendrequests.all() and profile in to_befriend.sentrequests.all():
        return JsonResponse({'recieved': True})

    elif profile.user == to_befriend.user:
        return JsonResponse({'self': True})

    return JsonResponse({'not_friends': True})


def withdraw_request(request, to_friend):
    profile = Profile.objects.get(user=request.user)
    to_befriend = Profile.objects.get(user__username=to_friend)

    to_befriend.friendrequests.remove(profile)
    profile.sentrequests.remove(to_befriend)

    profile.save()
    to_befriend.save()
    return JsonResponse({'success': 'xyz'})


def notifications(request):
    context = {}
    notifications = Notifications.objects.filter(recipient=request.user)
    context['notifications'] = notifications
    return render(request, 'notifications.html', context)


def add_collaborator(request, list_id):
    user_list = get_object_or_404(ListOfProducts, id=list_id)

    if request.user in user_list.collaborators.all():
        return JsonResponse({
            'status': 'info',
            'message': 'You are already a collaborator.'
        }, status=200)

    existing_notification = Notifications.objects.filter(
        recipient=user_list.user,
        sender=request.user,
        content_type=ContentType.objects.get_for_model(user_list),
        object_id=user_list.id,
    ).exists()

    if existing_notification:
        return JsonResponse({
            'status': 'info',
            'message': 'A collaboration request has already been sent.'
        }, status=200)

    notification = Notifications.objects.create(
        recipient=user_list.user,
        sender=request.user,
        content_type=ContentType.objects.get_for_model(user_list),
        object_id=user_list.id,
        accepted=False,
    )

    print(f"Notification created: {notification.id}")

    return JsonResponse({
        'status': 'success',
        'message': 'Collaboration request sent successfully.'
    }, status=201)


@login_required
def accept_collaboration(request, notification_id):
    notification = get_object_or_404(Notifications, id=notification_id)
    context = {}

    if notification.recipient != request.user:
        response_data = {
            'error': 'You are not authorized to accept this request.'
        }
        return HttpResponse(json.dumps(response_data), content_type='application/json', status=403)

    notification.responded = True
    notification.accepted = True
    notification.save()

    list_of_products = notification.content_object
    if isinstance(list_of_products, ListOfProducts):
        list_of_products.collaborators.add(notification.sender)
        list_of_products.save()

        notifications = Notifications.objects.filter(recipient=request.user)
        context['notifications'] = notifications
        return render(request, "notifications.html", context)

    notifications = Notifications.objects.filter(recipient=request.user)
    context['notifications'] = notifications
    return render(request, "notifications.html", context)


def decline_collaboration(request, notification_id):
    notification = get_object_or_404(Notifications, id=notification_id)
    notification.responded = True

    if notification.recipient != request.user:
        return JsonResponse({'error': 'You are not authorized to accept this request.'}, status=403)
    return HttpResponseRedirect(reverse('notifications'))


def decline_request(request, to_friend):
    profile = Profile.objects.get(user=request.user)
    to_befriend = Profile.objects.get(user__username=to_friend)
    to_befriend.sentrequests.remove(profile)
    profile.friendrequests.remove(to_befriend)
    profile.save()
    to_befriend.save()
    return JsonResponse({'success': 'Friend request sent successfully!'})
