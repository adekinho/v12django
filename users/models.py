from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

# Create your models here.

class SearchRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_requests')
    city = models.CharField(max_length=100, blank=True)
    vin = models.CharField(max_length=100, blank=True)
    make = models.CharField(max_length=100, blank=True)
    model = models.CharField(max_length=100, blank=True)
    generation = models.CharField(max_length=100, blank=True)
    search = models.CharField(max_length=255, blank=True)
    condition = models.CharField(max_length=50, default='new')
    image = models.ImageField(upload_to='search_requests', blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.search} for {self.make} {self.model} by {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']

class UserActivity(models.Model):
    ACTIVITY_TYPES = (
        ('search', 'Search'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('profile_update', 'Profile Update'),
        ('other', 'Other'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_TYPES)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.activity_type} by {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'User activities'

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.ImageField(upload_to='profile_pics', default='profile_pics/default.png')
    phone_number = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class SellerRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_requests')
    city = models.CharField(max_length=100)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    generation = models.CharField(max_length=100, blank=True)
    part_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.part_name} for {self.make} {self.model} by {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']

class RequestResponse(models.Model):
    seller_request = models.ForeignKey(SellerRequest, on_delete=models.CASCADE, null=True, blank=True, related_name='responses')
    search_request = models.ForeignKey(SearchRequest, on_delete=models.CASCADE, null=True, blank=True, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_vin_matched = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    city = models.CharField(max_length=100)
    address = models.CharField(max_length=255)
    image = models.ImageField(upload_to='response_images', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.seller_request:
            return f"Response to seller request {self.seller_request.id} by {self.user.username}"
        else:
            return f"Response to search request {self.search_request.id} by {self.user.username}"
    
    class Meta:
        ordering = ['-created_at']

class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_messages')
    response = models.ForeignKey(RequestResponse, on_delete=models.SET_NULL, null=True, blank=True, related_name='messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Message from {self.sender.username} to {self.receiver.username}"
    
    class Meta:
        ordering = ['created_at']
