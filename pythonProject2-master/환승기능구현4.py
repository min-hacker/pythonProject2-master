import requests
import xmltodict
from haversine import haversine

API_KEY = "a8o62hkYTQfh7mh2/1fYcwrkCY9nAkRHVl0tQEbIStbXP4VcsOSB7Sh4WqEFTTV6IRewyXe4Xhl729LG4c4OCg=="
BUS_SPEED = 17.1
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
                    return selected_node
                else:
                    print("유효한 번호를 입력하세요.")
            except ValueError:
                print("숫자를 입력하세요.")

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return None


def get_bus_route_info(node_id, node_nm):
    try:
        url_template = f"http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnThrghRouteList?serviceKey={API_KEY}&cityCode=22&nodeid={node_id}&numOfRows=1000&pageNo=1&_type=xml"
        content = requests.get(url_template).content
        data_dict = xmltodict.parse(content)
        items = data_dict['response']['body']['items']['item']

        if not isinstance(items, list):
            items = [items]

        routes = []
        for item in items:
            routeno = item.get('routeno', '')
            route_id = item.get('routeid')
            route_path = get_route_path(route_id)
            for path in route_path:
                if any(station == node_nm for station, _, _, _ in path):
                    routes.append((routeno, path))
                    break

        return routes

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return []


def get_route_path(route_id):
    try:
        url_template = f"http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteAcctoThrghSttnList?serviceKey={API_KEY}&cityCode=22&routeId={route_id}&numOfRows=1000&pageNo=1&_type=xml"
        content = requests.get(url_template).content
        data_dict = xmltodict.parse(content)

        items = data_dict['response']['body']['items']['item']
        if not isinstance(items, list):
            items = [items]

        route_paths = []
        current_route = []
        for item in items:
            nodenm = item.get('nodenm')
            updowncd = item.get('updowncd')
            gpslati = item.get('gpslati')
            gpslong = item.get('gpslong')
            if not current_route or current_route[-1][1] != updowncd:
                if current_route:
                    route_paths.append(current_route)
                current_route = [(nodenm, updowncd, gpslati, gpslong)]
            else:
                current_route.append((nodenm, updowncd, gpslati, gpslong))

        # Add the last route
        if current_route:
            route_paths.append(current_route)

        return route_paths

    except Exception as e:
        print(f"오류가 발생했습니다: {e}")
        return []


def find_common_stations(departure_routes, destination_routes):
    common_stations = []

    for departure_route in departure_routes:
        for departure_station, _, _, _ in departure_route[1]:
            for destination_route in destination_routes:
                for destination_station, _, _, _ in destination_route[1]:
                    if departure_station == destination_station:
                        common_stations.append((departure_station, departure_route[0], destination_route[0]))

    return common_stations


if __name__ == "__main__":
    departure_node_nm = input("출발 정류장을 입력하세요: ")
    departure_node = get_bus_station_info(departure_node_nm)
    if departure_node:
        departure_coords = (float(departure_node.get('gpsx', 0.0)), float(departure_node.get('gpsy', 0.0)))
        departure_node_id = departure_node['nodeid']
        departure_node_nm = departure_node['nodenm']

        # Get routes for departure
        departure_routes = get_bus_route_info(departure_node_id, departure_node_nm)

        # Print routes for departure
        # print(f"{departure_node_nm}에서의 노선 경로:")
        # for route in departure_routes:
        #     print(f"노선번호: {route[0]}")
        #     print(f"노선경로: {' -> '.join([f'{s}({d})' for s, _, _, d in route[1]])}")
        # print()

    destination_node_nm = input("도착 정류장을 입력하세요: ")
    destination_node = get_bus_station_info(destination_node_nm)
    if destination_node:
        destination_coords = (float(destination_node.get('gpsx', 0.0)), float(destination_node.get('gpsy', 0.0)))
        destination_node_id = destination_node['nodeid']
        destination_node_nm = destination_node['nodenm']

        # Get routes for destination
        destination_routes = get_bus_route_info(destination_node_id, destination_node_nm)

        # Print the route from departure to destination
        # print(f"{destination_node_nm}까지의 노선 경로:")
        # for destination_route in destination_routes:
        #     for idx, (station, _, _, _) in enumerate(destination_route[1]):
        #         if station == destination_node_nm:
        #             print(f"노선번호: {destination_route[0]}")
        #             print(f"노선경로: {' -> '.join([f'{s}({d})' for s, _, _, d in destination_route[1][:idx+1]])}")
        #             break
        print()

        # Find common stations
        common_stations = find_common_stations(departure_routes, destination_routes)

        # Print common stations
        if common_stations:

            for station, departure_bus, destination_bus in common_stations:
                print()
                print(f"{station} 공통정류장:")
                print(f"출발 버스 번호: {departure_bus}")
                print(f"도착 버스 번호: {destination_bus}")

                # Calculate distance from departure to common station
                distance_departure_to_common = 0
                for departure_route in departure_routes:
                    if departure_route[0] == departure_bus:
                        departure_route_path = departure_route[1]
                        idx_departure_station = next(
                            (idx for idx, (s, _, _, _) in enumerate(departure_route_path) if s == departure_node_nm), None)
                        idx_common_station = next(
                            (idx for idx, (s, _, _, _) in enumerate(departure_route_path) if s == station), None)
                        if idx_common_station is not None:
                            for i in range(idx_departure_station, idx_common_station):
                                coord1 = (float(departure_route_path[i][2]), float(departure_route_path[i][3]))
                                coord2 = (float(departure_route_path[i + 1][2]), float(departure_route_path[i + 1][3]))
                                distance_departure_to_common += haversine(coord1, coord2)

                print(f"출발 정류장에서 공통 정류소까지의 거리: {distance_departure_to_common:.1f} km")

                # Calculate distance from common station to destination
                distance_common_to_destination = 0
                for destination_route in destination_routes:
                    if destination_route[0] == destination_bus:
                        destination_route_path = destination_route[1]
                        idx_common_station = next(
                            (idx for idx, (s, _, _, _) in enumerate(destination_route_path) if s == station), None)
                        idx_destination_station = next(
                            (idx for idx, (s, _, _, _) in enumerate(destination_route_path) if s == destination_node_nm), None)
                        if idx_destination_station is not None:
                            for i in range(idx_common_station, idx_destination_station):
                                coord1 = (float(destination_route_path[i][2]), float(destination_route_path[i][3]))
                                coord2 = (float(destination_route_path[i + 1][2]), float(destination_route_path[i + 1][3]))
                                distance_common_to_destination += haversine(coord1, coord2)

                print(f"공통 정류소에서 도착 정류장까지의 거리: {distance_common_to_destination:.1f} km")

                # Calculate total distance
                total_distance = distance_departure_to_common + distance_common_to_destination
                print(f"총 거리: {total_distance:.1f} km")

                # Calculate estimated travel time in minutes
                travel_time_minutes = (total_distance / BUS_SPEED) * 60
                print(f"예상 소요 시간: {travel_time_minutes:.1f} 분")
