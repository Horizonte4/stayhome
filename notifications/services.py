from django.core.mail import send_mail
from django.utils.translation import gettext as _


class NotificationService:
    @staticmethod
    def _send_booking_status_email(booking, subject, message):
        client_email = getattr(booking.user, "email", None)

        if not client_email:
            raise ValueError(_("The booking client must have an email address."))

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[client_email],
                fail_silently=False,
            )
        except Exception as exc:
            raise ValueError(_("The booking status email could not be sent.")) from exc

    @staticmethod
    def send_booking_request_email(booking):
        owner = getattr(getattr(booking.property, "owner", None), "user", None)
        owner_email = getattr(owner, "email", None)

        if not owner or not owner_email:
            raise ValueError(_("The property owner must have an email address."))

        requester_name = (
            f"{booking.user.first_name} {booking.user.last_name}".strip()
            or booking.user.email
        )

        subject = f"Rental request for {booking.property.title}"
        message = (
            f"You have received a rental request for {booking.property.title} in "
            f"{booking.property.city}.\n\n"
            f"Requester: {requester_name}\n"
            f"Check-in: {booking.check_in}\n"
            f"Check-out: {booking.check_out}"
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=None,
                recipient_list=[owner_email],
                fail_silently=False,
            )
        except Exception as exc:
            raise ValueError(_("The booking request email could not be sent.")) from exc

    @staticmethod
    def send_booking_approved_email(booking):
        subject = f"Your booking for {booking.property.title} was approved"
        message = (
            f"Your rental request for {booking.property.title} in "
            f"{booking.property.city} has been approved.\n\n"
            f"Check-in: {booking.check_in}\n"
            f"Check-out: {booking.check_out}"
        )
        NotificationService._send_booking_status_email(booking, subject, message)

    @staticmethod
    def send_booking_rejected_email(booking):
        subject = f"Your booking for {booking.property.title} was denied"
        message = (
            f"Your rental request for {booking.property.title} in "
            f"{booking.property.city} was denied.\n\n"
            f"Check-in: {booking.check_in}\n"
            f"Check-out: {booking.check_out}"
        )
        NotificationService._send_booking_status_email(booking, subject, message)
