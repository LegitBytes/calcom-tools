import boto3
import requests
from botocore.exceptions import ClientError
import base64
from dotenv import load_dotenv
from typing import List,Dict,Optional
load_dotenv()

def get_decrypted_key_from_dynamodb(table_name, key, region='us-east-1'):
    dynamodb_client = boto3.client('dynamodb', region_name=region)
    kms_client = boto3.client('kms', region_name=region)

    try:
        response = dynamodb_client.get_item(TableName=table_name, Key=key)
        item = response.get('Item')

        if not item or 'key' not in item:
            print("Encrypted key not found in the item.")
            return None

        # Decode the base64-encoded string to binary
        encrypted_blob = base64.b64decode(item['key']['S'])

        # Decrypt with KMS
        decrypted_response = kms_client.decrypt(CiphertextBlob=encrypted_blob)
        decrypted_key = decrypted_response['Plaintext'].decode('utf-8')

        print(f"✅ Decrypted Key: {decrypted_key}")
        return decrypted_key

    except ClientError as e:
        print(f"❌ AWS error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None

# ******************************
# This one is Working
# if __name__ == "__main__":
#     get_key = get_decrypted_key_from_dynamodb('ApiKeys', {'user_id': {'S': '339cc9f2-9d39-43b4-9e80-d1b5f79aed04'}})
#     if get_key:
#         print("Decrypted Key:", get_key)
#     else:
#         print("Failed to retrieve or decrypt the key.") 
# A tool for creating a Booking
def create_cal_booking(
    api_key: str,
    start: str,
    attendee: Dict[str, str],
    event_type_id: int,
    event_type_slug: str,
    guests: Optional[List[str]] = None,
    booking_fields: Optional[Dict[str, str]] = None,
    metadata: Optional[Dict[str, str]] = None,
    routing: Optional[Dict] = None,
    api_version: str = "2024-08-13"
) -> Dict:
    """
    Create a booking on Cal.com via REST API.

    Args:
        api_key (str): Cal.com API key.
        start (str): ISO 8601 timestamp for booking start (e.g., "2025-08-13T09:00:00Z").
        attendee (dict): Dictionary with attendee info (name, email, timeZone, phoneNumber, language).
        event_type_id (int): Event type ID from Cal.com.
        event_type_slug (str): Event type slug (e.g., "30min").
        guests (list): Optional list of guest email addresses.
        booking_fields (dict): Optional custom booking field responses.
        metadata (dict): Optional metadata.
        routing (dict): Optional routing options (responseId, teamMemberIds).
        api_version (str): Cal.com API version (default "2024-08-13").

    Returns:
        dict: Response from Cal.com API.
    """
    url = "https://api.cal.com/v2/bookings"
    headers = {
        "Content-Type": "application/json",
        "cal-api-version": api_version,
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "start": start,
        "attendee": attendee,
        "eventTypeId": event_type_id,
        "eventTypeSlug": event_type_slug
    }

    if guests:
        payload["guests"] = guests
    if booking_fields:
        payload["bookingFieldsResponses"] = booking_fields
    if metadata:
        payload["metadata"] = metadata
    if routing:
        payload["routing"] = routing

    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        print("✅ Booking created.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print("❌ Booking failed:", e)
        if e.response is not None:
            print("Response:", e.response.text)
        return {"error": str(e)}

# To create a Booking
if __name__ == "__main__":
    response = create_cal_booking(
        api_key="cal_live_4499276c6e342f41e0d00e5314fdef4e",
        start="2025-08-01T08:00:00Z",
        attendee={
            "name": "Anas Quershi",
            "email": "moanas@legitbytes.com",
            "timeZone": "Asia/Kolkata",
            "phoneNumber": "+919876543210",
            "language": "en",
            "name": "Aamir Majeed",
            "email": "aamajeed@legitbytes.com",
            "phoneNumber": "+918082580873",
            "timeZone": "Asia/Kolkata",
            "language": "en",
        },
        event_type_id=2910092,
        event_type_slug="project",
        guests=["moanaq@legitbytes.com"],
        booking_fields={"customField": "customValue"},
        metadata={"key": "value"},
        routing={"responseId": 123, "teamMemberIds": [101, 102]}
    )

#     print(response)
# ***********************************

def reschedule_cal_booking(api_key: str,bookingUid: str,api_version:str = "2024-08-13") -> Dict:
    """
    Reschedule a Cal.com booking.

    Args:
        api_key (str): Cal.com API key.
        bookingUid (str): UID of the booking to reschedule.
        api_version (str): Cal.com API version.

    Returns:
        dict: JSON response from Cal.com API.
    """
    url = f"https://api.cal.com/v2/bookings/{bookingUid}/reschedule"
    headers = {
        "cal-api-version": api_version,
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        print("✅ Booking rescheduled.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print("❌ Booking reschedule failed:", e)
        return {"error": str(e)}

# Test the Reshedule a booking
# if __name__ == "__main__":
#     api_key = get_decrypted_key_from_dynamodb('ApiKeys',{'user_id': {'S': '339cc9f2-9d39-43b4-9e80-d1b5f79aed04'}})
#     bookingUid = "w8yRvDzeWUwyFNrGesqgyq"
#     api_version = "2024-08-13"
#     response = reschedule_cal_booking(api_key,bookingUid,api_version)
#     print("response--->",response)

def get_cal_bookings(api_key: str,attendee_email,take:int =100,api_version:str = "2024-08-13") -> Dict:
    """
    Fetch Cal.com bookins for a specific attendee email.

    Args:
        api_key (str): Cal.com API key.
        attendee_email (str): Email of the attendee to search for.
        take (int): Number of bookings to fetch (max limit).
        api_version (str): Cal.com API version.

    Returns:
        dict: JSON response from Cal.com API
    """
    url = "https://api.cal.com/v2/bookings"
    headers = {
        "cal-api-version": api_version,
        "Authorization": f"Bearer {api_key}"
    }
    params = {
        "take": take,
        "attendeeEmail": attendee_email
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print("❌ Error fetching bookings:", e)
        return {"error": str(e)}

# To List the attendee Bookings / GET all Bookings
# **********************
# if __name__ == "__main__":
#     response = get_cal_bookings(api_key="cal_live_4499276c6e342f41e0d00e5314fdef4e",attendee_email="moanasq@legitbytes.com",take="10",api_version="2024-08-13")
#     print("Respnse from get_cal_bookings---",response)
# **********************

# Get a Booking
def get_cal_booking_by_id(api_key: str, booking_id: str, api_version: str = "2024-08-13") -> Dict:
    """
    Fetch a specific Cal.com booking by its ID.

    Args:
        api_key (str): Cal.com API key.
        booking_id (str): ID of the booking to fetch.
        api_version (str): Cal.com API version.

    Returns:
        dict: JSON response from Cal.com API.
    """
    url = f"https://api.cal.com/v2/bookings/{booking_id}"
    headers = {
        "cal-api-version": api_version,
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        print("✅ Booking fetched successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print("❌ Error fetching booking:", e)
        if e.response is not None:
            print("Response:", e.response.text)
        return {"error": str(e)}

# ***********

# if __name__ == "__main__":
#     bookingUid = "ju8zQ8YeKovLYZxBc9z4Er"
#     response = get_cal_booking_by_id(api_key="cal_live_4499276c6e342f41e0d00e5314fdef4e",booking_id=bookingUid,api_version="2024-18-13")
#     print("response=========",response)
# ***********


# Get All Calenders
def get_calenders(api_key: str) -> Dict:
    """
    Fetch all the Calenders associated with Cal.com
    
    Args:
        api_key (str): Cal.com API key
    
    Returns:
        dict: JSON response from Cal.com API
    """
    print("Fetching Calenders")
    url = "https://api.cal.com/v2/calendars"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        response = requests.get(url,headers=headers)
        response.raise_for_status()
        print("✅ Calendars fetched successfully.")
        return response.json()
    except requests.exceptions.RequestException as e:
        print("❌ Error fetching calendars:", e)
        if e.response is not None:
            print("Response:", e.response.text)

# if __name__ == "__main__":
#     api_key = "cal_live_4499276c6e342f41e0d00e5314fdef4e"
#     calenders = get_calenders(api_key)
#     print("Calenders:", calenders)




# This one is Optional
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

# Test the Cancel Booking tool
# if __name__ == "__main__":
#     api_key = get_decrypted_key_from_dynamodb('ApiKeys', {'user_id': {'S': '339cc9f2-9d39-43b4-9e80-d1b5f79aed04'}})
#     print('api-key--->',api_key)
#     bookingUid = "w8yRvDzeWUwyFNrGesqgyq"
#     response = cancel_booking(api_key, bookingUid, "2024-08-13")
#     print("response=========", response)

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
# ***************
# if __name__ == "__main__":
#     table_name = 'ApiKeys'
#     user_id_value = '339cc9f2-9d39-43b4-9e80-d1b5f79aed04'
#     api_key = get_decrypted_key_from_dynamodb(table_name, {'user_id': {'S': user_id_value}})
#     print("apiKey--->",api_key)
    # Step 1: Verify schema
    # key_schema = describe_table_schema(table_name)
    # if not key_schema:
    #     print("Cannot proceed without correct schema.")
    # else:
    # Step 2: Fetch API key
    # api_key = get_api_key_by_user_id(user_id_value, table_name)
    # if api_key:
    #     print(f"API Key for userId {user_id_value}: {api_key}")
    #         # Step 3: Fetch bookings
    #     bookings = fetch_booking_by_email("aamajeed@legitbytes.com", api_key, "2024-08-13")
    #     print(f"Found {len(bookings)} bookings for email aamajeed@legitbytes.com")
    #         # Step 4: Reschedule booking
    #     reschedule_response = reschedule_booking_by_email_and_phone(
    #             "aamajeed@legitbytes.com", "+8360991407", "2023-12-25T10:00:00Z", "Aamir Majeed", "Rescheduled due to maintenance", api_key, "2024-08-13")
    #     print("Reschedule response:", reschedule_response)
    # else:
    #     print(f"No API Key found for userId {user_id_value}")
# ***************

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
#             bookings = fetch_booking_by_email("aamajeed@legitbytes.com", api_key, "2024-08-13")
#             print(f"Found {len(bookings)} bookings for email aamajeed@legitbytes.com")
#             # Step 4: Reschedule booking
#             reschedule_response = reschedule_booking_by_email_and_phone(
#                 "aamajeed.legitbytes@gmail.com", "+8360991407", "2023-12-25T10:00:00Z", "Aamir Majeed", "Rescheduled due to maintenance", api_key, "2024-08-13")
#             print("Reschedule response:", reschedule_response)
#         else:
#             print(f"No API Key found for userId {user_id_value}")
