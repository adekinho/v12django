from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm, SearchRequestForm, RequestResponseForm
from .models import SearchRequest, UserActivity, UserProfile, SellerRequest, RequestResponse, Message

# Create your views here.

def home_view(request):
    # Get all active search requests from all users
    # If user is authenticated, exclude their own requests
    if request.user.is_authenticated:
        search_requests = SearchRequest.objects.filter(active=True).exclude(user=request.user).order_by('-created_at')[:5]
    else:
        search_requests = SearchRequest.objects.filter(active=True).order_by('-created_at')[:5]
    
    # Get all seller requests
    seller_requests = SellerRequest.objects.all().order_by('-created_at')[:5]
    
    # Initialize the search request form
    form = SearchRequestForm()
    
    context = {
        'search_requests': search_requests,
        'seller_requests': seller_requests,
        'form': form,
    }
    
    return render(request, 'users/home.html', context)

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
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='profile_update',
                description='Updated profile information'
            )
            
            messages.success(request, 'Ваш профиль был успешно обновлен!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'user_profile': profile,
    }
    
    return render(request, 'users/profile.html', context)

@login_required
def results_view(request):
    # Initialize variables to avoid UnboundLocalError
    city = ''
    vin = ''
    make = ''
    model = ''
    generation = ''
    search = ''
    condition = 'new'
    
    # Get all search requests for the logged-in user
    search_requests = SearchRequest.objects.filter(user=request.user).order_by('-created_at')
    
    # Get all responses to the user's search requests
    # Use select_related to efficiently fetch related search_request data
    responses = RequestResponse.objects.filter(
        search_request__user=request.user
    ).select_related('search_request', 'user').order_by('-created_at')
    
    # Handle form submission with image upload
    if request.method == 'POST':
        form = SearchRequestForm(request.POST, request.FILES)
        if form.is_valid():
            # Create a new search request but don't save to DB yet
            search_request = form.save(commit=False)
            search_request.user = request.user
            search_request.active = True
            
            # If condition is 'any', set it to empty string to match all conditions
            if search_request.condition == 'any':
                search_request.condition = ''
                
            search_request.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='search',
                description=f"Searched for {search_request.search} - {search_request.make} {search_request.model}"
            )
            
            messages.success(request, 'Запрос успешно создан!')
    else:
        # Handle GET request with search parameters
        city = request.GET.get('city', '')
        vin = request.GET.get('vin', '')
        make = request.GET.get('make', '')
        model = request.GET.get('model', '')
        generation = request.GET.get('generation', '')
        search = request.GET.get('search', '')
        condition = request.GET.get('condition', 'new')
        
        # If form is submitted with search parameters, create a new search request
        if search:
            # Create initial data for the form
            initial_data = {
                'city': city,
                'vin': vin,
                'make': make,
                'model': model,
                'generation': generation,
                'search': search,
                'condition': condition
            }
            form = SearchRequestForm(initial=initial_data)
            
            # Create a new search request
            # If condition is 'any', set it to empty string to match all conditions
            condition_value = '' if condition == 'any' else condition
            
            search_request = SearchRequest.objects.create(
                user=request.user,
                city=city,
                vin=vin,
                make=make,
                model=model,
                generation=generation,
                search=search,
                condition=condition_value,
                active=True
            )
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='search',
                description=f"Searched for {search} - {make} {model}"
            )
        else:
            form = SearchRequestForm()
    
    # Prepare context
    context = {
        'city': city,
        'vin': vin,
        'make': make,
        'model': model,
        'generation': generation,
        'search': search,
        'condition': condition,
        'search_requests': search_requests,
        'active_searches': search_requests.filter(active=True),  # Add active searches explicitly
        'responses': responses,
    }
    
    return render(request, 'users/results.html', context)

@login_required
def sell_view(request):
    # Get filter parameters
    city_filter = request.GET.get('city', '')
    make_filter = request.GET.get('make', '')
    model_filter = request.GET.get('model', '')
    generation_filter = request.GET.get('generation', '')
    
    # Get all seller requests
    seller_requests = SellerRequest.objects.all().order_by('-created_at')
    
    # Get all active search requests from all users EXCEPT the current user
    search_requests = SearchRequest.objects.filter(active=True).exclude(user=request.user).order_by('-created_at')
    
    # Apply filters if provided
    if city_filter:
        seller_requests = seller_requests.filter(city=city_filter)
        search_requests = search_requests.filter(city=city_filter)
    if make_filter:
        seller_requests = seller_requests.filter(make=make_filter)
        search_requests = search_requests.filter(make=make_filter)
    if model_filter:
        seller_requests = seller_requests.filter(model=model_filter)
        search_requests = search_requests.filter(model=model_filter)
    if generation_filter:
        seller_requests = seller_requests.filter(generation=generation_filter)
        search_requests = search_requests.filter(generation=generation_filter)
    
    # Get unique values for filter dropdowns
    cities = SearchRequest.objects.values_list('city', flat=True).distinct()
    makes = SearchRequest.objects.values_list('make', flat=True).distinct()
    models = SearchRequest.objects.values_list('model', flat=True).distinct()
    generations = SearchRequest.objects.values_list('generation', flat=True).distinct()
    
    context = {
        'seller_requests': seller_requests,
        'search_requests': search_requests,
        'cities': cities,
        'makes': makes,
        'models': models,
        'generations': generations,
    }
    
    return render(request, 'users/sell.html', context)

