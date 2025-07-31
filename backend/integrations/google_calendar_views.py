from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import GoogleCalendarIntegration, CalendarEvent, MeetingSchedule, CalendarSync
from .serializers import (
    GoogleCalendarIntegrationSerializer, CalendarEventSerializer, 
    MeetingScheduleSerializer, CalendarSyncSerializer
)
from .google_calendar_service import GoogleCalendarService


class GoogleCalendarIntegrationViewSet(viewsets.ModelViewSet):
    serializer_class = GoogleCalendarIntegrationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return GoogleCalendarIntegration.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'], url_path='auth-url')
    def get_auth_url(self, request):
        """Get Google Calendar OAuth authorization URL"""
        try:
            auth_url = GoogleCalendarService.get_auth_url(request.user.id)
            return Response({'auth_url': auth_url})
        except Exception as e:
            return Response(
                {'error': f'Failed to generate auth URL: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='connect')
    def connect_google_calendar(self, request):
        """Handle Google Calendar OAuth callback and create integration"""
        code = request.data.get('code')
        state = request.data.get('state')
        
        if not code:
            return Response(
                {'error': 'Authorization code is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if str(state) != str(request.user.id):
            return Response(
                {'error': 'Invalid state parameter'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Exchange code for tokens
            token_data = GoogleCalendarService.exchange_code_for_tokens(code)
            
            # Create or update integration
            integration, created = GoogleCalendarIntegration.objects.update_or_create(
                user=request.user,
                defaults={
                    'access_token': token_data['access_token'],
                    'refresh_token': token_data['refresh_token'],
                    'token_expires_at': token_data['expires_at'],
                    'scope': token_data['scope'],
                }
            )
            
            # Get user info and update integration
            try:
                service = GoogleCalendarService(integration)
                user_info = service.get_user_info()
                integration.google_user_email = user_info.get('email', '')
                integration.save()
            except Exception as user_info_error:
                # If we can't get user info, that's okay, we'll continue
                pass
            
            serializer = self.get_serializer(integration)
            return Response({
                'integration': serializer.data,
                'created': created
            }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to connect Google Calendar: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'], url_path='disconnect')
    def disconnect_google_calendar(self, request, pk=None):
        """Disconnect Google Calendar integration"""
        try:
            integration = self.get_object()
            integration.delete()
            
            return Response({'message': 'Google Calendar integration disconnected successfully'})
        except Exception as e:
            return Response(
                {'error': f'Failed to disconnect Google Calendar: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='calendars')
    def list_calendars(self, request, pk=None):
        """List all calendars for the user"""
        try:
            integration = self.get_object()
            service = GoogleCalendarService(integration)
            
            calendars = service.list_calendars()
            
            return Response({'calendars': calendars})
            
        except Exception as e:
            return Response(
                {'error': f'Failed to list calendars: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='sync-events')
    def sync_events(self, request, pk=None):
        """Sync events from Google Calendar"""
        try:
            integration = self.get_object()
            service = GoogleCalendarService(integration)
            
            # Get optional date range from request
            start_date_str = request.data.get('start_date')
            end_date_str = request.data.get('end_date')
            
            start_date = None
            end_date = None
            
            if start_date_str:
                start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            if end_date_str:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            
            # Sync events
            sync_record = service.sync_events_to_database(start_date, end_date)
            
            serializer = CalendarSyncSerializer(sync_record)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to sync events: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='check-availability')
    def check_availability(self, request, pk=None):
        """Check availability for meeting scheduling"""
        try:
            integration = self.get_object()
            service = GoogleCalendarService(integration)
            
            start_datetime_str = request.data.get('start_datetime')
            end_datetime_str = request.data.get('end_datetime')
            attendee_emails = request.data.get('attendee_emails', [])
            
            if not start_datetime_str or not end_datetime_str:
                return Response(
                    {'error': 'start_datetime and end_datetime are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            start_datetime = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_datetime_str.replace('Z', '+00:00'))
            
            availability = service.check_availability(start_datetime, end_datetime, attendee_emails)
            
            return Response(availability)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to check availability: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='find-meeting-slots')
    def find_meeting_slots(self, request, pk=None):
        """Find available meeting slots"""
        try:
            integration = self.get_object()
            service = GoogleCalendarService(integration)
            
            duration_minutes = request.data.get('duration_minutes', 60)
            start_date_str = request.data.get('start_date')
            end_date_str = request.data.get('end_date')
            attendee_emails = request.data.get('attendee_emails', [])
            working_hours_start = request.data.get('working_hours_start', 9)
            working_hours_end = request.data.get('working_hours_end', 17)
            
            if not start_date_str or not end_date_str:
                return Response(
                    {'error': 'start_date and end_date are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            
            available_slots = service.find_meeting_slots(
                duration_minutes, start_date, end_date, attendee_emails,
                working_hours_start, working_hours_end
            )
            
            # Convert datetime objects to ISO strings for JSON serialization
            for slot in available_slots:
                slot['start'] = slot['start'].isoformat()
                slot['end'] = slot['end'].isoformat()
            
            return Response({'available_slots': available_slots})
            
        except Exception as e:
            return Response(
                {'error': f'Failed to find meeting slots: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class CalendarEventViewSet(viewsets.ModelViewSet):
    serializer_class = CalendarEventSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CalendarEvent.objects.filter(
            integration__user=self.request.user
        )

    @action(detail=False, methods=['post'], url_path='create-from-google')
    def create_event_in_google(self, request):
        """Create a new event in Google Calendar"""
        try:
            integration = GoogleCalendarIntegration.objects.get(user=request.user)
            service = GoogleCalendarService(integration)
            
            title = request.data.get('title', '')
            description = request.data.get('description', '')
            start_datetime_str = request.data.get('start_datetime')
            end_datetime_str = request.data.get('end_datetime')
            attendees = request.data.get('attendees', [])
            location = request.data.get('location', '')
            timezone_str = request.data.get('timezone', 'UTC')
            
            if not title or not start_datetime_str or not end_datetime_str:
                return Response(
                    {'error': 'title, start_datetime, and end_datetime are required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            start_datetime = datetime.fromisoformat(start_datetime_str.replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end_datetime_str.replace('Z', '+00:00'))
            
            # Create event in Google Calendar
            google_event = service.create_meeting_event(
                title, description, start_datetime, end_datetime,
                attendees, location, timezone_str
            )
            
            # Parse and save to local database
            event_data = service._parse_google_event(google_event)
            calendar_event = CalendarEvent.objects.create(**event_data)
            
            serializer = self.get_serializer(calendar_event)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except GoogleCalendarIntegration.DoesNotExist:
            return Response(
                {'error': 'Google Calendar integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create event: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['put'], url_path='update-in-google')
    def update_event_in_google(self, request, pk=None):
        """Update an event in Google Calendar"""
        try:
            event = self.get_object()
            service = GoogleCalendarService(event.integration)
            
            # Build event data from request
            event_data = {}
            
            if 'title' in request.data:
                event_data['summary'] = request.data['title']
            if 'description' in request.data:
                event_data['description'] = request.data['description']
            if 'location' in request.data:
                event_data['location'] = request.data['location']
                
            if 'start_datetime' in request.data and 'end_datetime' in request.data:
                start_datetime = datetime.fromisoformat(request.data['start_datetime'].replace('Z', '+00:00'))
                end_datetime = datetime.fromisoformat(request.data['end_datetime'].replace('Z', '+00:00'))
                timezone_str = request.data.get('timezone', event.timezone)
                
                event_data['start'] = {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': timezone_str,
                }
                event_data['end'] = {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': timezone_str,
                }
            
            if 'attendees' in request.data:
                event_data['attendees'] = [
                    {'email': email} for email in request.data['attendees']
                ]
            
            # Update event in Google Calendar
            updated_google_event = service.update_event(event.google_event_id, event_data)
            
            # Update local database record
            updated_event_data = service._parse_google_event(updated_google_event)
            for key, value in updated_event_data.items():
                if key not in ['integration']:  # Don't update the integration field
                    setattr(event, key, value)
            event.save()
            
            serializer = self.get_serializer(event)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update event: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['delete'], url_path='delete-from-google')
    def delete_event_from_google(self, request, pk=None):
        """Delete an event from Google Calendar"""
        try:
            event = self.get_object()
            service = GoogleCalendarService(event.integration)
            
            # Delete from Google Calendar
            success = service.delete_event(event.google_event_id)
            
            if success:
                # Delete from local database
                event.delete()
                return Response({'message': 'Event deleted successfully'})
            else:
                return Response(
                    {'error': 'Failed to delete event from Google Calendar'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            return Response(
                {'error': f'Failed to delete event: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class MeetingScheduleViewSet(viewsets.ModelViewSet):
    serializer_class = MeetingScheduleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MeetingSchedule.objects.filter(
            project__team__members__user=self.request.user
        )

    def create(self, request, *args, **kwargs):
        """Create a meeting schedule and optionally create Google Calendar event"""
        create_calendar_event = request.data.get('create_calendar_event', False)
        
        # Create the meeting schedule first
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meeting = serializer.save(created_by=request.user)
        
        # If requested, create Google Calendar event
        if create_calendar_event:
            try:
                integration = GoogleCalendarIntegration.objects.get(user=request.user)
                service = GoogleCalendarService(integration)
                
                # Get attendee emails
                attendee_emails = [user.email for user in meeting.attendees.all() if user.email]
                
                # Create Google Calendar event
                google_event = service.create_meeting_event(
                    title=meeting.title,
                    description=meeting.description or '',
                    start_datetime=meeting.start_datetime,
                    end_datetime=meeting.end_datetime,
                    attendees=attendee_emails,
                    location=meeting.location or '',
                    timezone_str=meeting.timezone
                )
                
                # Create CalendarEvent record and link to meeting
                event_data = service._parse_google_event(google_event)
                calendar_event = CalendarEvent.objects.create(**event_data)
                calendar_event.project = meeting.project
                calendar_event.save()
                
                # Link the meeting to the calendar event
                meeting.calendar_event = calendar_event
                meeting.meeting_url = calendar_event.meeting_url or calendar_event.hangout_link
                meeting.save()
                
            except GoogleCalendarIntegration.DoesNotExist:
                # If no Google Calendar integration, that's okay
                pass
            except Exception as calendar_error:
                # Log the error but don't fail the meeting creation
                print(f"Failed to create calendar event: {calendar_error}")
        
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='create-calendar-event')
    def create_calendar_event(self, request, pk=None):
        """Create a Google Calendar event for an existing meeting"""
        try:
            meeting = self.get_object()
            
            if meeting.calendar_event:
                return Response(
                    {'error': 'Calendar event already exists for this meeting'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            integration = GoogleCalendarIntegration.objects.get(user=request.user)
            service = GoogleCalendarService(integration)
            
            # Get attendee emails
            attendee_emails = [user.email for user in meeting.attendees.all() if user.email]
            
            # Create Google Calendar event
            google_event = service.create_meeting_event(
                title=meeting.title,
                description=meeting.description or '',
                start_datetime=meeting.start_datetime,
                end_datetime=meeting.end_datetime,
                attendees=attendee_emails,
                location=meeting.location or '',
                timezone_str=meeting.timezone
            )
            
            # Create CalendarEvent record and link to meeting
            event_data = service._parse_google_event(google_event)
            calendar_event = CalendarEvent.objects.create(**event_data)
            calendar_event.project = meeting.project
            calendar_event.save()
            
            # Link the meeting to the calendar event
            meeting.calendar_event = calendar_event
            meeting.meeting_url = calendar_event.meeting_url or calendar_event.hangout_link
            meeting.save()
            
            serializer = self.get_serializer(meeting)
            return Response(serializer.data)
            
        except GoogleCalendarIntegration.DoesNotExist:
            return Response(
                {'error': 'Google Calendar integration not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Failed to create calendar event: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'], url_path='update-status')
    def update_status(self, request, pk=None):
        """Update meeting status"""
        try:
            meeting = self.get_object()
            new_status = request.data.get('status')
            
            if not new_status:
                return Response(
                    {'error': 'Status is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if new_status not in dict(MeetingSchedule.STATUS_CHOICES):
                return Response(
                    {'error': 'Invalid status'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            meeting.status = new_status
            
            # Add notes and action items if provided
            if 'notes' in request.data:
                meeting.notes = request.data['notes']
            if 'action_items' in request.data:
                meeting.action_items = request.data['action_items']
            
            meeting.save()
            
            serializer = self.get_serializer(meeting)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to update meeting status: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class CalendarSyncViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CalendarSyncSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CalendarSync.objects.filter(
            integration__user=self.request.user
        )