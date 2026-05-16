from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q, Avg, Sum
from datetime import datetime, timedelta, date
from calendar import monthrange
import json
import calendar
from decimal import Decimal
from collections import defaultdict

from .forms import (
    UserRegisterForm, UserUpdateForm, ProfileUpdateForm,
    CategoryForm, DailyLogForm
)
from .models import UserProfile, Category, DailyLog, Penalty
from .decorators import check_penalties

def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Create user profile
            UserProfile.objects.create(user=user)
            login(request, user)
            messages.success(request, f'Account created successfully! Welcome {user.username}!')
            return redirect('dashboard')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})

def calculate_streak(user):
    """Calculate user's current streak and longest streak"""
    from datetime import timedelta
    
    today = timezone.now().date()
    
    # Get all logs grouped by date
    logs = DailyLog.objects.filter(user=user).order_by('date')
    
    if not logs.exists():
        return {'current': 0, 'longest': 0}
    
    # Track completion by date
    completion_by_date = defaultdict(lambda: {'total': 0, 'completed': 0})
    
    for log in logs:
        completion_by_date[log.date]['total'] += 1
        if log.completed:
            completion_by_date[log.date]['completed'] += 1
    
    # Calculate current streak (from today backwards)
    current_streak = 0
    check_date = today
    
    while check_date in completion_by_date:
        day_stats = completion_by_date[check_date]
        if day_stats['total'] > 0 and day_stats['completed'] == day_stats['total']:
            current_streak += 1
            check_date -= timedelta(days=1)
        else:
            break
    
    # Calculate longest streak
    longest_streak = 0
    temp_streak = 0
    last_date = None
    
    # Sort dates and find consecutive perfect days
    perfect_days = [
        date for date, stats in completion_by_date.items() 
        if stats['total'] > 0 and stats['completed'] == stats['total']
    ]
    perfect_days.sort()
    
    for day in perfect_days:
        if last_date is None or (day - last_date).days == 1:
            temp_streak += 1
        else:
            temp_streak = 1
        
        if temp_streak > longest_streak:
            longest_streak = temp_streak
        
        last_date = day
    
    return {
        'current': current_streak,
        'longest': longest_streak
    }

