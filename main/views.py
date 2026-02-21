from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from .emails import send_contact_email, send_booking_confirmation_async
from .models import EligibilityAssessment, SessionTime, Booking, Testimonial, Faq, TeamMember
from blog.models import Post
def home(request):
    faqs = Faq.objects.all().order_by('-created_at')
    testimonials = Testimonial.objects.filter(is_active=True).order_by('-created_at')
    posts = Post.objects.filter(status='published').order_by('-created_at')[:3]
    return render(request, 'main/homepage.html', {'posts': posts, 'testimonials': testimonials, 'faqs': faqs})

def about(request):
    team_members = TeamMember.objects.filter(is_active=True).order_by('order', 'created_at')
    return render(request, 'main/about.html', {'team_members': team_members})

def contact(request):
    if request.method == 'POST':
        try:
            contact_data = {
                'full_name': request.POST.get('full_name'),
                'email': request.POST.get('email'),
                'current_role': request.POST.get('current_role'),
                'inquiry_topic': request.POST.get('inquiry_topic'),
                'description': request.POST.get('description'),
            }

            if not all(contact_data.values()):
                messages.error(request, "Please fill in all required fields!")
                return redirect('contact')

            send_contact_email(contact_data)
            messages.success(request, "Thank you for your message! We will get back to you soon.")
            return redirect('contact')

        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('contact')

        
    return render(request, 'main/contact.html')

def bookings(request):    
    if request.method == 'POST':
        try:
            # Get form data
            full_name = request.POST.get('full_name')
            email = request.POST.get('email')
            whatsapp_number = request.POST.get('whatsapp_number')
            duration_hours = int(request.POST.get('duration_hours', 1))
            session_time_id = request.POST.get('session_time_id')
            payment_screenshot = request.FILES.get('payment_screenshot')
            
            # Validate required fields
            if not all([full_name, email, whatsapp_number, session_time_id]):
                messages.error(request, "Please fill in all required fields!")
                return redirect('bookings')
            
            # Get session time
            session_time = SessionTime.objects.get(id=session_time_id, is_available=True)
            
            # Create booking
            booking = Booking.objects.create(
                full_name=full_name,
                email=email,
                whatsapp_number=whatsapp_number,
                duration_hours=duration_hours,
                session_time=session_time,
                payment_screenshot=payment_screenshot
            )
            
            # Send confirmation email asynchronously
            send_booking_confirmation_async({
                'full_name': full_name,
                'email': email,
                'whatsapp_number': whatsapp_number,
                'session_time': str(session_time),
                'duration_hours': duration_hours,
                'total_price': f"₦{booking.total_price:,.2f}"
            })
            
            messages.success(request, "Booking submitted successfully! You'll receive a confirmation email shortly.")
            return redirect('bookings')
            
        except SessionTime.DoesNotExist:
            messages.error(request, "Selected session time is not available!")
            return redirect('bookings')
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('bookings')
    
    # GET request - fetch available session times
    available_sessions = SessionTime.objects.filter(is_available=True)
    
    context = {
        'available_sessions': available_sessions
    }
    
    return render(request, 'main/bookings.html', context)

def services(request):
    return render(request, 'main/services.html')

def disclaimer(request):
    return render(request, 'main/disclaimer.html')

def privacy(request):
    return render(request, 'main/privacy.html')

def terms(request):
    return render(request, 'main/terms.html')


@csrf_exempt
@require_POST
def eligibility_submit(request):
    try:
        data = json.loads(request.body)
        
        # Calculate score
        score = 0
        
        # Q2: Internship completed (20 points)
        if data.get('q2_internship') == 'Yes':
            score += 20
            
        # Q3: MDCN license (15 points)
        if data.get('q3_mdcn_license') == 'Yes':
            score += 15
            
        # Q4: German level (25 points for B2/C1)
        german_level = data.get('q4_german_level')
        if german_level in ['B2', 'C1']:
            score += 25
            
        # Q6: Experience (15 points for 1+ years)
        experience = data.get('q6_experience_years')
        if experience in ['1-3 years', '3-5 years', '5+ years']:
            score += 15
            
        # Q8: Funds (15 points)
        if data.get('q8_funds') == 'Yes (€5,000+)':
            score += 15
            
        # Q9: Timeline (10 points for <12 months)
        timeline = data.get('q9_timeline')
        if timeline in ['Within 6 months', '6-12 months']:
            score += 10
        
        # Determine category
        if score >= 80:
            category = 'Highly Eligible'
            package = 'Premium Package'
            color = 'green'
        elif score >= 60:
            category = 'Almost Ready'
            package = 'Language + Basic Package'
            color = 'yellow'
        elif score >= 40:
            category = 'Early Stage'
            package = 'Starter Consultation'
            color = 'orange'
        else:
            category = 'Not Yet Eligible'
            package = 'Preparation Resources'
            color = 'red'
        
        # Generate strengths (pick top 3)
        strengths = []
        if data.get('q2_internship') == 'Yes':
            strengths.append('You have completed your internship')
        if data.get('q3_mdcn_license') == 'Yes':
            strengths.append('You hold a full MDCN license')
        if german_level in ['B2', 'C1']:
            strengths.append(f'Your German is at a strong level ({german_level})')
        if experience in ['3-5 years', '5+ years']:
            strengths.append('You have significant medical experience')
        if data.get('q8_funds') == 'Yes (€5,000+)':
            strengths.append('You have funds ready for relocation')
        if timeline in ['Within 6 months', '6-12 months']:
            strengths.append('Your timeline is realistic and achievable')
        if data.get('q7_currently_practicing') != 'No':
            strengths.append('You are currently in active practice')
            
        # Generate weaknesses (pick top 2)
        weaknesses = []
        if data.get('q2_internship') != 'Yes':
            weaknesses.append('You need to complete your internship')
        if data.get('q3_mdcn_license') != 'Yes':
            weaknesses.append('You need to obtain your MDCN license')
        if german_level not in ['B2', 'C1']:
            weaknesses.append('German language training is required')
        if experience == '0-1 year':
            weaknesses.append('More clinical experience would strengthen your application')
        if data.get('q8_funds') != 'Yes (€5,000+)':
            weaknesses.append('Start planning your relocation budget')
        
        # Save to database
        assessment = EligibilityAssessment.objects.create(
            full_name=data.get('full_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            whatsapp=data.get('whatsapp'),
            q1_has_degree=data.get('q1_has_degree'),
            q2_internship=data.get('q2_internship'),
            q3_mdcn_license=data.get('q3_mdcn_license'),
            q4_german_level=data.get('q4_german_level'),
            q5_fsp_prep=data.get('q5_fsp_prep'),
            q6_experience_years=data.get('q6_experience_years'),
            q7_currently_practicing=data.get('q7_currently_practicing'),
            q8_funds=data.get('q8_funds'),
            q9_timeline=data.get('q9_timeline'),
            q10_dependents=data.get('q10_dependents'),
            score=score,
            category=category
        )
        
        return JsonResponse({
            'success': True,
            'score': score,
            'category': category,
            'package': package,
            'color': color,
            'strengths': strengths[:3],  # Top 3
            'weaknesses': weaknesses[:2]  # Top 2
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
