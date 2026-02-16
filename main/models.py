from django.db import models
from DR_JAKPA import settings
from django.core.exceptions import ValidationError


class GmailToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class EligibilityAssessment(models.Model):
    # Contact Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    whatsapp = models.CharField(max_length=20)
    
    # Quiz Responses
    q1_has_degree = models.CharField(max_length=50)
    q2_internship = models.CharField(max_length=50)
    q3_mdcn_license = models.CharField(max_length=50)
    q4_german_level = models.CharField(max_length=50)
    q5_fsp_prep = models.CharField(max_length=50)
    q6_experience_years = models.CharField(max_length=50)
    q7_currently_practicing = models.CharField(max_length=50)
    q8_funds = models.CharField(max_length=50)
    q9_timeline = models.CharField(max_length=50)
    q10_dependents = models.CharField(max_length=50)
    
    # Calculated Results
    score = models.IntegerField()
    category = models.CharField(max_length=50)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.full_name} - {self.category} ({self.score}%)"


class SessionTime(models.Model):
    date = models.DateField()
    time = models.TimeField()
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['date', 'time']
        unique_together = ['date', 'time']
    
    def __str__(self):
        return f"{self.date.strftime('%b %d')} • {self.time.strftime('%H:%M')}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Customer Information
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    whatsapp_number = models.CharField(max_length=20)
    
    # Booking Details
    session_time = models.ForeignKey(SessionTime, on_delete=models.PROTECT, related_name='bookings')
    duration_hours = models.IntegerField(default=1)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment
    payment_screenshot = models.ImageField(upload_to='booking_payments/', blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.session_time} ({self.duration_hours}hr)"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = self.duration_hours * 10000
        
        # Validate session time availability
        if self.session_time and not self.session_time.is_available:
            raise ValidationError("Selected session time is not available")
        
        super().save(*args, **kwargs)


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    image = models.ImageField(upload_to='testimonials/', blank=True, null=True)
    testimony = models.TextField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Testimonial from {self.name}"


class Faq(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.question