from django.core.mail import send_mail


class NotificationService:
    @staticmethod
    def send_booking_request_email(booking):
        owner = getattr(getattr(booking.property, "owner", None), "user", None)
        owner_email = getattr(owner, "email", None)

        if not owner or not owner_email:
            raise ValueError("The property owner must have an email address.")

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

        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[owner_email],
            fail_silently=False,
        )
