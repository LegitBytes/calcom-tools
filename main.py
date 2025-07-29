import boto3
import requests
from botocore.exceptions import ClientError
from dotenv import load_dotenv
load_dotenv()
def describe_table_schema(table_name, region='us-east-1'):
    """
    Print the key schema of the DynamoDB table.
    """
    dynamodb_client = boto3.client('dynamodb', region_name=region)
    try:
        response = dynamodb_client.describe_table(TableName=table_name)
        key_schema = response['Table']['KeySchema']
        print(f"Key Schema for '{table_name}': {key_schema}")
        return key_schema
    except ClientError as e:
        print(f"Failed to describe table '{table_name}': {e}")
        return None


def get_api_key_by_user_id(user_id_value, table_name='ApiKeys', region='us-east-1'):
    """
    Retrieve the API Key for a given userId from the DynamoDB table.
    """
    dynamodb = boto3.resource('dynamodb', region_name=region)
    table = dynamodb.Table(table_name)

    try:
        # Replace 'userId' below with your actual partition key name
        response = table.get_item(Key={
            'user_id': user_id_value
        })
        item = response.get('Item')
        if not item:
            print(f"No item found for userId: {user_id_value}")
            return None

        return item.get('key')

    except ClientError as e:
        print(f"Error retrieving API key for userId {user_id_value}: {e}")
        return None


def fetch_booking_by_email(email,api_key,api_version):
    """
    Fetch Booking for a User by Email
    """
    url = f"https://api.cal.com/v2/bookings"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "cal-api-verion": api_version
    }
    params = {
        "email": email
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json().get("bookings",[])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching bookings: {e}")
        return []

# Cancl a Booking of user with the ID
def cancel_booking(api_key, bookingUid, api_version):
    """
    Cancel a booking by its UID.
    
    Args:
        api_key (str): Cal.com API Key (Bearer Token)
        bookingUid (str): Booking UID
        api_version (str): Cal.com API version

    Returns:
        dict: API response from the cancellation request
    """
    url = f"https://api.cal.com/v2/bookings/{bookingUid}/cancel"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "cal-api-version": api_version,
        "Content-Type": "application/json"
    }
    payload = {
        "cancellationReason": "User requested cancellation",
        "cancelSubsequentBookings": True
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as http_err:
        return {"error": f"HTTP error occurred: {http_err}", "response": response.text}
    except Exception as err:
        return {"error": f"Other error occurred: {err}"}
    

def reschedule_booking_by_email_and_phone(email,phone_number,new_start_time,rescheduled_by,rescheduled_reason,api_key,api_version):
    """
    Find booking by email and phoneNumber, then reschedule it.
    """
    bookings = fetch_booking_by_email(email,api_key,api_version)
    print(f"Found {len(bookings)} bookings for email {email}")
    matching_booking = None
    for booking in bookings:
        if booking.get("phoneNumber") == phone_number:
            matching_booking = booking
            break
    if not matching_booking:
        print(f"No booking found for email {email} and phone number {phone_number}")
        return None
    
    booking_id = matching_booking.get("id")
    print(f"Rescheduling bookingId: {booking_id}")
    # Rescheduling Cal.com API
    url = f"https://api.cal.com/v2/bookings/{booking_id}/reschedule"
    payload = {
        "start": new_start_time,
        "rescheduledBy": rescheduled_by,
        "rescheduledReason": rescheduled_reason
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "cal-api-version": api_version,
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error rescheduling booking: {e}")
        if(response.content):
            print(response.content)
        return None

# Facing Issue in this API
def get_slot_availability(api_key,start_date,end_date,user,api_version):
    """
        Fetch Available Bookings from Cal.com
        Args:
            api_key (str): The API key for Cal.com.
            start_date (str): The start date for the availability check.
            end_date (str): The end date for the availability check.
            user (str): Cal.com Username 
            api_version (str): The API version to use.

        Returns:
            dict: The response from Cal.com containing the available bookings.
        """
    url = "https://api.cal.com/v2/slots"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "cal-api-version": api_version
    }
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "user": user
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        print(response)  
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching availability: {e}")
        return None

# Get Meeting Details
def get_meeting(api_key, calendar, event_uid):
    """
    Fetch a meeting (event) from Cal.com by calendar and event UID.

    Args:
        api_key (str): Cal.com API key (Bearer token).
        calendar (str): Cal.com calendar username (public identifier).
        event_uid (str): Unique event ID.

    Returns:
        dict: The event/meeting data if successful, else None.
    """
    url = f"https://api.cal.com/v2/calendars/{calendar}/event/{event_uid}"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"HTTP Error: {e} - {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Request Failed: {e}")
    
    return None


if __name__ == "__main__":
    API_KEY = "cal_live_4499276c6e342f41e0d00e5314fdef4e"
    CALENDAR_USERNAME = "aamir.majeed"  # Replace with your calendar username
    EVENT_UID = "evt_123456789"         # Replace with a real event UID

    event = get_meeting(API_KEY, CALENDAR_USERNAME, EVENT_UID)

    if event:
        print("Meeting Details:")
        print(event)
    else:
        print("Failed to fetch the meeting.")

# if __name__ == "__main__":
#     table_name = 'ApiKeys'
#     start_date = "2025-07-28"
#     end_date = "2025-07-28"
#     user = "aamir-majeed-8otwcq"
#     api_version = "2"
#     key = "cal_live_4499276c6e342f41e0d00e5314fdef4e"
#     slots = get_slot_availability(key,start_date,end_date,user,api_version)
#     print(slots)
#     if slots:
#         print("Available Slots: ",slots)
#         for slot in slots:
#             print(slot)
#     else:
#         print("No slots available")
    
# if __name__ == "__main__":
#     table_name = 'ApiKeys'
#     user_id_value = '339cc9f2-9d39-43b4-9e80-d1b5f79aed04'

#     # Step 1: Verify schema
#     key_schema = describe_table_schema(table_name)
#     if not key_schema:
#         print("Cannot proceed without correct schema.")
#     else:
#         # Step 2: Fetch API key
#         api_key = get_api_key_by_user_id(user_id_value, table_name)
#         if api_key:
#             print(f"API Key for userId {user_id_value}: {api_key}")
#             # Step 3: Fetch bookings
#             bookings = fetch_booking_by_email("aamajeed@legitbytes.com", api_key, "2")
#             print(f"Found {len(bookings)} bookings for email aamajeed@legitbytes.com")
#             # Step 4: Reschedule booking
#             reschedule_response = reschedule_booking_by_email_and_phone(
#                 "aamajeed@legitbytes.com", "+1234567890", "2023-12-25T10:00:00Z", "Aamir Majeed", "Rescheduled due to maintenance", api_key, "2")
#             print("Reschedule response:", reschedule_response)
#         else:
#             print(f"No API Key found for userId {user_id_value}")
