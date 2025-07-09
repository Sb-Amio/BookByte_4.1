import math
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.urls import reverse
from products.models import *
from django.contrib.auth import logout
from django.db.models import Value, Q
from products.forms import *
from django.contrib import messages
from django.contrib.auth.decorators import login_required

@login_required
def home(request): # Or whatever your view is named
    # Start with all books
    books = Book.objects.all()

    # --- 1. Get all unique categories for the dropdown ---
    # We get a flat list of unique category names from the database.
    categories = Book.objects.values_list('category', flat=True).distinct().order_by('category')

    # --- 2. Filtering by Category ---
    category_filter = request.GET.get('category', '') # Get the selected category
    if category_filter: # If a category is selected (and not empty)
        books = books.filter(category=category_filter)

    # --- 3. Sorting by Price ---
    sort_option = request.GET.get('sort', '') # Get the selected sort option
    if sort_option == 'price_asc':
        books = books.order_by('price')
    elif sort_option == 'price_desc':
        books = books.order_by('-price')
    else:
        # Default sorting, e.g., by newest first
        books = books.order_by('-date_time')

    context = {
        'book': books, # Pass the filtered & sorted list of books
        'categories': categories, # Pass the list of all available categories
        'current_category': category_filter, # Pass back the selected category for the form
        'current_sort': sort_option, # Pass back the selected sort option for the form
    }
    return render(request, 'home_user.html', context)

@login_required
def logout_user(request):
    logout(request)
    return redirect('book_non')

@login_required
def book_details_user(request, id):
    products = Book.objects.get(pk=id)
    reviews = Review.objects.filter(Book = id)
    average_review = calculate_average_review(reviews)
    context = {'products': products, 'average_review': average_review}
    return render(request, template_name='book_details_user.html', context=context)

@login_required
def search_user(request):
    query = request.GET.get('q')
    search_results = []  # Initialize as an empty list

    if query:
        # --- CORRECTED BOOK SEARCH ---
        # Search directly in the 'author' CharField.
        book_results = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct().annotate(item_type=Value(value='home')) # .distinct() prevents duplicates

        # --- EBOOK AND ACCESSORIES SEARCH ---
        # Note: Your Ebook model also has an author CharField. Let's search it too.
        ebook_results = Ebook.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct().annotate(item_type=Value(value='ebook_user'))
        
        accessories_results = Accessories.objects.filter(
            title__icontains=query
        ).annotate(item_type=Value(value='accessories_user'))

        # Combine the results
        search_results = list(book_results) + list(ebook_results) + list(accessories_results)

    context = {
        'search_results': search_results,
        'query': query
    }
    return render(request, 'search_results_user.html', context)

def live_search_suggestions_user(request):
    """
    This view handles the AJAX requests for search suggestions.
    It returns results in JSON format.
    """
    query = request.GET.get('q', '').strip()
    suggestions = []
    
    # Only search if the query has 2 or more characters
    if len(query) >= 2:
        # Limit the number of results to keep the suggestions list clean
        limit = 5 
        
        # Search Books
        book_results = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct()[:limit]
        
        for item in book_results:
            suggestions.append({
                'title': item.title,
                'type': 'Book',
                # Use reverse() to generate the correct URL dynamically
                'url': reverse('book_details_user', args=[item.id]) 
            })

        # Search E-books
        ebook_results = Ebook.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct()[:limit]

        for item in ebook_results:
            suggestions.append({
                'title': item.title,
                'type': 'E-Book',
                'url': reverse('ebook_details_user', args=[item.id]) # Replace with your ebook detail URL if you have one
            })

        # Search Accessories
        accessories_results = Accessories.objects.filter(
            title__icontains=query
        )[:limit]

        for item in accessories_results:
             suggestions.append({
                'title': item.title,
                'type': 'Accessory',
                'url': reverse('accessories_details_user', args=[item.id]) # Replace with your accessory detail URL if you have one
            })

    # Return the suggestions as a JSON response
    return JsonResponse({'suggestions': suggestions})

@login_required
def create_order_book(request, id):
    book_ins = Book.objects.get(pk=id)
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        if form.is_valid():
            order = form.save(commit=False)
            order.book = book_ins
            order.user = request.user
            ordered_quantity = form.cleaned_data['quantity']
            if book_ins.quantity < ordered_quantity:
                messages.error(request, 'Insufficient quantity available.')
                return redirect('my_cart')
            else:
                book_ins.quantity -= ordered_quantity
                book_ins.save()
            order.save()

            # Remove the corresponding cart item after placing the order
            CartItem.objects.filter(user=request.user, book=book_ins).delete()

            return redirect('my_orders')
    else:
        form = OrderForm()
    context = {'form': form, 'book': book_ins}
    return render(request, template_name='order_form_book.html', context=context)

