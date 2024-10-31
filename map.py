import os
import requests

def get_street_view_image_url(lat, lon, api_key, heading):
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    metadata_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    
    meta_params = {
        "location": f"{lat},{lon}",
        "key": api_key,
        "source": "outdoor"
    }
    
    image_params = {
        "size": "600x300",  
        "location": f"{lat},{lon}",  
        "key": api_key, 
        "fov": 90,  
        "heading": heading,  
        "pitch": 0,
        "source": "outdoor"
    }

    meta_response = requests.get(metadata_url, params=meta_params)

    if meta_response.status_code == 200:
        metadata = meta_response.json()
        if metadata.get('status') == 'OK':
            image_url = f"{base_url}?size=640x640&location={lat},{lon}&key={api_key}&fov=90&heading={heading}&pitch=0"
            print(f"Street View image URL for heading {heading}: {image_url}")
            return image_url
        else:
            print(f"Street View imagery is NOT available for heading {heading}.")
            return None
    else:
        print(f"Failed to retrieve metadata. Status code: {meta_response.status_code}, Reason: {meta_response.reason}")
        return None

# Example usage
if __name__ == "__main__":
    latitude = 37.869545  
    longitude = -122.2527 
    api_key=os.get_env('GOOGLE_MAP_API_KEY')
    headings = [0, 45, 90, 135, 180, 225, 270, 315]  
    for heading in headings:
        get_street_view_image_url(latitude, longitude, api_key, heading)