from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q, F, OuterRef, Subquery
from .models import Message, UserActivity, RequestResponse

@login_required
def messages_view(request, contact_id=None):
    # Get all users that the current user has exchanged messages with
    contacts_with_messages = User.objects.filter(
        Q(sent_messages__receiver=request.user) | Q(received_messages__sender=request.user)
    ).distinct()
    
    # Get the latest message for each contact
    latest_messages = Message.objects.filter(
        Q(sender=request.user, receiver=OuterRef('pk')) | 
        Q(receiver=request.user, sender=OuterRef('pk'))
    ).order_by('-created_at').values('content')[:1]
    
    # Get contacts with their latest message
    from django.db.models import Count, Max, Case, When, F, Value, DateTimeField
    from django.db.models.functions import Greatest
    
    # Get all contacts with their latest message timestamp
    # Use separate annotations for sent and received messages, then use Greatest to find the latest
    contacts = contacts_with_messages.annotate(
        latest_sent=Max('sent_messages__created_at', filter=Q(sent_messages__receiver=request.user)),
        latest_received=Max('received_messages__created_at', filter=Q(received_messages__sender=request.user))
    ).annotate(
        # Use Case/When to handle NULL values
        last_message_time=Case(
            When(latest_sent__isnull=False, latest_received__isnull=False,
                 then=Greatest('latest_sent', 'latest_received')),
            When(latest_sent__isnull=False, then=F('latest_sent')),
            When(latest_received__isnull=False, then=F('latest_received')),
            default=None,
            output_field=DateTimeField()
        )
    ).order_by('-last_message_time')
    
    # Prepare contact data with additional information
    for contact in contacts:
        # Get the latest message content
        latest_message = Message.objects.filter(
            (Q(sender=request.user, receiver=contact) | Q(receiver=request.user, sender=contact))
        ).order_by('-created_at').first()
        
        if latest_message:
            contact.last_message = latest_message.content
        else:
            contact.last_message = ''
        
        # Count unread messages
        contact.unread_count = Message.objects.filter(
            sender=contact,
            receiver=request.user,
            is_read=False
        ).count()
        
        # Check if user is online (active today)
        contact.is_online = contact.last_login and contact.last_login.date() == timezone.now().date()
    
    active_contact = None
    messages_list = []
    
    # If a specific contact is selected, get the conversation
    if contact_id:
        try:
            active_contact = User.objects.get(id=contact_id)
            # Get all messages between the current user and the selected contact
            messages_list = Message.objects.filter(
                (Q(sender=request.user, receiver=active_contact) | 
                 Q(receiver=request.user, sender=active_contact))
            ).select_related('sender', 'receiver', 'response').order_by('created_at')
            
            # Mark messages as read
            unread_messages = messages_list.filter(receiver=request.user, is_read=False)
            unread_count = unread_messages.count()
            unread_messages.update(is_read=True)
            
            if unread_count > 0:
                # Log activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f"Read {unread_count} new messages from {active_contact.username}"
                )
            
        except User.DoesNotExist:
            messages.error(request, 'Contact not found!')
    
    context = {
        'contacts': contacts,
        'active_contact': active_contact,
        'messages_list': messages_list,
    }
    
    return render(request, 'users/messages.html', context)

@login_required
def send_message_view(request, receiver_id):
    if request.method == 'POST':
        try:
            receiver = User.objects.get(id=receiver_id)
            content = request.POST.get('message', '').strip()
            
            if content:
                # Create new message
                Message.objects.create(
                    sender=request.user,
                    receiver=receiver,
                    content=content
                )
                
                # Log activity
                UserActivity.objects.create(
                    user=request.user,
                    activity_type='other',
                    description=f"Sent a message to {receiver.username}"
                )
                
                messages.success(request, 'Message sent successfully!')
            else:
                messages.error(request, 'Message cannot be empty!')
                
        except User.DoesNotExist:
            messages.error(request, 'Recipient not found!')
    
    return redirect('messages', contact_id=receiver_id)

@login_required
def contact_seller_view(request, response_id):
    try:
        # Get the response
        response = RequestResponse.objects.get(id=response_id)
        
        # The seller is the user who created the response
        seller = response.user
        
        # Check if this is the first message for this response
        if not Message.objects.filter(response=response).exists():
            # Create a message with information about the part
            if response.search_request:
                part_info = response.search_request.search
                car_info = f"{response.search_request.make} {response.search_request.model}"
                initial_message = f"Здравствуйте! Я интересуюсь запчастью '{part_info}' для {car_info}, на которую вы ответили."
            else:
                part_info = response.seller_request.part_name
                car_info = f"{response.seller_request.make} {response.seller_request.model}"
                initial_message = f"Здравствуйте! Я интересуюсь запчастью '{part_info}' для {car_info}, которую вы продаете."
            
            # Create the message
            Message.objects.create(
                sender=request.user,
                receiver=seller,
                response=response,
                content=initial_message
            )
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                activity_type='other',
                description=f"Started conversation with {seller.username} about {part_info}"
            )
        
        # Redirect to messages with this seller
        return redirect('messages', contact_id=seller.id)
        
    except RequestResponse.DoesNotExist:
        messages.error(request, 'Response not found!')
        return redirect('results')