@login_required
def my_orders(request):
    order_ins = Order.objects.filter(user=request.user).order_by('-date_time')
    context = {'order_ins': order_ins}
    return render(request, template_name='my_orders.html', context=context)

@login_required
def my_reviews(request):
    review_ins = Review.objects.filter(user=request.user)
    context = {'review_ins': review_ins}
    return render(request, template_name='my_reviews.html', context=context)

@login_required
def giveReview_Book(request, id):
    product = get_object_or_404(Book, id=id)
    if request.method == 'POST':
        form = ReviewForm(request.POST, request.FILES)
        if form.is_valid():
            # Delete all previous reviews by this user for this book
            Review.objects.filter(user=request.user, Book=product).delete()
            # Save the new one
            review = form.save(commit=False)
            review.user = request.user
            review.Book = product
            review.save()
            return redirect('my_orders')
    else:
        # Optional: Show existing review if it exists (for editing)
        existing_review = Review.objects.filter(user=request.user, Book=product).first()
        form = ReviewForm(instance=existing_review)
    context = {'form': form, 'product': product}
    return render(request, 'reviewform.html', context)


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

@login_required
def accessories_user(request): # Or whatever your view is named
    # Start with all accessories
    accessories = Accessories.objects.all()

    # --- Sorting by Price ---
    sort_option = request.GET.get('sort', '') # Get the selected sort option
    if sort_option == 'price_asc':
        accessories = accessories.order_by('price')
    elif sort_option == 'price_desc':
        accessories = accessories.order_by('-price')
    else:
        # Default sorting, e.g., by newest first
        accessories = accessories.order_by('-date_time')

    context = {
        'accessories_ins': accessories, # Pass the sorted list of accessories
        'current_sort': sort_option, # Pass back the selected sort option for the form
    }
    return render(request, 'accessories_user.html', context)

@login_required
def accessories_details_user(request, id):
    accessories_ins = Accessories.objects.get(pk=id)
    reviews = Review.objects.filter(acc=id)
    average_review = calculate_average_review(reviews)
    context = {'accessories_ins': accessories_ins, 'average_review': average_review}
    return render(request, template_name='accessories_details_user.html', context=context)


@login_required
def create_order_accessories(request, id):
    acc_ins = Accessories.objects.get(pk=id)
    if request.method == 'POST':
        form = OrderForm(request.POST, request.FILES)
        if form.is_valid():
            order = form.save(commit=False)
            order.accessories = acc_ins
            order.user = request.user
            ordered_quantity = form.cleaned_data['quantity']
            if acc_ins.quantity < ordered_quantity:
                messages.error(request, 'Insufficient quantity available.')
                return redirect('my_cart')
            else:
                acc_ins.quantity -= ordered_quantity
                acc_ins.save()
            order.save()
            CartItem.objects.filter(user=request.user, accessories=acc_ins).delete()
            return redirect('my_orders')
        
    else:
        form = OrderForm()

    context = {'form': form, 'Accessories': acc_ins}
    return render(request, template_name='order_form_book.html', context=context)

@login_required
def ebook_user(request): # Or whatever your view is named
    # Start with all e-books
    ebooks = Ebook.objects.all()

    # --- Sorting by Price ---
    sort_option = request.GET.get('sort', '') # Get the selected sort option
    if sort_option == 'price_asc':
        ebooks = ebooks.order_by('price')
    elif sort_option == 'price_desc':
        ebooks = ebooks.order_by('-price')
    else:
        # Default sorting, e.g., by newest first
        ebooks = ebooks.order_by('-date_time')

    context = {
        'ebook': ebooks, # Pass the sorted list of e-books
        'current_sort': sort_option, # Pass back the selected sort option for the form
    }
    return render(request, 'ebook_user.html', context)

@login_required
def ebook_details_user(request, id):
    products = Ebook.objects.get(pk=id)
    context = {'products': products}
    return render(request, template_name='ebook_details_user.html', context=context)

@login_required
def usedBook_user(request): # Or whatever your view is named
    # Start with all used books. Adjust the filter if you identify them differently.
    products = Book.objects.filter(type_choice='Used')

    # --- Get all unique categories for the dropdown ---
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
    return render(request, 'usedBook_user.html', context)


