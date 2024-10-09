import requests
import os

def get_street_view_image(lat, lon, api_key,  heading, save_path='street_view_image.jpg'):
    # Street View Static API endpoint
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    metadata_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    
    # Set the parameters for the API request
    params = {
        "size": "640x640",  # Output image size (width x height)
        "location": f"{lat},{lon}",  # Latitude and Longitude
        "key": api_key,  # Your API key
        "fov": 90,  # Field of view (default is 90)
        "heading": heading,  # Heading angle (default is 0)
        "pitch": 0  # Pitch angle (default is 0)
    }
    
    # Send the request to the API
    response = requests.get(base_url, params=params) 
    meta_response = requests.get(metadata_url, params= params)
    
    # Check if the request was successful
    if meta_response.status_code == 200:
        metadata = meta_response.json()
        print("Metadata retrieved:", metadata)
        if metadata["status"] == "OK":
            print("Street View imagery is available at this location.")
        else:
            print("Street View imagery is NOT available.")
            return  # If imagery is not available, return without saving the image.
    else:
        print(f"Failed to retrieve metadata. Status code: {meta_response.status_code}, Reason: {meta_response.reason}")
        return

    # If metadata is OK, proceed to get the image
    response = requests.get(base_url, params=params)
    
    # Check if the image request was successful
    if response.status_code == 200:
        # Save the image
        with open(save_path, 'wb') as f:
            f.write(response.content)
        print(f"Street View image saved to {save_path}")
    else:
        print(f"Failed to retrieve image. Status code: {response.status_code}, Reason: {response.reason}")

# Example usage
if __name__ == "__main__":
    latitude = 37.869545  # Replace with your desired latitude
    longitude = -122.2527  # Replace with your desired longitude
    api_key = "AIzaSyDv1zr5JJYKjv3MGIeYNEe5n1nP4gv2SSY"  # Replace with your Google Maps API key
    headings = [0, 45 ,90, 135, 180, 225, 270, 315] # 8 inputs for llm
    image_dir = "streetview_image"

    for heading in headings:
        save_path = os.path.join(image_dir, f"view_{heading}.jpg")
    # Call the function to get the street view image
        get_street_view_image(latitude, longitude, api_key, heading, save_path)