@login_required
@check_penalties
def dashboard(request):
    """Main dashboard with visualizations"""
    user = request.user
    profile = user.profile
    
    # Get today's date
    today = timezone.now().date()
    
    # Get filter parameter (default to 'current_month')
    time_range = request.GET.get('range', 'current_month')
    
    # Handle POST request - Mark task as complete
    if request.method == 'POST' and 'complete_log_id' in request.POST:
        log_id = request.POST.get('complete_log_id')
        try:
            log = DailyLog.objects.get(id=log_id, user=user)
            if not log.completed:
                log.completed = True
                log.save()
                messages.success(request, f'✅ "{log.category.name}" marked as completed! Great job!')
            else:
                messages.info(request, f'Task was already completed.')
        except DailyLog.DoesNotExist:
            messages.error(request, 'Task not found.')
        return redirect('dashboard')
    
    # Get all categories for the user
    categories = Category.objects.filter(user=user)
    total_categories = categories.count()
    
    # Get or create today's logs for all categories
    today_logs_list = []
    pending_tasks = []
    completed_tasks_count = 0
    
    for category in categories:
        # Get or create today's log for this category
        log, created = DailyLog.objects.get_or_create(
            user=user,
            category=category,
            date=today,
            defaults={'completed': False}
        )
        today_logs_list.append(log)
        
        if log.completed:
            completed_tasks_count += 1
        else:
            pending_tasks.append({
                'id': log.id,
                'category_id': category.id,
                'category_name': category.name,
                'category_icon': category.icon,
                'target_value': category.target_value,
                'unit': category.unit,
                'penalty_text': category.penalty_text,
                'missed_reason': log.missed_reason,
            })
    
    total_tasks_count = len(today_logs_list)
    completion_percentage = (completed_tasks_count / total_tasks_count * 100) if total_tasks_count > 0 else 0
    today_completed = completed_tasks_count
    
    # Determine date range based on filter
    if time_range == 'current_month':
        start_date = today.replace(day=1)
        end_date = today
        range_name = f"Current Month ({today.strftime('%B %Y')})"
    elif time_range == 'last_3_months':
        start_date = today - timedelta(days=90)
        end_date = today
        range_name = "Last 3 Months"
    elif time_range == 'last_6_months':
        start_date = today - timedelta(days=180)
        end_date = today
        range_name = "Last 6 Months"
    elif time_range == 'last_12_months':
        start_date = today - timedelta(days=365)
        end_date = today
        range_name = "Last 12 Months"
    else:
        start_date = today.replace(day=1)
        end_date = today
        range_name = f"Current Month ({today.strftime('%B %Y')})"
    
    # Get daily progress data
    daily_data = []
    current_date = start_date
    while current_date <= end_date:
        day_logs = DailyLog.objects.filter(user=user, date=current_date)
        total_day_tasks = day_logs.count()
        completed_day_tasks = day_logs.filter(completed=True).count()
        completion_rate = (completed_day_tasks / total_day_tasks * 100) if total_day_tasks > 0 else 0
        
        daily_data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'label': current_date.strftime('%d %b'),
            'completed': completed_day_tasks,
            'total': total_day_tasks,
            'rate': completion_rate
        })
        current_date += timedelta(days=1)
    
    # Prepare chart data
    chart_labels = [d['label'] for d in daily_data]
    chart_completed = [d['completed'] for d in daily_data]
    chart_total = [d['total'] for d in daily_data]
    chart_rate = [d['rate'] for d in daily_data]
    
    # Calculate summary statistics
    total_completed_tasks = sum(d['completed'] for d in daily_data)
    total_possible_tasks = sum(d['total'] for d in daily_data)
    overall_completion_rate = (total_completed_tasks / total_possible_tasks * 100) if total_possible_tasks > 0 else 0
    
    # Get monthly trend data for the filter dropdown
    monthly_trend_labels = []
    monthly_trend_data = []
    
    for i in range(5, -1, -1):
        month_date = today.replace(day=1) - timedelta(days=30*i)
        month_start = month_date.replace(day=1)
        
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
        
        month_logs = DailyLog.objects.filter(
            user=user,
            date__gte=month_start,
            date__lte=month_end
        )
        
        total = month_logs.count()
        completed = month_logs.filter(completed=True).count()
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        monthly_trend_labels.append(month_start.strftime('%B %Y'))
        monthly_trend_data.append(completion_rate)
    
    # Category-wise progress for current month
    current_month_start = today.replace(day=1)
    if current_month_start.month == 12:
        next_month = current_month_start.replace(year=current_month_start.year + 1, month=1)
    else:
        next_month = current_month_start.replace(month=current_month_start.month + 1)
    current_month_end = next_month - timedelta(days=1)
    
    category_progress = []
    category_performance = []
    penalty_frequency = []
    penalty_categories = []
    
    for category in categories:
        logs = DailyLog.objects.filter(
            user=user,
            category=category,
            date__gte=current_month_start,
            date__lte=current_month_end
        )
        total = logs.count()
        completed = logs.filter(completed=True).count()
        completion_rate = (completed / total * 100) if total > 0 else 0
        
        category_progress.append({
            'name': category.name,
            'completion': completion_rate,
            'icon': category.icon
        })
        
        category_performance.append({
            'name': category.name,
            'icon': category.icon,
            'target_value': category.target_value,
            'unit': category.unit,
            'completed': completed,
            'total': total,
            'completion_rate': completion_rate
        })
        
        # Count penalties for this category
        penalty_count = Penalty.objects.filter(
            user=user,
            category=category,
            date__gte=current_month_start
        ).count()
        penalty_frequency.append(penalty_count)
        penalty_categories.append(category.name)
    
    # Get recent penalties
    recent_penalties = Penalty.objects.filter(
        user=user,
        served=False
    ).order_by('-date')[:5]
    
    # Calculate streaks
    streak_data = calculate_streak(user)
    
    # Prepare heatmap data
    heatmap_data = []
    heatmap_dates = []
    for i in range(30):
        check_date = today - timedelta(days=i)
        day_logs = DailyLog.objects.filter(user=user, date=check_date)
        if day_logs:
            completed_count = day_logs.filter(completed=True).count()
            total_count = day_logs.count()
            completion_pct = (completed_count / total_count * 100) if total_count > 0 else 0
            heatmap_data.append({
                'x': check_date.strftime('%Y-%m-%d'),
                'y': completion_pct
            })
            heatmap_dates.append(check_date.strftime('%d %b'))
        else:
            heatmap_data.append({
                'x': check_date.strftime('%Y-%m-%d'),
                'y': 0
            })
            heatmap_dates.append(check_date.strftime('%d %b'))
    
    # Rank progress message
    rank_progress_message = ""
    if profile.current_rank == 'S':
        rank_progress_message = "🏆 You've reached the highest rank! Keep maintaining your consistency!"
    elif profile.current_rank == 'A':
        rank_progress_message = f"✨ Just {90 - profile.consistency_score:.0f}% more to reach S-Rank!"
    elif profile.current_rank == 'B':
        rank_progress_message = f"💪 {76 - profile.consistency_score:.0f}% more to reach A-Rank!"
    elif profile.current_rank == 'C':
        rank_progress_message = f"📈 {61 - profile.consistency_score:.0f}% more to reach B-Rank!"
    elif profile.current_rank == 'D':
        rank_progress_message = f"🎯 {41 - profile.consistency_score:.0f}% more to reach C-Rank!"
    else:
        rank_progress_message = f"🚀 {21 - profile.consistency_score:.0f}% more to reach D-Rank!"
    
    context = {
        'profile': profile,
        'today_completed': today_completed,
        'pending_tasks': pending_tasks,
        'total_tasks_count': total_tasks_count,
        'completed_tasks_count': completed_tasks_count,
        'completion_percentage': completion_percentage,
        'current_month_completion_rate': overall_completion_rate,
        'months': json.dumps(monthly_trend_labels),
        'monthly_completion': json.dumps(monthly_trend_data),
        'chart_labels': json.dumps(chart_labels),
        'chart_completed': json.dumps(chart_completed),
        'chart_total': json.dumps(chart_total),
        'chart_rate': json.dumps(chart_rate),
        'range_name': range_name,
        'time_range': time_range,
        'total_categories': total_categories,
        'total_completed_tasks': total_completed_tasks,
        'total_possible_tasks': total_possible_tasks,
        'overall_completion_rate': overall_completion_rate,
        'category_names': json.dumps([c['name'] for c in category_progress]),
        'category_completions': json.dumps([c['completion'] for c in category_progress]),
        'category_icons': json.dumps([c['icon'] for c in category_progress]),
        'category_performance': category_performance,
        'penalty_frequency_data': json.dumps(penalty_frequency),
        'penalty_categories': json.dumps(penalty_categories),
        'recent_penalties': recent_penalties,
        'streak_data': streak_data,
        'heatmap_data': json.dumps(heatmap_data),
        'heatmap_dates': json.dumps(heatmap_dates),
        'rank_progress_message': rank_progress_message,
        'today': today,
        'categories': categories,
        'current_month_name': today.strftime('%B %Y'),
    }
    
    return render(request, 'core/dashboard.html', context)