@login_required
def donate_book(request):
    if request.method == 'POST':
        form = DonateBookForm(request.POST, request.FILES)
        if form.is_valid():
            book = form.save(commit=False)
            book.type_choice = 'Used'
            book.donated_by = request.user
            book.save()
            return redirect('usedBook_user')
    else:
        form = DonateBookForm()

    return render(request, 'donate_book.html', {'form': form})

@login_required
def my_donations(request):
    donated_books = Book.objects.filter(donated_by=request.user).order_by('-date_time')
    context = {'donated_books': donated_books}
    return render(request, 'my_donation.html', context)

@login_required
def add_to_cart_book(request, id):
    book = get_object_or_404(Book, id=id)
    if book.donated_by == request.user:
        return redirect(request.META.get('HTTP_REFERER', 'userBook_user'))
    cart_item, created = CartItem.objects.get_or_create(user=request.user, book=book)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect(request.META.get('HTTP_REFERER', 'userBook_user'))

@login_required
def add_to_cart_accessories(request, id):
    accessories = get_object_or_404(Accessories, id=id)
    if accessories.donated_by == request.user:
        return redirect(request.META.get('HTTP_REFERER', 'accessories_user'))
    cart_item, created = CartItem.objects.get_or_create(user=request.user, accessories=accessories)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect(request.META.get('HTTP_REFERER', 'accessories_user'))

@login_required
def view_cart(request):
    cart_items = CartItem.objects.filter(user=request.user).order_by('-added_at')
    total_price = sum(item.get_item_price() for item in cart_items)
    context = {'cart_items': cart_items, 'total_price': total_price}
    return render(request, 'my_cart.html', context=context)

@login_required
def admission_user(request):
    products = Book.objects.filter(type_choice='Admission').order_by('-date_time')
    context = {'products': products}
    return render(request, template_name='admission_user.html', context=context)

@login_required
def academic_user(request):
    products = Book.objects.filter(type_choice='Academic').order_by('-date_time')
    context = {'products': products}
    return render(request, template_name='academic_user.html', context=context)



def get_recommended_books(limit=3):
    best_selling_books = Book.objects.filter(sales_count__gt=10).order_by('-sales_count')[:limit]
    highly_rated_books = Book.objects.filter(average_rating__gt=3).order_by('-average_rating')[:limit]
    recommended_books = list(set(best_selling_books) | set(highly_rated_books))
    recommended_books = [book for book in recommended_books if book.average_rating >= 3 and book.sales_count >= 10]
    return recommended_books[:limit]  # Limit the number of recommendations


def get_recommended_accessories(limit=3):
    best_selling_accessories = Accessories.objects.filter(sales_count__gt=10).order_by('-sales_count')[:limit]
    highly_rated_accessories = Accessories.objects.filter(average_rating__gt=3).order_by('-average_rating')[:limit]
    recommended_accessories = list(set(best_selling_accessories) | set(highly_rated_accessories))
    recommended_accessories = [accessory for accessory in recommended_accessories if accessory.average_rating >= 3 and accessory.sales_count >= 10]
    
    return recommended_accessories[:limit]  # Limit the number of recommendations


def recommendation(request):
    recommended_books = get_recommended_books()
    recommended_accessories = get_recommended_accessories()
    context = {'recommended_books': recommended_books,'recommended_accessories': recommended_accessories}
    return render(request, 'recomendation.html', context=context)


def chat_bot(request):
    return render(request, 'gemini.html')

def find_book(request):
    return render(request, 'gemeni-image.html')

@login_required
def edit_book(request, id):
    book = get_object_or_404(Book, pk=id)
    if request.user != book.donated_by:
        return redirect('home')  # prevent others from editing
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, instance=book)
        if form.is_valid():
            form.save()
            return redirect('home')  # or redirect to detail view
    else:
        form = BookForm(instance=book)
    context =  {'form': form, 'book': book}
    return render(request, 'donate_book.html',context=context)

@login_required
def cancel_order(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)

    if order.status == 'pending':
        # Restore stock for the correct product type
        if order.book:
            order.book.quantity += order.quantity
            order.book.save()
        elif order.ebook:
            order.ebook.quantity += order.quantity
            order.ebook.save()
        elif order.accessories:
            order.accessories.quantity += order.quantity
            order.accessories.save()
        order.delete()
    return redirect('my_orders')
