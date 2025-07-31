import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.utils import timezone
from .models import GoogleCalendarIntegration, CalendarEvent, CalendarSync


class GoogleCalendarService:
    """
    Service class for interacting with Google Calendar API
    """
    
    def __init__(self, integration: GoogleCalendarIntegration):
        self.integration = integration
        self.service = None
        self._build_service()
    
    def _build_service(self):
        """Build the Google Calendar service with proper authentication"""
        try:
            # Create credentials from stored tokens
            creds = Credentials(
                token=self.integration.access_token,
                refresh_token=self.integration.refresh_token,
                token_uri='https://oauth2.googleapis.com/token',
                client_id=os.getenv('GOOGLE_CLIENT_ID'),
                client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
                scopes=[self.integration.scope]
            )
            
            # Check if credentials need refresh
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                # Update stored tokens
                self.integration.access_token = creds.token
                self.integration.refresh_token = creds.refresh_token
                self.integration.token_expires_at = creds.expiry
                self.integration.save()
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=creds)
            
        except Exception as e:
            raise Exception(f"Failed to build Google Calendar service: {str(e)}")
    
    @staticmethod
    def get_auth_url(user_id: int) -> str:
        """Get Google OAuth authorization URL"""
        client_config = {
            'web': {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/integrations/google/callback')]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/integrations/google/callback')
        )
        
        auth_url, _ = flow.authorization_url(
            access_type='offline',
            include_granted_scopes='true',
            state=str(user_id)
        )
        
        return auth_url
    
    @staticmethod
    def exchange_code_for_tokens(code: str) -> Dict[str, Any]:
        """Exchange authorization code for access and refresh tokens"""
        client_config = {
            'web': {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'redirect_uris': [os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/integrations/google/callback')]
            }
        }
        
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/calendar'],
            redirect_uri=os.getenv('GOOGLE_REDIRECT_URI', 'http://localhost:3000/integrations/google/callback')
        )
        
        flow.fetch_token(code=code)
        
        return {
            'access_token': flow.credentials.token,
            'refresh_token': flow.credentials.refresh_token,
            'expires_at': flow.credentials.expiry,
            'scope': ' '.join(flow.credentials.scopes) if flow.credentials.scopes else ''
        }
    
    def get_user_info(self) -> Dict[str, Any]:
        """Get user information from Google"""
        try:
            # Use the calendar service to get calendar list and extract user info
            calendar_list = self.service.calendarList().list().execute()
            primary_calendar = None
            
            for calendar in calendar_list.get('items', []):
                if calendar.get('primary'):
                    primary_calendar = calendar
                    break
            
            if primary_calendar:
                return {
                    'email': primary_calendar.get('id'),
                    'summary': primary_calendar.get('summary', ''),
                }
            
            return {}
            
        except Exception as e:
            raise Exception(f"Failed to get user info: {str(e)}")
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars for the user"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            return calendar_list.get('items', [])
        except HttpError as e:
            raise Exception(f"Failed to list calendars: {str(e)}")
    
    def get_events(self, start_date: datetime = None, end_date: datetime = None, 
                   max_results: int = 100) -> List[Dict[str, Any]]:
        """Get events from the calendar"""
        try:
            # Default to next 30 days if no dates provided
            if not start_date:
                start_date = timezone.now()
            if not end_date:
                end_date = start_date + timedelta(days=30)
            
            # Convert to RFC3339 format
            time_min = start_date.isoformat()
            time_max = end_date.isoformat()
            
            events_result = self.service.events().list(
                calendarId=self.integration.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
            
        except HttpError as e:
            raise Exception(f"Failed to get events: {str(e)}")
    
    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            event = self.service.events().insert(
                calendarId=self.integration.calendar_id,
                body=event_data
            ).execute()
            
            return event
            
        except HttpError as e:
            raise Exception(f"Failed to create event: {str(e)}")
    
    def update_event(self, event_id: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing calendar event"""
        try:
            event = self.service.events().update(
                calendarId=self.integration.calendar_id,
                eventId=event_id,
                body=event_data
            ).execute()
            
            return event
            
        except HttpError as e:
            raise Exception(f"Failed to update event: {str(e)}")
    
    def delete_event(self, event_id: str) -> bool:
        """Delete a calendar event"""
        try:
            self.service.events().delete(
                calendarId=self.integration.calendar_id,
                eventId=event_id
            ).execute()
            
            return True
            
        except HttpError as e:
            if e.resp.status == 410:  # Event already deleted
                return True
            raise Exception(f"Failed to delete event: {str(e)}")
    
    def create_meeting_event(self, title: str, description: str, start_datetime: datetime,
                           end_datetime: datetime, attendees: List[str] = None,
                           location: str = None, timezone_str: str = 'UTC') -> Dict[str, Any]:
        """Create a meeting event with Google Meet integration"""
        
        # Convert datetime objects to RFC3339 format
        start_time = start_datetime.isoformat()
        end_time = end_datetime.isoformat()
        
        # Build attendees list
        attendees_list = []
        if attendees:
            attendees_list = [{'email': email} for email in attendees]
        
        event_data = {
            'summary': title,
            'description': description,
            'start': {
                'dateTime': start_time,
                'timeZone': timezone_str,
            },
            'end': {
                'dateTime': end_time,
                'timeZone': timezone_str,
            },
            'attendees': attendees_list,
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                    {'method': 'popup', 'minutes': 15},       # 15 minutes before
                ],
            },
            'conferenceData': {
                'createRequest': {
                    'requestId': f"meet-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                    'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                }
            }
        }
        
        if location:
            event_data['location'] = location
        
        try:
            # Create event with conference data
            event = self.service.events().insert(
                calendarId=self.integration.calendar_id,
                body=event_data,
                conferenceDataVersion=1  # Required for Google Meet integration
            ).execute()
            
            return event
            
        except HttpError as e:
            raise Exception(f"Failed to create meeting event: {str(e)}")
    
    def sync_events_to_database(self, start_date: datetime = None, 
                               end_date: datetime = None) -> CalendarSync:
        """Sync events from Google Calendar to local database"""
        
        # Create sync record
        sync_record = CalendarSync.objects.create(
            integration=self.integration,
            sync_type='full',
            status='in_progress'
        )
        
        try:
            # Get events from Google Calendar
            google_events = self.get_events(start_date, end_date)
            
            events_created = 0
            events_updated = 0
            
            for google_event in google_events:
                event_data = self._parse_google_event(google_event)
                
                # Create or update local event record
                calendar_event, created = CalendarEvent.objects.update_or_create(
                    google_event_id=google_event['id'],
                    defaults=event_data
                )
                
                if created:
                    events_created += 1
                else:
                    events_updated += 1
            
            # Update sync record
            sync_record.status = 'completed'
            sync_record.completed_at = timezone.now()
            sync_record.events_synced = len(google_events)
            sync_record.events_created = events_created
            sync_record.events_updated = events_updated
            sync_record.save()
            
            return sync_record
            
        except Exception as e:
            # Update sync record with error
            sync_record.status = 'failed'
            sync_record.error_message = str(e)
            sync_record.completed_at = timezone.now()
            sync_record.save()
            
            raise e
    
    def _parse_google_event(self, google_event: Dict[str, Any]) -> Dict[str, Any]:
        """Parse Google Calendar event data for local storage"""
        
        # Parse start and end times
        start = google_event.get('start', {})
        end = google_event.get('end', {})
        
        # Handle all-day events
        if 'date' in start:
            start_datetime = datetime.strptime(start['date'], '%Y-%m-%d')
            end_datetime = datetime.strptime(end['date'], '%Y-%m-%d')
            all_day = True
            timezone_str = 'UTC'
        else:
            start_datetime = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
            end_datetime = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
            all_day = False
            timezone_str = start.get('timeZone', 'UTC')
        
        # Parse attendees
        attendees = []
        for attendee in google_event.get('attendees', []):
            attendees.append({
                'email': attendee.get('email'),
                'displayName': attendee.get('displayName'),
                'responseStatus': attendee.get('responseStatus', 'needsAction'),
                'organizer': attendee.get('organizer', False)
            })
        
        # Parse reminders
        reminders = []
        reminder_data = google_event.get('reminders', {})
        if reminder_data.get('useDefault'):
            reminders.append({'method': 'default'})
        else:
            for override in reminder_data.get('overrides', []):
                reminders.append({
                    'method': override.get('method'),
                    'minutes': override.get('minutes')
                })
        
        # Extract Google Meet link
        hangout_link = google_event.get('hangoutLink')
        meeting_url = hangout_link
        
        # Check for other conference data
        conference_data = google_event.get('conferenceData', {})
        if conference_data and not meeting_url:
            entry_points = conference_data.get('entryPoints', [])
            for entry_point in entry_points:
                if entry_point.get('entryPointType') == 'video':
                    meeting_url = entry_point.get('uri')
                    break
        
        return {
            'integration': self.integration,
            'title': google_event.get('summary', 'Untitled Event'),
            'description': google_event.get('description', ''),
            'location': google_event.get('location', ''),
            'start_datetime': start_datetime,
            'end_datetime': end_datetime,
            'timezone': timezone_str,
            'all_day': all_day,
            'recurring': 'recurrence' in google_event,
            'recurrence_rule': '\n'.join(google_event.get('recurrence', [])),
            'status': google_event.get('status', 'confirmed'),
            'transparency': google_event.get('transparency', 'opaque'),
            'attendees': attendees,
            'creator_email': google_event.get('creator', {}).get('email'),
            'organizer_email': google_event.get('organizer', {}).get('email'),
            'hangout_link': hangout_link,
            'meeting_url': meeting_url,
            'visibility': google_event.get('visibility', 'default'),
            'reminders': reminders,
            'google_created_at': datetime.fromisoformat(
                google_event.get('created', timezone.now().isoformat()).replace('Z', '+00:00')
            ),
            'google_updated_at': datetime.fromisoformat(
                google_event.get('updated', timezone.now().isoformat()).replace('Z', '+00:00')
            )
        }
    
    def check_availability(self, start_datetime: datetime, end_datetime: datetime,
                          attendee_emails: List[str] = None) -> Dict[str, Any]:
        """Check availability for meeting scheduling"""
        try:
            # Prepare the freebusy query
            body = {
                'timeMin': start_datetime.isoformat(),
                'timeMax': end_datetime.isoformat(),
                'items': [{'id': self.integration.calendar_id}]
            }
            
            # Add attendee calendars if provided
            if attendee_emails:
                for email in attendee_emails:
                    body['items'].append({'id': email})
            
            # Query freebusy information
            freebusy_result = self.service.freebusy().query(body=body).execute()
            
            return freebusy_result
            
        except HttpError as e:
            raise Exception(f"Failed to check availability: {str(e)}")
    
    def find_meeting_slots(self, duration_minutes: int, start_date: datetime,
                          end_date: datetime, attendee_emails: List[str] = None,
                          working_hours_start: int = 9, working_hours_end: int = 17) -> List[Dict[str, Any]]:
        """Find available meeting slots within the specified time range"""
        
        available_slots = []
        current_date = start_date.date()
        end_date_only = end_date.date()
        
        while current_date <= end_date_only:
            # Skip weekends (optional - can be made configurable)
            if current_date.weekday() >= 5:  # Saturday = 5, Sunday = 6
                current_date += timedelta(days=1)
                continue
            
            # Check each hour within working hours
            for hour in range(working_hours_start, working_hours_end):
                slot_start = datetime.combine(current_date, datetime.min.time().replace(hour=hour))
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                
                # Make timezone-aware
                if timezone.is_naive(slot_start):
                    slot_start = timezone.make_aware(slot_start)
                    slot_end = timezone.make_aware(slot_end)
                
                # Check if this slot conflicts with existing events
                try:
                    freebusy_result = self.check_availability(slot_start, slot_end, attendee_emails)
                    
                    # Check if any calendar has busy time during this slot
                    is_available = True
                    for calendar_id, calendar_data in freebusy_result.get('calendars', {}).items():
                        busy_times = calendar_data.get('busy', [])
                        for busy_time in busy_times:
                            busy_start = datetime.fromisoformat(busy_time['start'].replace('Z', '+00:00'))
                            busy_end = datetime.fromisoformat(busy_time['end'].replace('Z', '+00:00'))
                            
                            # Check for overlap
                            if (slot_start < busy_end and slot_end > busy_start):
                                is_available = False
                                break
                        
                        if not is_available:
                            break
                    
                    if is_available:
                        available_slots.append({
                            'start': slot_start,
                            'end': slot_end,
                            'duration_minutes': duration_minutes
                        })
                
                except Exception:
                    # If we can't check availability, skip this slot
                    continue
            
            current_date += timedelta(days=1)
        
        return available_slots[:10]  # Return top 10 slots