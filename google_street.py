import requests
import numpy as np
import json
import math
from tqdm import tqdm
import folium
import os
from util import visualize_with_folium, save_to_json
import matplotlib.pyplot as plt

# use `setx GOOGLE_API_KEY "your_api_key"` in cmd to set the environment variable first
API_KEY = os.environ.get('GOOGLE_API_KEY')


def generate_points(corner1, corner2, step):
    x_min = min(corner1[0], corner2[0])
    x_max = max(corner1[0], corner2[0])
    y_min = min(corner1[1], corner2[1])
    y_max = max(corner1[1], corner2[1])

    x_coords = np.arange(x_min, x_max + step, step)
    y_coords = np.arange(y_min, y_max + step, step)
    points = []
    for x in x_coords:
        for y in y_coords:
            points.append((x, y))
    
    return points

def get_center_point(corner1, corner2):
    lat = (corner1[0] + corner2[0]) / 2
    lon = (corner1[1] + corner2[1]) / 2
    return lat, lon

def nearest_roads(api_key, points):
    point_strings = ["{},{}".format(lat, lng) for lat, lng in points]
  
    batch_size = 100
    nearest_road_points = {}

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
            for r in roads:
                placeId = r['placeId']
                if placeId not in nearest_road_points:
                    nearest_road_points[placeId] = r
                    
        else:
            print(f"Error: {response.status_code}, {response.text}")
    
    return nearest_road_points

def L2(lat1, lon1, lat2, lon2):
    return math.sqrt((lat1 - lat2) ** 2 + (lon1 - lon2) ** 2)


def filter_overlapping_points(snapped_points, min_distance):
    filtered_points = {}
    distances = []
    
    for point in snapped_points.values():
        too_close = False
        for filtered_point in filtered_points.values():
            distance = L2(
                point['location']['latitude'], point['location']['longitude'],
                filtered_point['location']['latitude'], filtered_point['location']['longitude']
            )
            distances.append(distance) # //////////////////////////
            if distance < min_distance:
                too_close = True
                break
        
        if not too_close:
            filtered_points[point['placeId']] = point
            
    print(f"[filter_overlapping_points]Average distance: {sum(distances) / len(distances)}")
    print(f"[filter_overlapping_points]Median distance: {sorted(distances)[len(distances) // 2]}")
    print(f"[filter_overlapping_points]Number of points: {len(snapped_points)} -> {len(filtered_points)}")
    
    return filtered_points


def draw_points(nearest_road_points, edges, show_placeId=False,):
    
    if show_placeId:
        places = set()
        for road in nearest_road_points.items():
            places.add(road['placeId'])
        
        colors = plt.cm.rainbow(np.linspace(0, 1, len(places)))
        places_colors = {place: color for place, color in zip(places, colors)}
    for edge in edges:
        point1 = None
        point2 = None
        for road in nearest_road_points.items():
            if road['placeId'] == edge[0]:
                point1 = (road['location']['longitude'], road['location']['latitude'])
            elif road['placeId'] == edge[1]:
                point2 = (road['location']['longitude'], road['location']['latitude'])
                
            if point1 and point2:
                plt.plot([point1[0], point2[0]], [point1[1], point2[1]], c='b', linewidth=0.5)
                break
    for road in nearest_road_points.items():
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

def connect_points(points, max_distance=0.0003) -> set: # naive implementation
    points_with_edges = []
    edges = set() #1 
    for point in points.values():
        pos = (point['location']['latitude'], point['location']['longitude'])
        points_with_edges.append(point)
        neighbor_distances = []
        point['neighbors'] = []
        for neighbor in points.values():
            if neighbor['placeId'] == point['placeId']:
                continue
            neighbor_pos = (neighbor['location']['latitude'], neighbor['location']['longitude'])
            dis = L2(pos[0], pos[1], neighbor_pos[0], neighbor_pos[1])
            neighbor_distances.append((dis, neighbor['placeId']))
        neighbor_distances.sort(key=lambda x: x[0])
        ctn = 0
        for (dis, placeId) in neighbor_distances:
            if dis > max_distance or ctn > 3:
                break
            edge = (point['placeId'], placeId)
            edge = tuple(sorted(edge))
            point['neighbors'].append(placeId) # 2
            edges.add(edge)
            ctn += 1
    return edges, points

