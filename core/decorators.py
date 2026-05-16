from django.shortcuts import redirect
from django.contrib import messages
from .models import Penalty

def check_penalties(view_func):
    """Decorator to check and double overdue penalties"""
    def wrapper(request, *args, **kwargs):
        if request.user.is_authenticated:
            # Check for overdue penalties
            overdue_penalties = Penalty.objects.filter(
                user=request.user,
                served=False,
                due_date__lt=request.user.date_joined.date()  # This needs to be fixed
            )
            for penalty in overdue_penalties:
                if penalty.double_penalty():
                    messages.warning(
                        request, 
                        f'Penalty for {penalty.category.name} has been doubled due to being overdue!'
                    )
        return view_func(request, *args, **kwargs)
    return wrapper