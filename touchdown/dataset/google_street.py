import requests
import numpy as np
import json
import math
from tqdm import tqdm

API_KEY = 'AIzaSyBZdkQTQnrPBtfpmlPh5-Ngs5vdMO2Xy80'

def generate_points(corner1, corner2, corner3, corner4, step):
    x_min = min(corner1[0], corner2[0], corner3[0], corner4[0])
    x_max = max(corner1[0], corner2[0], corner3[0], corner4[0])
    y_min = min(corner1[1], corner2[1], corner3[1], corner4[1])
    y_max = max(corner1[1], corner2[1], corner3[1], corner4[1])

    x_coords = np.arange(x_min, x_max + step, step)
    y_coords = np.arange(y_min, y_max + step, step)
    points = []
    for x in x_coords:
        for y in y_coords:
            points.append((x, y))
    
    return points

def get_center_point(corner1, corner2, corner3, corner4):
    lat = (corner1[0] + corner2[0] + corner3[0] + corner4[0]) / 4
    lon = (corner1[1] + corner2[1] + corner3[1] + corner4[1]) / 4
    return lat, lon

def nearest_roads(api_key, points):
    point_strings = ["{},{}".format(lat, lng) for lat, lng in points]
  
    batch_size = 100
    nearest_road_points = []

    for i in tqdm(range(0, len(point_strings), batch_size)):
        
        if i + batch_size > len(point_strings):
            batch_size = len(point_strings) - i
            
        batch = point_strings[i:i+batch_size]
        locations = "|".join(batch)
        
        url = f"https://roads.googleapis.com/v1/nearestRoads?points={locations}&key={api_key}"
        
        response = requests.get(url)
        if response.status_code == 200:
            road_data = response.json()
            # for road in road_data.get('snappedPoints', []):
            roads = road_data.get('snappedPoints', [])
            # nearest_road_points.append(roads)
            nearest_road_points.extend(roads)
        else:
            print(f"Error: {response.status_code}, {response.text}")
    
    return nearest_road_points

def L2(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


def filter_overlapping_points(snapped_points, min_distance):
    filtered_points = []
    distances = []
    
    for point in snapped_points:
        too_close = False
        for filtered_point in filtered_points:
            distance = L2(
                point['location']['latitude'], point['location']['longitude'],
                filtered_point['location']['latitude'], filtered_point['location']['longitude']
            )
            distances.append(distance) # //////////////////////////
            if distance < min_distance:
                too_close = True
                break
        
        if not too_close:
            filtered_points.append(point)
            
    print(f"Average distance: {sum(distances) / len(distances)}")
    print(f"Median distance: {sorted(distances)[len(distances) // 2]}")
    print(f"Number of points: {len(snapped_points)} -> {len(filtered_points)}")
    
    return filtered_points

def save_to_json(data, filename='nearest_roads.json'):
    with open(filename, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    print(f"Data saved to {filename}")


def draw_points(nearest_road_points, show_placeId=False):
    import matplotlib.pyplot as plt
    
    if show_placeId:
        places = set()
        for road in nearest_road_points:
            places.add(road['placeId'])
        
        colors = plt.cm.rainbow(np.linspace(0, 1, len(places)))
        places_colors = {place: color for place, color in zip(places, colors)}
    for road in nearest_road_points:
        lat = road['location']['latitude']
        lng = road['location']['longitude']
        if show_placeId:
            plt.scatter(lng, lat, c=places_colors[road['placeId']], s=2)
        else:
            plt.scatter(lng, lat, c='r', s=2)
    plt.show() 


def get_street_view(api_key, lat, lon, heading=0, pitch=20, fov=120, size="600x300", file_name="street_view_image.jpg"):
    base_url = "https://maps.googleapis.com/maps/api/streetview"
    params = {
        "location": f"{lat},{lon}",
        "size": size,
        "heading": heading,
        "pitch": pitch,
        "fov": fov,
        "key": api_key,
        "source": "outdoor"
    }

    response = requests.get(base_url, params=params, stream=True)
    
    if response.status_code == 200:
        with open(file_name, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Street View image saved as {file_name}")
        return file_name
    else:
        return f"Error: Unable to retrieve street view image (Status code: {response.status_code})"


def get_street_view_metadata(api_key, lat, lon):
    base_url = "https://maps.googleapis.com/maps/api/streetview/metadata"
    params = {
        "location": f"{lat},{lon}",
        "key": api_key,
        "source": "outdoor"
    }

    response = requests.get(base_url, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error: Unable to retrieve street view metadata (Status code: {response.status_code})"
    
def get_static_map_with_markers(api_key, center_lat, center_lon, coordinates_list, zoom=14, size="600x400", maptype="roadmap", filename="map_with_markers.png"):
    base_url = "https://maps.googleapis.com/maps/api/staticmap"
    markers = "size:tiny|color:red|label:P|"
    for lat, lon in coordinates_list:
        markers += f"{lat},{lon}|"
    markers = markers.strip('|')
    
    params = {
        # "center": f"{center_lat},{center_lon}",
        # "zoom": zoom,
        "size": size,
        "maptype": maptype,
        "markers": markers,
        "key": api_key
    }
    

    response = requests.get(base_url, params=params, stream=True)
    
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Map with markers saved as {filename}")
        return filename
    else:
        return f"Error: Unable to retrieve map (Status code: {response.status_code})"


if __name__ == "__main__":

    corner1 = (37.873349, -122.273222)
    corner2 = (37.870582, -122.272911)
    corner3 = (37.871121, -122.268245)
    corner4 = (37.873900, -122.268541)
    step = 1e-4

    sample_points = generate_points(corner1, corner2, corner3, corner4, step)
    print(f"Number of sample points: {len(sample_points)}")


    points_metadata = {}
    valid_points = []
    for p in tqdm(sample_points):
        metadata = get_street_view_metadata(API_KEY, p[0], p[1])
        if metadata.get('status') == 'OK':
            points_metadata[metadata['pano_id']] = metadata
            location = metadata['location']
            valid_points.append((location['lat'], location['lng']))
            

    nearest_road_points = nearest_roads(API_KEY, valid_points)

    save_to_json(nearest_road_points, 'dataset\\test_data\\nearest_roads.json')
    # draw_points(nearest_road_points)

    # with open('dataset\\test_data\\nearest_roads.json') as f:
    #     nearest_road_points = json.load(f)

    nearest_road_points_positions = [(road['location']['latitude'], road['location']['longitude']) for road in nearest_road_points]
    center_point = get_center_point(corner1, corner2, corner3, corner4)
    filtered_points = filter_overlapping_points(nearest_road_points, 0.00015)
    save_to_json(filtered_points, 'dataset\\test_data\\filtered_nearest_roads.json')
    filtered_points_positions = [(road['location']['latitude'], road['location']['longitude']) for road in filtered_points]
    get_static_map_with_markers(API_KEY, center_point[0], center_point[1], filtered_points_positions, size="1800x1200", filename="dataset\\test_data\\map_with_markers_filtered.png")