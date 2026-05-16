from django.contrib import admin
from .models import UserProfile, Category, DailyLog, Penalty

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'current_rank', 'consistency_score', 'target_achieved']
    list_filter = ['current_rank', 'target_achieved']
    search_fields = ['user__username']

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'target_value', 'unit']
    list_filter = ['user']
    search_fields = ['name']

@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'date', 'completed']
    list_filter = ['completed', 'date', 'user']
    search_fields = ['user__username', 'category__name']

@admin.register(Penalty)
class PenaltyAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'date', 'served', 'doubled']
    list_filter = ['served', 'doubled', 'date']
    search_fields = ['user__username']