from datetime import datetime
from .models import Penalty, UserProfile

def user_rank(request):
    """Add user rank and pending penalties to all templates"""
    if request.user.is_authenticated and hasattr(request.user, 'profile'):
        profile = request.user.profile
        pending_count = Penalty.objects.filter(
            user=request.user, 
            served=False
        ).count()
        
        # Get greeting based on time
        hour = datetime.now().hour
        if hour < 12:
            greeting = 'Good Morning'
        elif hour < 17:
            greeting = 'Good Afternoon'
        else:
            greeting = 'Good Evening'
        
        return {
            'user_rank': dict(UserProfile.RANK_CHOICES).get(profile.current_rank, 'E-Rank'),
            'user_rank_color': UserProfile.RANK_COLORS.get(profile.current_rank, '#5e72e4'),
            'user_rank_icon': UserProfile.RANK_ICONS.get(profile.current_rank, 'fa-star'),
            'consistency_score': profile.consistency_score,
            'pending_penalties_count': pending_count,
            'greeting': greeting,
        }
    return {
        'user_rank': 'E-Rank',
        'user_rank_color': '#5e72e4',
        'user_rank_icon': 'fa-star',
        'consistency_score': 0,
        'pending_penalties_count': 0,
        'greeting': 'Good Day',
    }