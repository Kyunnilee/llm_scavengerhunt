import requests
import os

def get_street_name(lat, lng, api_key):
    url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lng}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data['status'] == 'OK':
        # 从返回的结果中获取街道名称
        for result in data['results']:
            for component in result['address_components']:
                if 'route' in component['types']:  # 'route' 类型通常是街道名称
                    return component['long_name']
    return data

# 示例使用
lat, lng = 37.8754, -122.2588  # 例如：Bancroft Street, Berkeley, CA
api_key = os.environ.get('GOOGLE_API_KEY')
street_name = get_street_name(lat, lng, api_key)
print(street_name)
