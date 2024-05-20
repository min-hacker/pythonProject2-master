import requests
import xmltodict
import math
import time
from geopy.distance import geodesic
API_KEY = "a8o62hkYTQfh7mh2/1fYcwrkCY9nAkRHVl0tQEbIStbXP4VcsOSB7Sh4WqEFTTV6IRewyXe4Xhl729LG4c4OCg=="
def get_bus_station_info(node_nm):
    try:
        url_template = f"http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnNoList?serviceKey={API_KEY}&cityCode=22&nodeNm={node_nm}&nodeNo=&numOfRows=1000&pageNo=1&_type=xml"
        content = requests.get(url_template).content
        data_dict = xmltodict.parse(content)

        items = data_dict['response']['body']['items']['item']
        if not isinstance(items, list):
            items = [items]

        print("일치하는 정류소 목록:")
        for i, item in enumerate(items, start=1):
            print(f"{i}. 정류소명: {item.get('nodenm', '')}")

        while True:
            try:
                choice = int(input("선택할 정류소의 번호를 입력하세요: "))
                if 1 <= choice <= len(items):
                    selected_node = items[choice - 1]
                    break
                else:
                    print("유효한 번호를 입력하세요.")
            except ValueError:
                print("숫자를 입력하세요.")
        return selected_node
    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return None

def get_bus_route_info(node_id, end_node_id=None):
    try:
        url_template = f"http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnThrghRouteList?serviceKey={API_KEY}&cityCode=22&nodeid={node_id}&numOfRows=100&pageNo=1&_type=xml"
        content = requests.get(url_template).content
        data_dict = xmltodict.parse(content)

        items = data_dict['response']['body']['items']['item']
        if not isinstance(items, list):
            items = [items]

        route_info = {}
        for i, item in enumerate(items, start=1):
            routeno = item.get('routeno', '')
            route_id = item.get('routeid', '')
            route_path = get_route_path(route_id, node_id, end_node_id)

            if route_path:
                route_info[routeno] = route_path
        return route_info

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return {}

def get_route_path(route_id, selected_node_id, end_node_id=None):
    try:
        url_template = f"http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteAcctoThrghSttnList?serviceKey={API_KEY}&cityCode=22&routeId={route_id}&numOfRows=1000&pageNo=1&_type=xml"
        content = requests.get(url_template).content
        data_dict = xmltodict.parse(content)

        items = data_dict['response']['body']['items']['item']
        if not isinstance(items, list):
            items = [items]

        route_path = []
        is_within_interval = False
        for i, item in enumerate(items, start=1):
            nodenm = item.get('nodenm', '')
            node_id = item.get('nodeid', '')
            node_lat = item.get('gpslati', '')
            node_lon = item.get('gpslong', '')

            if node_id == selected_node_id:
                is_within_interval = True

            if is_within_interval:
                route_path.append((nodenm, (float(node_lat), float(node_lon))))

            if end_node_id and node_id == end_node_id:
                is_within_interval = False
                break
        return route_path

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return []

def calculate_distance(coords1, coords2):
    return geodesic(coords1, coords2).kilometers

def calculate_travel_time(distance):
    average_speed_kmh = 17.1  #버스 평균 속력
    travel_hours = distance / average_speed_kmh
    travel_hours_int = int(travel_hours)
    travel_minutes = (travel_hours - travel_hours_int) * 60
    return travel_hours_int, travel_minutes

def main():
    start_node_nm = input("출발 정류소명을 입력하세요: ")
    selected_node_1 = get_bus_station_info(start_node_nm)

    end_node_nm = input("도착 정류소명을 입력하세요: ")
    selected_node_2 = get_bus_station_info(end_node_nm) if end_node_nm else None

    if selected_node_1 and (selected_node_2 or not end_node_nm):
        route_info_1 = get_bus_route_info(selected_node_1['nodeid'], selected_node_2['nodeid'] if selected_node_2 else None)

        if selected_node_2:
            filtered_route_info_1 = {k: v for k, v in route_info_1.items() if selected_node_2['nodenm'] in [node[0] for node in v]}

            if filtered_route_info_1:
                print(f"\n{selected_node_1['nodenm']}을 포함하고 {selected_node_2['nodenm']}을 포함하는 노선의 경로:")# 나중에 삭제할 코드
                for routeno, path in filtered_route_info_1.items():
                    print(f"{routeno} 노선 구간:")
                    total_distance = 0
                    for i in range(len(path) - 1):
                        start_node, start_coords = path[i]
                        end_node, end_coords = path[i + 1]
                        distance = calculate_distance(start_coords, end_coords)
                        travel_hours, travel_minutes = calculate_travel_time(distance)
                        # print(f"{start_node}에서 {end_node}까지 거리: {distance:.2f} km, 소요 시간: {travel_hours} 시간 {travel_minutes:.0f} 분")
                        total_distance += distance
                    print(f"총 이동 거리: {total_distance:.2f} km")
                    total_travel_hours, total_travel_minutes = calculate_travel_time(total_distance)
                    print(f"총 소요 시간: {total_travel_hours} 시간 {total_travel_minutes:.0f} 분")
                    print()
if __name__ == "__main__":
    main()