import json
from datetime import datetime, timedelta


def normalize_availability_dates(raw_dates):
    raw_dates = (raw_dates or "").strip()
    if not raw_dates:
        return "", []

    parsed_dates = []
    invalid_dates = []

    for part in raw_dates.split(","):
        value = part.strip()
        if not value:
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
            parsed_dates.append(value)
        except ValueError:
            invalid_dates.append(value)

    if invalid_dates:
        return None, invalid_dates

    return ",".join(sorted(set(parsed_dates))), []


def get_blocked_dates(property_obj):
    return property_obj.get_blocked_dates()


def get_reserved_dates(property_obj):
    reserved_dates = set()
    approved_bookings = property_obj.bookings.filter(status="approved")

    for booking in approved_bookings:
        current_date = booking.check_in
        while current_date < booking.check_out:
            reserved_dates.add(current_date.strftime("%Y-%m-%d"))
            current_date += timedelta(days=1)

    return sorted(reserved_dates)


def filter_properties_by_availability(queryset, start_date=None, end_date=None):
    available_ids = [
        property_obj.pk
        for property_obj in queryset
        if property_obj.is_available(start_date, end_date)
    ]
    return queryset.filter(pk__in=available_ids)


def build_calendar_payload(property_obj):
    blocked_dates = [
        blocked_date.strftime("%Y-%m-%d")
        for blocked_date in get_blocked_dates(property_obj)
    ]
    reserved_dates = get_reserved_dates(property_obj)

    return {
        "blocked_dates": blocked_dates,
        "blocked_dates_json": json.dumps(blocked_dates),
        "reserved_dates": reserved_dates,
        "reserved_dates_json": json.dumps(reserved_dates),
        "all_days_available": not blocked_dates and not reserved_dates,
    }
