import googlemaps
from typing import Dict

def get_info(lat: float, lng: float, info_type: str) -> Dict:
    """
    Get specific information about a location.
    
    Args:
        lat: Latitude
        lng: Longitude
        info_type: Type of information wanted ('street' or 'neighbors' or 'landmarks' or 'attractions')
    
    Returns:
        Dictionary containing requested information
    """
    try:
        gmaps = googlemaps.Client(key="AIzaSyC04gYkv5OP4fqaKx6etfcdd6oPGELNmi8")
        
        if info_type == 'street':
            result = gmaps.reverse_geocode((lat, lng))
            if result:
                # 遍历所有地址组件找到街道名
                for component in result[0]['address_components']:
                    if 'route' in component['types']:
                        return {"street": component['long_name']}
                # 如果没找到 route 类型，返回子地址
                for component in result[0]['address_components']:
                    if 'sublocality' in component['types']:
                        return {"street": component['long_name']}
            return {"street": "Unknown street"}
            
        elif info_type == 'neighbors':
            result = gmaps.places_nearby(
                location=(lat, lng),
                radius=20,  # 20米内
                type='premise'
            )
            
            if not result.get('results'):
                return {"neighbors": "No buildings found"}
            
            nearest = result['results'][0]
            return {"neighbors": {
                "name": nearest['name'],
                "address": nearest.get('vicinity', 'No address'),
                "type": nearest.get('types', ['unknown'])[0]
            }}
            
        elif info_type == 'landmarks':
            result = gmaps.places_nearby(
                location=(lat, lng),
                radius=50,  # 50米内
                type='point_of_interest'
            )
            
            if not result.get('results'):
                return {"landmarks": "No landmarks found"}
                
            landmarks = []
            for place in result['results'][:3]:  # 只取前3个
                landmarks.append({
                    "name": place['name'],
                    "address": place.get('vicinity', 'No address')
                })
            return {"landmarks": landmarks}
            
        elif info_type == 'attractions':
            result = gmaps.places_nearby(
                location=(lat, lng),
                radius=50,  # 50米内
                type='tourist_attraction'
            )
            
            if not result.get('results'):
                return {"attractions": "No attractions found"}
                
            attractions = []
            for place in result['results'][:3]:  # 只取前3个
                attractions.append({
                    "name": place['name'],
                    "address": place.get('vicinity', 'No address')
                })
            return {"attractions": attractions}
            
        else:
            return {"error": "Unknown info_type"}
            
    except Exception as e:
        return {"error": f"Failed to get information: {str(e)}"}

def main():
    # 测试地点：纽约帝国大厦
    lat, lng = 40.7484, -73.9857
    
    print("\n=== 街道名称 ===")
    print(get_info(lat, lng, 'street'))
    
    print("\n=== 相邻建筑 ===")
    print(get_info(lat, lng, 'neighbors'))
    
    print("\n=== 附近地标 ===")
    print(get_info(lat, lng, 'landmarks'))
    
    print("\n=== 附近景点 ===")
    print(get_info(lat, lng, 'attractions'))
    
    # 测试其他位置
    test_coords = [
        (40.7516, -73.9877),  # 另一个纽约位置
        (37.7749, -122.4194)  # 旧金山
    ]
    
    for lat, lng in test_coords:
        print(f"\n=== 测试坐标: {lat}, {lng} ===")
        print("街道:", get_info(lat, lng, 'street'))
        print("相邻建筑:", get_info(lat, lng, 'neighbors'))

if __name__ == "__main__":
    main()