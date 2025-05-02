from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import UserRegisterForm, UserLoginForm
from .models import SearchRequest, UserActivity, UserProfile, SellerRequest, RequestResponse

# Create your views here.

def register_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            # Create a new user with the email as username
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password
            )
            
            # Create user profile
            UserProfile.objects.create(user=user)
            
            # Log activity
            UserActivity.objects.create(
                user=user,
                activity_type='other',
                description='Account created'
            )
            
            messages.success(request, 'Account created successfully! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    context = {
        'form': form,
        'recaptcha_site_key': 'YOUR_RECAPTCHA_SITE_KEY',  # Replace with your actual key
    }
    return render(request, 'users/register.html', context)

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password')
            
            # First try to authenticate with the email as username
            user = authenticate(username=email, password=password)
            
            # If that fails and email is 'admin', try authenticating with username='admin'
            if user is None and email == 'admin':
                user = authenticate(username='admin', password=password)
            
            if user is not None:
                login(request, user)
                
                # Log login activity
                UserActivity.objects.create(
                    user=user,
                    activity_type='login',
                    description='User logged in'
                )
                
                messages.success(request, 'You have been logged in successfully!')
                return redirect('home')  # Redirect to your home page
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = UserLoginForm()
    
    context = {
        'form': form,
        'recaptcha_site_key': 'YOUR_RECAPTCHA_SITE_KEY',  # Replace with your actual key
    }
    return render(request, 'users/login.html', context)

def logout_view(request):
    if request.user.is_authenticated:
        # Log logout activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='logout',
            description='User logged out'
        )
    
    logout(request)
    messages.success(request, 'You have been logged out successfully!')
    return redirect('login')

@login_required
def profile_view(request):
    # Get user's search history
    search_history = SearchRequest.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    # Get user's activities
    activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')[:15]
    
    context = {
        'search_history': search_history,
        'activities': activities,
    }
    
    return render(request, 'users/profile.html', context)

def results_view(request):
    # Get search parameters from request
    search_params = {
        'city': request.GET.get('city', ''),
        'vin': request.GET.get('vin', ''),
        'make': request.GET.get('make', ''),
        'model': request.GET.get('model', ''),
        'generation': request.GET.get('generation', ''),
        'search': request.GET.get('search', ''),
        'condition': request.GET.get('condition', 'new'),
    }
    
    # Check if this is a search request
    is_search_request = any(search_params.values())
    
    # Save search request if user is authenticated and it's a valid search
    if is_search_request and request.user.is_authenticated:
        # Create search request record
        search_request = SearchRequest.objects.create(
            user=request.user,
            city=search_params['city'],
            vin=search_params['vin'],
            make=search_params['make'],
            model=search_params['model'],
            generation=search_params['generation'],
            search=search_params['search'],
            condition=search_params['condition']
        )
        
        # Log search activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='search',
            description=f"Searched for {search_params['search']} - {search_params['make']} {search_params['model']}"
        )
    
    # Get search requests for the user
    active_searches = []
    if request.user.is_authenticated:
        active_searches = SearchRequest.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'search_params': search_params,
        'is_search_request': is_search_request,
        'active_searches': active_searches,
    }
    
    return render(request, 'users/results.html', context)

@login_required
def sell_view(request):
    # Get all seller requests
    seller_requests = SellerRequest.objects.all().order_by('-created_at')
    
    # Get unique cities, makes, models and generations for dropdowns
    cities = SellerRequest.objects.values_list('city', flat=True).distinct()
    makes = SellerRequest.objects.values_list('make', flat=True).distinct()
    models = SellerRequest.objects.values_list('model', flat=True).distinct()
    generations = SellerRequest.objects.values_list('generation', flat=True).distinct()
    
    # Filter requests if filters are applied
    city_filter = request.GET.get('city', '')
    make_filter = request.GET.get('make', '')
    model_filter = request.GET.get('model', '')
    generation_filter = request.GET.get('generation', '')
    
    if city_filter:
        seller_requests = seller_requests.filter(city=city_filter)
    if make_filter:
        seller_requests = seller_requests.filter(make=make_filter)
    if model_filter:
        seller_requests = seller_requests.filter(model=model_filter)
    if generation_filter:
        seller_requests = seller_requests.filter(generation=generation_filter)
    
    context = {
        'seller_requests': seller_requests,
        'cities': cities,
        'makes': makes,
        'models': models,
        'generations': generations,
    }
    
    return render(request, 'users/sell.html', context)

