import math
from django.db.models import Q, Value
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from products.models import *

# Create your views here.

def book_non(request):
    book = Book.objects.exclude(type_choice='Used')
    context = {'book': book}
    return render(request, 'home_non.html',context=context)

def book_details_non(request, id):
    products = Book.objects.get(pk=id)
    reviews = Review.objects.filter(Book = id)
    average_review = calculate_average_review(reviews)

    context = {'products': products, 'average_review': average_review}
    return render(request, template_name='book_details_non.html', context=context)

def search_non(request):
    query = request.GET.get('q')
    search_results = []  # Initialize as an empty list

    if query:
        # --- CORRECTED BOOK SEARCH ---
        # Search directly in the 'author' CharField.
        book_results = Book.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct().annotate(item_type=Value(value='book_non')) # .distinct() prevents duplicates

        # --- EBOOK AND ACCESSORIES SEARCH ---
        # Note: Your Ebook model also has an author CharField. Let's search it too.
        ebook_results = Ebook.objects.filter(
            Q(title__icontains=query) | Q(author__icontains=query)
        ).distinct().annotate(item_type=Value(value='ebook_non'))
        
        accessories_results = Accessories.objects.filter(
            title__icontains=query
        ).annotate(item_type=Value(value='accessories_non'))

        # Combine the results
        search_results = list(book_results) + list(ebook_results) + list(accessories_results)

    context = {
        'search_results': search_results,
        'query': query
    }
    return render(request, 'search_results_non.html', context)


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
    
def accessories_non(request):
    accessories_ins = Accessories.objects.all()
    context = {'accessories_ins': accessories_ins}
    return render(request, template_name='accessories_non.html', context=context)

def accessories_details_non(request, id):
    products = Accessories.objects.get(pk=id)
    reviews = Review.objects.filter(acc=id)
    average_review = calculate_average_review(reviews)
    context = {'products': products, 'average_review': math.ceil(average_review)}
    return render(request, template_name='accessories_details_non.html', context=context)

def ebook_details_non(request, id):
    products = Ebook.objects.get(pk=id)
    context = {'products': products}
    return render(request, template_name='ebook_details_non.html', context=context)

def ebook_non(request):
    ebook = Ebook.objects.all()
    context = {'ebook': ebook}
    return render(request, 'ebook_non.html', context=context)

def usedBook_non(request):
    products = Book.objects.filter(type_choice='Used')
    context = {'products': products}
    return render(request, template_name='usedBook_non.html', context=context)