@login_required
@check_penalties
def tracker_view(request, year=None, month=None):
    """Main tracker page with calendar grid"""
    user = request.user
    today = timezone.now().date()
    
    # Set current date
    if year and month:
        try:
            current_date = date(int(year), int(month), 1)
        except ValueError:
            current_date = today.replace(day=1)
    else:
        current_date = today.replace(day=1)
    
    # Get month range (first and last day of the month)
    last_day = monthrange(current_date.year, current_date.month)[1]
    month_dates = [current_date.replace(day=day) for day in range(1, last_day + 1)]
    
    # Get categories for the user
    categories = Category.objects.filter(user=user).order_by('name')
    
    # Get all logs for this month (optimize with select_related)
    logs = list(DailyLog.objects.filter(
        user=user,
        date__year=current_date.year,
        date__month=current_date.month
    ).select_related('category'))
    
    # Create a set of existing log keys for quick lookup
    existing_log_keys = {(log.category_id, log.date) for log in logs}
    
    # Create missing logs for any category-date combination that doesn't exist
    new_logs = []
    for category in categories:
        for log_date in month_dates:
            if (category.id, log_date) not in existing_log_keys:
                new_log = DailyLog(
                    user=user,
                    category=category,
                    date=log_date,
                    completed=False
                )
                new_logs.append(new_log)
    
    # Bulk create all missing logs at once for better performance
    if new_logs:
        logs.extend(DailyLog.objects.bulk_create(new_logs))
    
    # Handle POST request - Save all changes
    if request.method == 'POST' and 'save_all' in request.POST:
        updated_count = 0
        for key, value in request.POST.items():
            if key.startswith('log_'):
                try:
                    log_id = int(key.split('_')[1])
                    log = DailyLog.objects.get(id=log_id, user=user)
                    # Check if checkbox was checked (value will be 'true' or 'on')
                    is_completed = value == 'true' or value == 'on'
                    
                    if log.completed != is_completed:
                        log.completed = is_completed
                        log.save()
                        updated_count += 1
                except (DailyLog.DoesNotExist, ValueError, IndexError):
                    pass
        
        if updated_count > 0:
            messages.success(request, f'✅ Successfully updated {updated_count} task(s)!')
        else:
            messages.info(request, 'No changes were made.')
        
        # Redirect to the same month to refresh the page
        return redirect('tracker', year=current_date.year, month=current_date.month)
    
    # Calculate monthly statistics
    total_logs = len(logs)
    completed_logs = sum(1 for log in logs if log.completed)
    monthly_completion = (completed_logs / total_logs * 100) if total_logs > 0 else 0
    
    # Calculate previous month
    if current_date.month == 1:
        prev_month = current_date.replace(year=current_date.year - 1, month=12)
    else:
        prev_month = current_date.replace(month=current_date.month - 1)
    
    # Calculate next month
    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1)
    
    # Calculate today's completion for the current month view
    today_logs = [log for log in logs if log.date == today]
    today_completed = sum(1 for log in today_logs if log.completed)
    today_total = len(today_logs)
    today_percentage = (today_completed / today_total * 100) if today_total > 0 else 0
    
    context = {
        'categories': categories,
        'month_dates': month_dates,
        'current_date': current_date,
        'logs': logs,
        'monthly_completion': monthly_completion,
        'prev_month': prev_month,
        'next_month': next_month,
        'calendar_month_name': current_date.strftime('%B %Y'),
        'today': today,
        'today_completed': today_completed,
        'today_total': today_total,
        'today_percentage': today_percentage,
    }
    
    return render(request, 'core/tracker.html', context)

