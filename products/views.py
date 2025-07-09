import math
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Value, Q
from .forms import  *
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout as django_logout
from django.views.decorators.cache import never_cache
from django.views.decorators.cache import cache_control
from django.core.paginator import Paginator
import sys

sys.setrecursionlimit(150)


# Create your views here.

def useradmin(request):
    return render(request, template_name='user_or_admin.html')

def loginPage(request):
    return render(request, template_name='loginpage.html')

def main(request): # Or whatever your view is named (e.g., home_admin)
    # Start with all products
    products = Book.objects.all()

    # --- Get all unique categories for the dropdown ---
    categories = Book.objects.values_list('category', flat=True).distinct().order_by('category')

    # --- Filtering by Category ---
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category=category_filter)

    # --- Sorting by Price ---
    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    else:
        # Default sorting
        products = products.order_by('-date_time')

    context = {
        'products': products,
        'categories': categories,
        'current_category': category_filter,
        'current_sort': sort_option,
    }
    return render(request, 'home.html', context)

def register(request, user_type):
    form = CustomUserCreationForm()
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            #profile = Profile.objects.create(user=user)  # Use Profile here (assuming it's your model name)
            if user_type == 'customer':
                user.profile.is_admin = False
                user.profile.save()
                user.save()
            else:
                user.is_staff = True
                user.profile.is_admin = True
                user.profile.save()
                user.save()
            return redirect('login_user')
    context = {'form': form}
    return render(request, 'registration_form.html', context = context)

def login_user(request):
    if request.method == 'POST':
        form = AuthenticationForm(request=request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                if hasattr(user, 'profile') and user.profile.is_admin:
                    return redirect('main')  # Redirect to admin dashboard
                else:
                    return redirect('home')  # Redirect to customer dashboard
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'loginpage.html', {'form': form})

def logout_admin(request):
    logout(request)
    return redirect('useradmin')

@login_required
def upload_book(request):
    form = BookForm()
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('main')

    context = {'form': form}
    return render(request, template_name='upload_book.html', context=context)

def book_details(request, id):
    products = Book.objects.get(pk=id)
    reviews = Review.objects.filter(Book=id)
    average_review = calculate_average_review(reviews)
    context = {'products': products, 'average_review': average_review}
    return render(request, template_name='book_details.html', context=context)

@login_required
def update_book(request, id):
    book = Book.objects.get(pk=id)
    form = BookForm(instance=book)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            return redirect('main')
    context = {'form': form}
    return render(request, template_name='upload_book.html', context=context)

@login_required
def delete_book(request, id):
    book_to_delete = Book.objects.get(pk=id)
    if request.method == 'POST':
        book_to_delete.delete()
        return redirect(request.META.get('HTTP_REFERER', 'main'))
    
def search(request):
    query = request.GET.get('q')
    if query:
        book_results = Book.objects.filter(title__contains=query).annotate(item_type=Value(value='book'))
        ebook_results = Ebook.objects.filter(title__contains=query).annotate(item_type=Value(value='ebook'))
        accessories_results = Accessories.objects.filter(title__contains=query).annotate(
            item_type=Value(value='accessories'))

        search_results = list(book_results) + list(ebook_results) + list(accessories_results)
    else:
        search_results = None

    return render(request, template_name='search_results.html', context={'search_results': search_results, 'query': query})

@login_required
def upload_ebook(request):
    form = EBookForm()
    if request.method == 'POST':
        form = EBookForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('ebook')
    context = {'form': form}
    return render(request, template_name='upload_ebook.html', context=context)

@login_required
def upload_accessories(request):
    form = AccessoriesForm()
    if request.method == 'POST':
        form = AccessoriesForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('accessories')
    context = {'form': form}
    return render(request, template_name='upload_accessories.html', context=context)

def ebooks(request): # Or whatever your view is named (e.g., ebook)
    # Start with all e-books
    products = Ebook.objects.all()

    # --- Sorting by Price ---
    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    else:
        # Default sorting
        products = products.order_by('-date_time')

    context = {
        'products': products,
        'current_sort': sort_option,
    }
    return render(request, 'ebook.html', context)
@login_required
def delete_ebook(request, id):
    ebook_to_delete = Ebook.objects.get(pk=id)
    if request.method == 'POST':
        ebook_to_delete.delete()
        return redirect(request.META.get('HTTP_REFERER', 'ebook'))