@login_required
def respond_view(request, request_id):
    # Try to get the seller request first
    seller_request = None
    search_request = None
    request_type = 'seller'
    
    try:
        seller_request = SellerRequest.objects.get(id=request_id)
    except SellerRequest.DoesNotExist:
        # If seller request not found, try to get search request
        try:
            search_request = SearchRequest.objects.get(id=request_id)
            request_type = 'search'
        except SearchRequest.DoesNotExist:
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
        image = request.FILES.get('image', None)
        
        # Validate required fields
        if price and city and address:
            try:
                price = float(price)
                # Create response based on request type
                if request_type == 'seller':
                    response = RequestResponse.objects.create(
                        seller_request=seller_request,
                        user=request.user,
                        description=description,
                        price=price,
                        is_vin_matched=is_vin_matched,
                        is_new=is_new,
                        city=city,
                        address=address,
                        image=image
                    )
                else:  # search request
                    response = RequestResponse.objects.create(
                        search_request=search_request,
                        user=request.user,
                        description=description,
                        price=price,
                        is_vin_matched=is_vin_matched,
                        is_new=is_new,
                        city=city,
                        address=address,
                        image=image
                    )
                
                # Log activity
                if request_type == 'seller':
                    activity_description = f"Responded to seller request for {seller_request.part_name}"
                else:
                    activity_description = f"Responded to search request for {search_request.search}"
                
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=activity_description
                )
                
                messages.success(request, 'Your response has been submitted successfully!')
                
                # Redirect to results page if it's a search request response
                if request_type == 'search':
                    return redirect('results')
                else:
                    return redirect('sell')
            except ValueError:
                messages.error(request, 'Please enter a valid price.')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    # Prepare context based on request type
    if request_type == 'seller':
        context = {
            'request': seller_request,
            'request_type': 'seller',
        }
    else:
        context = {
            'request': search_request,
            'request_type': 'search',
        }
    
    return render(request, 'users/respond.html', context)

@login_required
def delete_search_view(request, search_id):
    # Only allow POST requests for deletion to prevent accidental deletions from GET requests
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for deletion')
        return redirect('results')
    
    try:
        # Debug info before deletion
        all_requests = SearchRequest.objects.filter(user=request.user)
        request_ids = [req.id for req in all_requests]
        print(f"Before deletion - User: {request.user.username}, Request IDs: {request_ids}")
        
        # Delete ALL search requests for this user
        count = all_requests.count()
        all_requests.delete()
        
        # Verify deletion
        remaining = SearchRequest.objects.filter(user=request.user).count()
        print(f"After deletion - Remaining requests: {remaining}")
        
        if remaining > 0:
            # Force delete any remaining requests
            print("Forcing deletion of remaining requests...")
            SearchRequest.objects.filter(user=request.user).delete()
            
            # Double-check
            final_count = SearchRequest.objects.filter(user=request.user).count()
            print(f"Final check - Remaining requests: {final_count}")
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            activity_type='other',
            description=f"Permanently deleted all search requests ({count} total)"
        )
        
        messages.success(request, f'Successfully deleted all your search requests ({count} total)')
        
    except Exception as e:
        print(f"Error in delete_search_view: {str(e)}")
        messages.error(request, f'Error deleting search requests: {str(e)}')
    
    return redirect('results')

@login_required
def delete_seller_request_view(request, request_id):
    # Only allow POST requests for deletion to prevent accidental deletions from GET requests
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for deletion')
        return redirect('sell')
    
    try:
        # Get the seller request
        seller_request = SellerRequest.objects.get(id=request_id, user=request.user)
        
        # Store information for activity log before deletion
        request_info = f"{seller_request.part_name} - {seller_request.make} {seller_request.model}"
        
        # Get a reference to the ID for verification
        request_id = seller_request.id
        
        # Hard delete the record from the database
        seller_request.delete()
        
        # Verify deletion by trying to fetch the record again
        deleted = not SellerRequest.objects.filter(id=request_id).exists()
        
        if deleted:
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='other',
                description=f"Permanently deleted seller request for {request_info}"
            )
            
            messages.success(request, f'Seller request #{request_id} was permanently deleted from the database')
        else:
            messages.error(request, 'Failed to delete the seller request. Please try again.')
        
    except SellerRequest.DoesNotExist:
        messages.error(request, 'Seller request not found!')
    
    return redirect('sell')

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

@login_required
def delete_response_view(request, response_id):
    # Only allow POST requests for deletion to prevent accidental deletions from GET requests
    if request.method != 'POST':
        messages.error(request, 'Invalid request method for deletion')
        return redirect('results')
    
    try:
        # Get the response
        response = RequestResponse.objects.get(id=response_id)
        
        # Check if the response is related to the user's search request
        if (response.search_request and response.search_request.user == request.user) or response.user == request.user:
            # Store information for activity log before deletion
            if response.search_request:
                request_info = f"response to search request for {response.search_request.search}"
            else:
                request_info = f"response to seller request for {response.seller_request.part_name}"
            
            # Get a reference to the ID for verification
            response_id = response.id
            
            # Hard delete the record from the database
            response.delete()
            
            # Verify deletion by trying to fetch the record again
            deleted = not RequestResponse.objects.filter(id=response_id).exists()
            
            if deleted:
                # Log activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f"Permanently deleted {request_info}"
                )
                
                messages.success(request, f'Response #{response_id} was permanently deleted from the database')
            else:
                messages.error(request, 'Failed to delete the response. Please try again.')
        else:
            messages.error(request, 'You do not have permission to delete this response.')
        
    except RequestResponse.DoesNotExist:
        messages.error(request, 'Response not found!')
    
    return redirect('results')