@login_required
def categories_view(request):
    """Manage categories"""
    user = request.user
    categories = Category.objects.filter(user=user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.user = user
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('categories')
    else:
        form = CategoryForm()
    
    context = {
        'categories': categories,
        'form': form,
    }
    return render(request, 'core/categories.html', context)

@login_required
def edit_category(request, pk):
    """Edit a category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, f'Category "{category.name}" updated successfully!')
            return redirect('categories')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
    }
    return render(request, 'core/category_edit.html', context)

@login_required
def delete_category(request, pk):
    """Delete a category"""
    category = get_object_or_404(Category, pk=pk, user=request.user)
    if request.method == 'POST':
        category_name = category.name
        category.delete()
        messages.success(request, f'Category "{category_name}" deleted successfully!')
        return redirect('categories')
    
    return render(request, 'core/category_confirm_delete.html', {'category': category})

@login_required
def penalties_view(request):
    """View and manage penalties"""
    user = request.user
    
    # Check and double overdue penalties
    overdue_penalties = Penalty.objects.filter(
        user=user,
        served=False,
        due_date__lt=timezone.now().date()
    )
    for penalty in overdue_penalties:
        penalty.double_penalty()
    
    pending_penalties = Penalty.objects.filter(user=user, served=False).order_by('due_date')
    penalty_history = Penalty.objects.filter(user=user, served=True).order_by('-served_date')[:20]
    
    if request.method == 'POST':
        penalty_id = request.POST.get('penalty_id')
        if penalty_id:
            penalty = get_object_or_404(Penalty, id=penalty_id, user=user)
            penalty.serve()
            messages.success(request, 'Penalty marked as completed!')
            return redirect('penalties')
    
    context = {
        'pending_penalties': pending_penalties,
        'penalty_history': penalty_history,
    }
    return render(request, 'core/penalties.html', context)

@login_required
def profile_view(request):
    """User profile page"""
    user = request.user
    profile = user.profile
    
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=user)
        p_form = ProfileUpdateForm(instance=profile)
    
    # Check if target is achieved based on consistency
    if profile.consistency_score >= 80:
        profile.target_achieved = True
        profile.save()
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'profile': profile,
    }
    return render(request, 'core/profile.html', context)

@login_required
def toggle_dark_mode(request):
    """Toggle dark/light mode"""
    user = request.user
    profile = user.profile
    profile.dark_mode = not profile.dark_mode
    profile.save()
    return JsonResponse({'dark_mode': profile.dark_mode})

@login_required
def get_chart_data(request):
    """AJAX endpoint for chart data"""
    user = request.user
    data = {}
    
    # Get data for radar chart (target vs actual)
    categories = Category.objects.filter(user=user)
    targets = []
    actuals = []
    
    current_month_start = timezone.now().date().replace(day=1)
    next_month = current_month_start.replace(day=28) + timedelta(days=4)
    current_month_end = next_month - timedelta(days=next_month.day)
    
    for category in categories:
        targets.append(float(category.target_value))
        
        logs = DailyLog.objects.filter(
            user=user,
            category=category,
            date__gte=current_month_start,
            date__lte=current_month_end
        )
        avg_achieved = logs.aggregate(Avg('value_achieved'))['value_achieved__avg'] or 0
        actuals.append(float(avg_achieved))
    
    data['targets'] = targets
    data['actuals'] = actuals
    data['categories'] = [c.name for c in categories]
    
    return JsonResponse(data)

from django.http import JsonResponse
import json

@login_required
def update_log(request, log_id):
    """AJAX endpoint to update a single log"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            log = DailyLog.objects.get(id=log_id, user=request.user)
            log.completed = data.get('completed', False)
            log.save()
            return JsonResponse({'success': True})
        except DailyLog.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Log not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

@login_required
def add_missed_reason(request, log_id):
    """AJAX endpoint to add reason for missed target"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            log = DailyLog.objects.get(id=log_id, user=request.user)
            log.missed_reason = data.get('reason', '')
            log.save()
            return JsonResponse({'success': True})
        except DailyLog.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Log not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=400)
    return JsonResponse({'success': False, 'error': 'Invalid method'}, status=405)

from django.contrib.auth import authenticate, login as auth_login
def user_login(request):
    """Custom login view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.username}! 👋')
            next_url = request.POST.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password!')
    
    return render(request, 'registration/login.html')

@login_required
def get_notifications(request):
    """AJAX endpoint for notifications"""
    user = request.user
    
    # Get pending penalties as notifications
    penalties = Penalty.objects.filter(user=user, served=False)[:5]
    
    notifications = []
    for penalty in penalties:
        notifications.append({
            'icon': 'mdi-alert-circle',
            'title': f'Penalty: {penalty.category.name} - {penalty.penalty_text[:50]}',
            'time': penalty.date.strftime('%b %d, %Y'),
            'link': reverse('penalties'),
        })
    
    return JsonResponse({'notifications': notifications})