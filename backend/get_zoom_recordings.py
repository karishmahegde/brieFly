import requests

#Fetch recrodings from the user's account
def fetch_recordings(access_token):
    headers = {
        "Authorization": f"Bearer {access_token.strip()}"
    }

    url = "https://api.zoom.us/v2/users/me/recordings"
    
    recordings = []
    page_token = None #To handle pagination. The URL returns a page_token if there are more results are available on the next page. When returned, we will fetch the results till this token is returned empty

    while True:
        params = {} #Fetching the page token param to fetch recodings from multiple pages, when available
        if page_token:
            params["page_token"] = page_token
            
        response = requests.get(url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            for meeting in data.get("meetings", []):
                recordings.append({
                    "topic":meeting.get("topic"), 
                    "download_url": meeting.get("download_url"), 
                    "start_time":meeting.get("start_time")
                })
            page_token = data.get("next_page_token")
            if not page_token:
                break   #No more pages
        
        else:
            print("Failed to fetch recordings:")
            print("Status code:", response.status_code)
            print("Response:", response.text)
            break
        
    return recordings