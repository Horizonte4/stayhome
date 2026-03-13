from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import OuterRef, Q, Subquery
from django.http import HttpResponseForbidden, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from transactions.models import Booking
from .models import Conversation


from properties.models import Property

from .models import Conversation, Message


def _get_conversation_for_user_or_404(conversation_id, user):
    return get_object_or_404(
        Conversation.objects.with_related().filter(
            Q(buyer=user) | Q(owner=user)
        ),
        pk=conversation_id,
    )


@login_required
@transaction.atomic
def start_conversation(request, property_id):

    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    property_obj = get_object_or_404(
        Property.objects.select_related("owner__user"),
        pk=property_id,
        active_listing=True,
    )

    if not property_obj.owner:
        messages.error(request, "This property has no owner assigned.")
        return redirect("properties:property_detail", pk=property_obj.pk)

    owner_user = property_obj.owner.user
    buyer_user = request.user

    if buyer_user == owner_user:
        messages.error(request, "You cannot start a chat with yourself.")
        return redirect("properties:property_detail", pk=property_obj.pk)

    # -----------------------------
    # VALIDAR BOOKING APROBADO
    # -----------------------------

    approved_booking = Booking.objects.filter(
        property=property_obj,
        user=buyer_user,
        status="approved"
    ).exists()

    if not approved_booking:
        messages.error(
            request,
            "You can only contact the owner after your booking has been approved."
        )
        return redirect("transactions:my_bookings")

    # -----------------------------
    # CREAR / OBTENER CONVERSACIÓN
    # -----------------------------

    conversation, created = Conversation.objects.get_or_create(
        property=property_obj,
        buyer=buyer_user,
        defaults={"owner": owner_user},
    )

    if created:
        messages.success(request, "Conversation started successfully.")

    return redirect(
        "comunication:conversation_detail",
        conversation_id=conversation.pk
    )


@login_required
def inbox(request):
    last_message_subquery = Message.objects.filter(
        conversation=OuterRef("pk")
    ).order_by("-created_at")

    conversations = (
        Conversation.objects.for_user(request.user)
        .with_related()
        .annotate(
            last_message_content=Subquery(last_message_subquery.values("content")[:1]),
            last_message_created_at=Subquery(last_message_subquery.values("created_at")[:1]),
        )
        .prefetch_related("messages")
    )

    conversation_rows = []
    for conversation in conversations:
        other_user = conversation.owner if conversation.buyer == request.user else conversation.buyer

        unread_count = conversation.messages.filter(is_read=False).exclude(sender=request.user).count()

        conversation_rows.append(
            {
                "conversation": conversation,
                "property": conversation.property,
                "other_user": other_user,
                "last_message": conversation.last_message_content,
                "last_message_created_at": conversation.last_message_created_at,
                "unread_count": unread_count,
            }
        )

    context = {
        "conversation_rows": conversation_rows,
    }
    return render(request, "comunication/inbox.html", context)


@login_required
def conversation_detail(request, conversation_id):

    conversation = _get_conversation_for_user_or_404(conversation_id, request.user)

    # -------------------------
    # MENSAJES DE LA CONVERSACIÓN
    # -------------------------

    messages_qs = (
        conversation.messages.with_related()
        .select_related("sender")
        .order_by("created_at")
    )

    conversation.messages.filter(
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    other_user = conversation.owner if conversation.buyer == request.user else conversation.buyer


    # -------------------------
    # CONVERSACIONES (SIDEBAR)
    # -------------------------

    last_message_subquery = Message.objects.filter(
        conversation=OuterRef("pk")
    ).order_by("-created_at")

    conversations = (
        Conversation.objects.for_user(request.user)
        .with_related()
        .annotate(
            last_message_content=Subquery(last_message_subquery.values("content")[:1]),
            last_message_created_at=Subquery(last_message_subquery.values("created_at")[:1]),
        )
        .prefetch_related("messages")
    )
    print(other_user)
    conversation_rows = []

    for conv in conversations:

        other = conv.owner if conv.buyer == request.user else conv.buyer

        unread_count = conv.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()

        conversation_rows.append({
            "conversation": conv,
            "property": conv.property,
            "other_user": other,
            "last_message": conv.last_message_content,
            "last_message_created_at": conv.last_message_created_at,
            "unread_count": unread_count,
        })


    context = {
        "conversation": conversation,
        "messages_list": messages_qs,
        "other_user": other_user,
        "conversation_rows": conversation_rows,   # 👈 IMPORTANTE
    }

    return render(
        request,
        "comunication/conversation_detail.html",
        context
    )
    
#
# @login_required
#def conversation_detail(request, conversation_id):
    conversation = _get_conversation_for_user_or_404(conversation_id, request.user)

    messages_qs = (
        conversation.messages.with_related()
        .select_related("sender")
        .order_by("created_at")
    )

    conversation.messages.filter(
        is_read=False
    ).exclude(sender=request.user).update(is_read=True)

    other_user = conversation.owner if conversation.buyer == request.user else conversation.buyer

    context = {
        "conversation": conversation,
        "messages_list": messages_qs,
        "other_user": other_user,
    }
    return render(request, "comunication/conversation_detail.html", context)


@login_required
def send_message(request, conversation_id):
    if request.method != "POST":
        return HttpResponseNotAllowed(["POST"])

    conversation = _get_conversation_for_user_or_404(conversation_id, request.user)

    content = request.POST.get("content", "").strip()
    if not content:
        messages.error(request, "Message cannot be empty.")
        return redirect("comunication:conversation_detail", conversation_id=conversation.pk)

    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    conversation.save(update_fields=["updated_at"])

    return redirect("comunication:conversation_detail", conversation_id=conversation.pk)