def convert_nodes_edges_to_vis(nodes, edges):
    nodes_vis = []
    edges_vis = []
    for node in nodes.values():
        nodes_vis.append({
            'id': node['placeId'],
            'name': node['placeId'],
            'latitude': node['location']['latitude'],
            'longitude': node['location']['longitude']
        })
    for edge in edges:
        edges_vis.append({
            'source': edge[0],
            'target': edge[1],
            'weight': 1
        })
    return nodes_vis, edges_vis

def generate_txt_file(nodes, edges, data_root=r'graph\our_graph'):
    nodes_list = []
    for node in nodes.values():
        for neighbor in node['neighbors']:
            nodes_list.append((node['placeId'], neighbor))
    with open(os.path.join(data_root, 'nodes.txt'), 'w') as f:
        for node in nodes_list:
            pos = (nodes[node[0]]['location']['latitude'], nodes[node[0]]['location']['longitude'])
            pos_face = (nodes[node[1]]['location']['latitude'], nodes[node[1]]['location']['longitude'])
            yaw_angle = math.atan2(pos_face[1] - pos[1], pos_face[0] - pos[0]) / math.pi * 180
            yaw_angle = int(yaw_angle)
            f.write(f"{node[0]},{yaw_angle},{pos[0]},{pos[1]}\n")
            
    with open(os.path.join(data_root, 'links.txt'), 'w') as f:
        for edge in edges:
            pos = (nodes[edge[0]]['location']['latitude'], nodes[edge[0]]['location']['longitude'])
            pos_face = (nodes[edge[1]]['location']['latitude'], nodes[edge[1]]['location']['longitude'])
            facing_angle = math.atan2(pos_face[1] - pos[1], pos_face[0] - pos[0]) / math.pi * 180
            facing_angle = int(facing_angle)
            f.write(f"{edge[0]},{facing_angle},{edge[1]}\n")
                
        
if __name__ == "__main__":

    # # provie opposite corners of the area
    # corner1 = (37.870582, -122.272911)
    # corner2 = (37.873900, -122.268541)
    # step = 1e-4

    # sample_points = generate_points(corner1, corner2, step)
    # print(f"Number of sample points: {len(sample_points)}")


    # points_metadata = {}
    # valid_points = []
    # for p in tqdm(sample_points):
    #     metadata = get_street_view_metadata(API_KEY, p[0], p[1])
    #     if metadata.get('status') == 'OK':
    #         points_metadata[metadata['pano_id']] = metadata
    #         location = metadata['location']
    #         valid_points.append((location['lat'], location['lng']))
            

    # nearest_road_points = nearest_roads(API_KEY, valid_points)
    # save_to_json(nearest_road_points, 'dataset\\test_data\\nearest_roads.json')

    # # with open('dataset\\test_data\\nearest_roads.json') as f:
    # #     nearest_road_points = json.load(f)


    # center_point = get_center_point(corner1, corner2)
    # filtered_points = filter_overlapping_points(nearest_road_points, 0.00015)
    # save_to_json(filtered_points, 'dataset\\test_data\\filtered_nearest_roads.json')
    
    
    with open('dataset/test_data/filtered_nearest_roads.json') as f:
        filtered_points = json.load(f)

    edges, points_with_neighbor = connect_points(filtered_points)
    nodes_vis, edges_vis = convert_nodes_edges_to_vis(filtered_points, edges)
    vis_result = visualize_with_folium(nodes_vis, edges_vis)
    vis_result.save('map.html') 
    generate_txt_file(points_with_neighbor, edges)
    
    # get_static_map_with_markers(API_KEY, center_point[0], center_point[1], filtered_points_positions, size="1800x1200", filename="dataset\\test_data\\map_with_markers_filtered.png")