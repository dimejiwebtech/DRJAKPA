from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import threading

def send_contact_email(contact_data):

    admin_subject = f"New Contact Form Submission from {contact_data ['full_name']}"
    admin_message = render_to_string('main/emails/admin_notification.txt', {
        'full_name': contact_data['full_name'],
        'email': contact_data['email'],
        'current_role': contact_data['current_role'],
        'inquiry_topic': contact_data['inquiry_topic'],
        'description': contact_data['description'],
    })

    send_mail(
        admin_subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [settings.DEFAULT_FROM_EMAIL],
        html_message=admin_message,
        fail_silently=False,
    )

    user_subject = "Thank you for contacting Dr. Jakpa"
    user_message = render_to_string('main/emails/user_confirmation.txt', {
        'full_name': contact_data['full_name'],
    })

    send_mail(
        user_subject,
        '',
        settings.DEFAULT_FROM_EMAIL,
        [contact_data['email']],
        html_message=user_message,
        fail_silently=False,
    )


def send_booking_confirmation_async(booking_data):
    def _send_email():
        user_subject = "Booking Confirmation - Dr. Jakpa Strategy Session"
        user_message = render_to_string('main/emails/booking_confirmation.html', {
            'full_name': booking_data['full_name'],
            'session_time': booking_data['session_time'],
            'duration_hours': booking_data['duration_hours'],
            'total_price': booking_data['total_price'],
        })

        send_mail(
            user_subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [booking_data['email']],
            html_message=user_message,
            fail_silently=False,
        )

        # Also notify admin
        admin_subject = f"New Booking from {booking_data['full_name']}"
        admin_message = render_to_string('main/emails/booking_admin_notification.html', {
            'full_name': booking_data['full_name'],
            'email': booking_data['email'],
            'whatsapp_number': booking_data['whatsapp_number'],
            'session_time': booking_data['session_time'],
            'duration_hours': booking_data['duration_hours'],
            'total_price': booking_data['total_price'],
        })

        send_mail(
            admin_subject,
            '',
            settings.DEFAULT_FROM_EMAIL,
            [settings.DEFAULT_FROM_EMAIL],
            html_message=admin_message,
            fail_silently=False,
        )
    
    # Run email sending in a separate thread
    email_thread = threading.Thread(target=_send_email)
    email_thread.start()