@login_required
def respond_view(request, request_id):
    # Get the seller request
    try:
        seller_request = SellerRequest.objects.get(id=request_id)
    except SellerRequest.DoesNotExist:
        messages.error(request, 'Request not found.')
        return redirect('sell')
    
    if request.method == 'POST':
        # Handle form submission
        description = request.POST.get('description', '')
        price = request.POST.get('price', '')
        is_vin_matched = request.POST.get('is_vin_matched', '') == 'on'
        is_new = request.POST.get('is_new', '') == 'on'
        city = request.POST.get('city', '')
        address = request.POST.get('address', '')
        
        # Validate required fields
        if price and city and address:
            try:
                price = float(price)
                # Create response
                response = RequestResponse.objects.create(
                    seller_request=seller_request,
                    user=request.user,
                    description=description,
                    price=price,
                    is_vin_matched=is_vin_matched,
                    is_new=is_new,
                    city=city,
                    address=address
                )
                
                # Log activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f"Responded to request for {seller_request.part_name}"
                )
                
                messages.success(request, 'Your response has been sent successfully!')
                return redirect('sell')
            except ValueError:
                messages.error(request, 'Please enter a valid price.')
        else:
            messages.error(request, 'Please fill all required fields.')
    
    context = {
        'seller_request': seller_request
    }
    
    return render(request, 'users/respond.html', context)

@login_required
def delete_search_view(request, search_id):
    # Only allow POST requests for deletion to prevent accidental deletions from GET requests
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for deletion')
        return redirect('results')
        
    try:
        # Get the search request
        search_request = SearchRequest.objects.get(id=search_id, user=request.user)
        
        # Store information for activity log before deletion
        search_info = f"{search_request.search} - {search_request.make} {search_request.model}"
        
        # Get a reference to the ID for verification
        request_id = search_request.id
        
        # Hard delete the record from the database
        search_request.delete()
        
        # Verify deletion by trying to fetch the record again
        deleted = not SearchRequest.objects.filter(id=request_id).exists()
        
        if deleted:
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='other',
                description=f"Permanently deleted search request for {search_info}"
            )
            
            messages.success(request, f'Search request #{request_id} was permanently deleted from the database')
        else:
            messages.error(request, 'Failed to delete the search request. Please try again.')
        
    except SearchRequest.DoesNotExist:
        messages.error(request, 'Search request not found!')
    
    return redirect('results')

@login_required
def update_search_view(request, search_id):
    try:
        search_request = SearchRequest.objects.get(id=search_id, user=request.user)
        
        if request.method == 'POST':
            # Update search request with new values
            search_request.city = request.POST.get('city', search_request.city)
            search_request.vin = request.POST.get('vin', search_request.vin)
            search_request.make = request.POST.get('make', search_request.make)
            search_request.model = request.POST.get('model', search_request.model)
            search_request.generation = request.POST.get('generation', search_request.generation)
            search_request.search = request.POST.get('search', search_request.search)
            search_request.condition = request.POST.get('condition', search_request.condition)
            search_request.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='other',
                description=f"Updated search request for {search_request.search} - {search_request.make} {search_request.model}"
            )
            
            messages.success(request, 'Search request updated successfully!')
            return redirect('results')
        
        context = {
            'search_request': search_request
        }
        
        return render(request, 'users/update_search.html', context)
        
    except SearchRequest.DoesNotExist:
        messages.error(request, 'Search request not found!')
        return redirect('results')
