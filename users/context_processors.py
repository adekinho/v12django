from .models import UserProfile

def user_profile(request):
    """
    Context processor to make the user's profile available in all templates.
    """
    if request.user.is_authenticated:
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        return {'user_profile': profile}
    return {'user_profile': None}