@login_required
def update_ebook(request, id):
    EBook = Ebook.objects.get(pk=id)
    form = EBookForm(instance=EBook)
    if request.method == 'POST':
        form = EBookForm(request.POST, request.FILES, instance=EBook)
        if form.is_valid():
            form.save()
            return redirect('ebook')
    context = {'form': form}
    return render(request, template_name='upload_ebook.html', context=context)

def ebook_details(request, id):
    products = Ebook.objects.get(pk=id)
    context = {'products': products}
    return render(request, template_name='ebook_details.html', context=context)

def accessories(request): # Or whatever your view is named (e.g., accessories)
    # Start with all accessories
    products = Accessories.objects.all()

    # --- Sorting by Price ---
    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    else:
        # Default sorting
        products = products.order_by('-date_time')

    context = {
        'products': products,
        'current_sort': sort_option,
    }
    return render(request, 'accessories.html', context)

def accessories_details(request, id):
    products = Accessories.objects.get(pk=id)
    reviews = Review.objects.filter(acc = id)
    average_review = calculate_average_review(reviews)
    context = {'products': products, 'average_review': average_review}
    return render(request, template_name='accessories_details.html', context=context)

@login_required
def update_accessories(request, id):
    accessories = Accessories.objects.get(pk=id)
    form = AccessoriesForm(instance=accessories)
    if request.method == 'POST':
        form = AccessoriesForm(request.POST, request.FILES, instance=accessories)
        if form.is_valid():
            form.save()
            return redirect('accessories')
    context = {'form': form}
    return render(request, template_name='upload_accessories.html', context=context)

@login_required
def delete_accessories(request, id):
    accessories = Accessories.objects.get(pk=id)
    if request.method == 'POST':
        accessories.delete()
        return redirect(request.META.get('HTTP_REFERER', 'accessories'))


def calculate_average_review(reviews):
    total_score = 0
    num_reviews = 0
    for review in reviews:
        if review.review_choice:
            try:
                total_score += int(review.review_choice)
                num_reviews += 1
            except ValueError:
                pass
    if num_reviews > 0:
        avg = total_score / num_reviews
        return f"{avg:.1f}" 
    else:
        return 0
    
def usedBook(request):
    # Or whatever your view is named (e.g., usedBook)
    # Start with all used books. Adjust the filter if you identify them differently.
    products = Book.objects.filter(type_choice='Used')

    # --- Get all unique categories from the used books for the dropdown ---
    categories = products.values_list('category', flat=True).distinct().order_by('category')

    # --- Filtering by Category ---
    category_filter = request.GET.get('category', '')
    if category_filter:
        products = products.filter(category=category_filter)

    # --- Sorting by Price ---
    sort_option = request.GET.get('sort', '')
    if sort_option == 'price_asc':
        products = products.order_by('price')
    elif sort_option == 'price_desc':
        products = products.order_by('-price')
    else:
        # Default sorting
        products = products.order_by('-date_time')

    context = {
        'products': products,
        'categories': categories,
        'current_category': category_filter,
        'current_sort': sort_option,
    }
    return render(request, 'usedBook.html', context)


def ordered_items(request):
        # --- Performance Optimization ---
    # Use select_related to pre-fetch related user and product data in a single query,
    # preventing hundreds of extra database hits.
    order_list = Order.objects.select_related(
        'user', 'book', 'ebook', 'accessories'
    ).order_by('-date_time')

    # --- Get Dashboard Stats ---
    total_orders = order_list.count()
    pending_orders_count = order_list.filter(status='pending').count()
    delivered_orders_count = order_list.filter(status='delivered').count()

    # --- Search Logic ---
    query = request.GET.get('q', '')
    if query:
        order_list = order_list.filter(
            Q(user__username__icontains=query) |
            Q(book__title__icontains=query) |
            Q(ebook__title__icontains=query) |
            Q(accessories__title__icontains=query)
        )

    # --- Status Filter Logic ---
    status_filter = request.GET.get('status', '')
    if status_filter in ['pending', 'delivered']:
        order_list = order_list.filter(status=status_filter)

    # --- Pagination ---
    paginator = Paginator(order_list, 10) # Show 10 orders per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj, # Pass the paginated list of orders
        'total_orders': total_orders,
        'pending_orders': pending_orders_count,
        'delivered_orders': delivered_orders_count,
        'query': query,
        'current_status': status_filter,
    }
    return render(request, 'ordered_items.html', context)

# You will also need the view to handle the status update
def update_order_status(request, id):
    if request.method == 'POST':
        order = Order.objects.get(id=id)
        order.status = request.POST.get('status')
        order.save()
    return redirect('ordered_items')
