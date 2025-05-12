from django.contrib.auth.models import User
from django.db import models

# Create your models here.

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_admin = models.BooleanField(default=True)

    def __str__(self):
        return self.user.username

class Book(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    category_type = (('Story', 'Story'), ('Fiction', 'Fiction'), ('Non-Fiction', 'Non-Fiction'), ('Novel', 'Novel'),
                     ('History', 'History'), ('Poetry', 'Poetry'), ('Cookbook', 'Cookbook'),
                     ('Drama', 'Drama'), ('Thriller', 'Thriller'), ('Biography', 'Biography'), ('Action', 'Action'),
                     ('Literature', 'Literature'), ('Adventure', 'Adventure'), ('Others', 'Others'))
    category = models.CharField(max_length=200, choices=category_type, blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True, default='images/default.jpg')
    review_choice = models.ForeignKey('Review', on_delete= models.CASCADE, blank=True, null=True)
    type = (('New', 'New'), ('Used', 'Used'), ('Academic', 'Academic'), ('Admission', 'Admission'))
    type_choice = models.CharField(max_length=100, choices=type, blank=True, null=True)
    donated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_time = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    sales_count = models.IntegerField(default=0) 
    average_rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.title
    
class Ebook(models.Model):
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True, default='images/default.jpg')
    price = models.IntegerField(blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True, blank=True, null=True)


    def __str__(self):
        return self.title

class Accessories(models.Model):
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    price = models.IntegerField(blank=True, null=True)
    quantity = models.IntegerField(blank=True, null=True)
    image = models.ImageField(upload_to='images/', blank=True, null=True, default='images/default.jpg')
    review_choice = models.ForeignKey('Review', on_delete= models.CASCADE, blank=True, null=True)
    donated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    date_time = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    sales_count = models.IntegerField(default=0)  
    average_rating = models.FloatField(default=0.0)

    def __str__(self):
        return self.title
    
class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    Book = models.ForeignKey(Book, on_delete=models.CASCADE, blank=True, null=True)
    acc = models.ForeignKey(Accessories, on_delete=models.CASCADE, blank=True, null=True)
    review = (('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'))
    review_choice = models.CharField(max_length=100, choices=review, blank=True, null=True)
    date_time = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.Book} Review: {self.review_choice}"    
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update the average rating for the associated book
        if self.Book:
            reviews = Review.objects.filter(Book=self.Book)
            total_rating = sum(int(review.review_choice) for review in reviews)
            average_rating = total_rating / reviews.count() if reviews.count() > 0 else 0
            self.Book.average_rating = average_rating
            self.Book.save()
        if self.acc:
            reviews = Review.objects.filter(acc=self.acc)
            total_rating = sum(int(review.review_choice) for review in reviews)
            average_rating = total_rating / reviews.count() if reviews.count() > 0 else 0
            self.acc.average_rating = average_rating
            self.acc.save()
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('delivered', 'Delivered'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE, blank=True, null=True)
    ebook = models.ForeignKey(Ebook, on_delete=models.CASCADE, blank=True, null=True)
    accessories = models.ForeignKey(Accessories, on_delete=models.CASCADE, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    date_time = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    def price(self):
        total_price = 0
        if self.book:
            total_price += self.book.price * self.quantity
        elif self.ebook:
            total_price += self.ebook.price 
        elif self.accessories:
            total_price += self.accessories.price * self.quantity
        return total_price
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.accessories:
            self.accessories.sales_count += self.quantity
            self.accessories.save()
        if self.book:
            self.book.sales_count += self.quantity
            self.book.save()


class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, null=True, blank=True, on_delete=models.CASCADE)
    accessories = models.ForeignKey(Accessories, null=True, blank=True, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def get_item_price(self):
        if self.book:
            return self.book.price * self.quantity
        elif self.accessories:
            return self.accessories.price * self.quantity
        return 0