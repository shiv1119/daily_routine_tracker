from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

class UserProfile(models.Model):
    RANK_CHOICES = [
        ('E', 'E-Rank'),
        ('D', 'D-Rank'),
        ('C', 'C-Rank'),
        ('B', 'B-Rank'),
        ('A', 'A-Rank'),
        ('S', 'S-Rank'),
    ]
    
    RANK_COLORS = {
        'E': '#6c757d',  # Gray
        'D': '#cd7f32',  # Bronze
        'C': '#28a745',  # Green
        'B': '#007bff',  # Blue
        'A': '#6f42c1',  # Purple
        'S': '#ff8c00',  # Gold/Orange
    }
    
    RANK_ICONS = {
        'E': '🐛',  # Bug/E-Rank
        'D': '🛡️',  # Shield
        'C': '⚔️',  # Crossed swords
        'B': '🏹',  # Bow
        'A': '🔱',  # Trident
        'S': '👑',  # Crown
    }
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    dob = models.DateField(null=True, blank=True)
    personal_target = models.CharField(max_length=200, blank=True)
    target_achieved = models.BooleanField(default=False)
    current_rank = models.CharField(max_length=1, choices=RANK_CHOICES, default='E')
    consistency_score = models.FloatField(default=0.0)
    dark_mode = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def update_rank_and_score(self):
        """Update user's rank based on last 30 days consistency"""
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        
        logs = DailyLog.objects.filter(
            user=self.user,
            date__gte=thirty_days_ago,
            date__lte=timezone.now().date()
        )
        
        total_logs = logs.count()
        if total_logs == 0:
            self.consistency_score = 0
            self.current_rank = 'E'
        else:
            completed_logs = logs.filter(completed=True).count()
            self.consistency_score = (completed_logs / total_logs) * 100
            
            # Determine rank
            if self.consistency_score >= 90:
                self.current_rank = 'S'
            elif self.consistency_score >= 76:
                self.current_rank = 'A'
            elif self.consistency_score >= 61:
                self.current_rank = 'B'
            elif self.consistency_score >= 41:
                self.current_rank = 'C'
            elif self.consistency_score >= 21:
                self.current_rank = 'D'
            else:
                self.current_rank = 'E'
        
        self.save()
    
    def get_next_rank_threshold(self):
        """Get percentage needed for next rank"""
        if self.current_rank == 'S':
            return 100
        thresholds = {'E': 21, 'D': 41, 'C': 61, 'B': 76, 'A': 90}
        return thresholds.get(self.current_rank, 100)
    
    def get_rank_progress(self):
        """Get progress to next rank as percentage"""
        if self.current_rank == 'S':
            return 100
        
        current_threshold = 0
        next_threshold = self.get_next_rank_threshold()
        
        if self.current_rank == 'E':
            current_threshold = 0
        elif self.current_rank == 'D':
            current_threshold = 21
        elif self.current_rank == 'C':
            current_threshold = 41
        elif self.current_rank == 'B':
            current_threshold = 61
        elif self.current_rank == 'A':
            current_threshold = 76
        
        progress = ((self.consistency_score - current_threshold) / 
                   (next_threshold - current_threshold)) * 100
        return min(max(progress, 0), 100)

class Category(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')
    name = models.CharField(max_length=100)
    target_value = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit = models.CharField(max_length=50, default='times')
    icon = models.CharField(max_length=10, default='✅')
    penalty_text = models.CharField(max_length=200, default="You didn't meet your target!")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'name']
        ordering = ['name']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_today_log(self):
        """Get today's log for this category"""
        today = timezone.now().date()
        return DailyLog.objects.filter(
            category=self, 
            date=today,
            user=self.user
        ).first()

class DailyLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_logs')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='logs')
    date = models.DateField(default=timezone.now)
    completed = models.BooleanField(default=False)
    value_achieved = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    missed_reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['category', 'date', 'user']
        ordering = ['-date']
    
    def __str__(self):
        status = "✓" if self.completed else "✗"
        return f"{self.user.username} - {self.category.name} - {self.date} {status}"
    
    def save(self, *args, **kwargs):
        """Override save to auto-create penalty if target missed"""
        is_new = self.pk is None
        old_completed = False
        
        if not is_new:
            old = DailyLog.objects.get(pk=self.pk)
            old_completed = old.completed
        
        super().save(*args, **kwargs)
        
        # Create penalty if target was missed (or newly missed)
        if not self.completed and (is_new or old_completed):
            Penalty.objects.get_or_create(
                user=self.user,
                category=self.category,
                date=self.date,
                defaults={
                    'penalty_text': self.category.penalty_text,
                    'due_date': self.date + timedelta(days=3)
                }
            )
        # Remove penalty if marked completed
        elif self.completed and not old_completed:
            Penalty.objects.filter(
                user=self.user,
                category=self.category,
                date=self.date
            ).delete()
        
        # Update user rank
        self.user.profile.update_rank_and_score()

class Penalty(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='penalties')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='penalties')
    date = models.DateField()
    penalty_text = models.CharField(max_length=200)
    served = models.BooleanField(default=False)
    served_date = models.DateField(null=True, blank=True)
    doubled = models.BooleanField(default=False)
    due_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'category', 'date']
        ordering = ['-date', '-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.date}"
    
    def is_overdue(self):
        """Check if penalty is overdue"""
        return not self.served and timezone.now().date() > self.due_date
    
    def serve(self):
        """Mark penalty as served"""
        self.served = True
        self.served_date = timezone.now().date()
        self.save()
    
    def double_penalty(self):
        """Double the penalty if not served in time"""
        if not self.served and not self.doubled and timezone.now().date() > self.due_date:
            self.penalty_text = f"DOUBLED: {self.penalty_text} (x2)"
            self.doubled = True
            # Create new due date 3 days from now
            self.due_date = timezone.now().date() + timedelta(days=3)
            self.save()
            return True
        return False