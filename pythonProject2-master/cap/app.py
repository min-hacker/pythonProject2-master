import psycopg2
from flask import Flask, request, jsonify
import requests
import xml.etree.ElementTree as ET
import xmltodict
from operator import itemgetter
from haversine import haversine

app = Flask(__name__)

key = "a8o62hkYTQfh7mh2/1fYcwrkCY9nAkRHVl0tQEbIStbXP4VcsOSB7Sh4WqEFTTV6IRewyXe4Xhl729LG4c4OCg=="

@app.route('/')
def index():
    return "Server is running!"

@app.route('/get_congestion_info', methods=['POST'])
def get_congestion_info():
    try:
        input_route_number = request.json['route_number']
        print("요청된 노선 번호:", input_route_number)

        # 데이터베이스 연결
        conn = psycopg2.connect(host='192.168.0.2', dbname='postgres', user='postgres', password='root', port=5432)
        cur = conn.cursor()

        # 입력한 노선 번호에 대한 혼잡도 정보 가져오기
        cur.execute("SELECT bus_plate_number, route_number, congestion_level FROM bus_congestion_app.bus_congestion WHERE route_number = %s;", (input_route_number,))
        congestion_info = cur.fetchall()

        cur.close()
        conn.close()

        if not congestion_info:
            return jsonify({"error": "주어진 노선 번호에 대한 혼잡도 정보를 찾을 수 없습니다."}), 404

        # 응답 데이터 구성
        response_data = []
        for info in congestion_info:
            plate_number, route_number, congestion_level = info
            response_data.append({
                "bus_plate_number": plate_number,
                "route_number": route_number,
                "congestion_level": congestion_level
            })

        print("혼잡도 정보:", response_data)
        return jsonify(response_data), 200

    except KeyError:
        return jsonify({"error": "JSON 데이터에서 'route_number'를 찾을 수 없습니다."}), 400
    except psycopg2.DatabaseError as db_err:
        return jsonify({"error": f"데이터베이스 오류: {db_err}"}), 500


@app.route('/search_bus_stop', methods=['POST'])
def search_bus_stop():
    try:
        bus_stop_name = request.json['bus_stop_name']
        print("입력된 정류장 이름: ", bus_stop_name)
        node_info = get_node_info(bus_stop_name)
        print("검색된 노선 리스트: ", node_info)
        return jsonify(node_info)
    except KeyError:
        return "Error: 'bus_stop_name' not found in JSON data", 400

@app.route('/get_bus_arrival_info', methods=['POST'])
def get_bus_arrival_info():
    try:
        node_id = request.json['node_id']
        print("노드 ID: ", node_id)
        bus_arrival_info = fetch_bus_arrival_info(node_id)
        return jsonify(bus_arrival_info)
    except KeyError:
        return "Error: 'node_id' not found in JSON data", 400

def get_node_info(input_bus_stop_name):
    url_template = "http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnNoList?serviceKey={}&cityCode=22&nodeNm={}"
    url = url_template.format(key, input_bus_stop_name)
    response = requests.get(url)
    root = ET.fromstring(response.content)
    items = root.findall('.//item')
    node_info = []
    for item in items:
        node_info.append({
            'nodeid': item.find('nodeid').text,
            'nodenm': item.find('nodenm').text,
        })
    return node_info

def fetch_bus_arrival_info(node_id):
    url_template = "http://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList?serviceKey={}&cityCode=22&nodeId={}"
    url = url_template.format(key, node_id)
    response = requests.get(url)
    root = ET.fromstring(response.content)
    items = root.findall('.//item')
    bus_arrival_info = []
    for item in items:
        bus_arrival_info.append({
            'routeid': item.find('routeid').text,
            'routeno': item.find('routeno').text,
            'arrprevstationcnt': item.find('arrprevstationcnt').text,
            'arrtime': item.find('arrtime').text,
        })
    return bus_arrival_info

def get_route_id(routeno):
    url_template = "http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteNoList?serviceKey={}&cityCode=22&routeNo={}&numOfRows=300&pageNo=1&_type=xml"
    url = url_template.format(key, routeno)
    content = requests.get(url).content
    root = ET.fromstring(content)
    items = root.findall('.//item')
    if not items:
        return None
    else:
        for item in items:
            if item.find('routeno').text == routeno:
                return item.find('routeid').text


def get_nodenm(route_id):
    # 노선에 대한 정류소 정보 조회 API 호출
    url_stops = f"http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteAcctoThrghSttnList?serviceKey={key}&cityCode=22&routeId={route_id}&numOfRows=300&pageNo=1&_type=xml"
    url_vehicle = f"http://apis.data.go.kr/1613000/BusLcInfoInqireService/getRouteAcctoBusLcList?serviceKey={key}&cityCode=22&routeId={route_id}&numOfRows=100&pageNo=1&_type=xml"
    response_stops = requests.get(url_stops)
    response_vehicle = requests.get(url_vehicle)

    root_stops = ET.fromstring(response_stops.text)
    root_vehicle = ET.fromstring(response_vehicle.text)

    bus_stops = root_stops.findall('.//item')
    vehicle_info = root_vehicle.findall('.//item')

    if not bus_stops:
        return None
    else:
        # 정류소명과 차량번호 리스트 반환
        nodenms_and_vehicles = []
        for stop in bus_stops:
            nodenm = stop.find('nodenm').text
            vehicle_no = "" #차량 번호 없을 경우 빈값만들기
            for vehicle in vehicle_info:
                if vehicle.find('nodenm').text == nodenm:
                    vehicle_no = vehicle.find('vehicleno').text
                    break
            nodenms_and_vehicles.append({"nodenm": nodenm, "vehicleno": vehicle_no})
        return nodenms_and_vehicles


@app.route('/bus_route_info', methods=['POST'])
def bus_route_info():
    data = request.json
    bus_no = data.get('bus_no')
    print(f"프론트에서 요청한 버스 번호: {bus_no}")  # 프론트에서 전송한 버스 번호 출력
    if not bus_no:
        print("버스 번호를 입력하세요.")
        return jsonify({"error": "버스 번호를 입력하세요."}), 400

    url_template = "http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteNoList?serviceKey={}&cityCode=22&routeNo={}&numOfRows=300&pageNo=1&_type=xml"
    url = url_template.format(key, bus_no)
    response = requests.get(url)
    root = ET.fromstring(response.text)
    items = root.findall('.//item')

    if not items:
        print(f"{bus_no} 버스 번호에 대한 노선이 없습니다.")
        return jsonify({"error": "{} 버스 번호에 대한 노선이 없습니다.".format(bus_no)}), 404
    else:
        routes = []
        for item in items:
            route_id = item.find('routeid').text
            routes.append({
                "routeno": item.find('routeno').text,
                "routeid": route_id
            })
        print(f"반환된 노선 정보: {routes}")  # 반환된 노선 정보 출력
        return jsonify({"routes": routes}), 200


@app.route('/bus_stop_info', methods=['POST'])
def bus_stop_info():
    data = request.json
    route_id = data.get('route_id')
    nodenm_and_vehicle = get_nodenm(route_id)  # 노선에 대한 정류소 정보와 차량 정보 가져오기

    if not nodenm_and_vehicle:
        print(f"해당 노선에 대한 정류소 정보를 가져올 수 없습니다. (노선 ID: {route_id})")
        return jsonify({"error": "해당 노선에 대한 정류소 정보를 가져올 수 없습니다."}), 404

    print(f"정류소 및 차량 정보: 노선 ID - {route_id}, 정보  {nodenm_and_vehicle}")  # 정류소 및 차량 정보 출력
    return jsonify({"nodenm_and_vehicle": nodenm_and_vehicle}), 200


# 버스 스케줄링

bus_speed = 20

def fetch_bus_station_info(station_name):
    try:
        url = f"http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnNoList?serviceKey={key}&cityCode=22&nodeNm={station_name}&nodeNo=&numOfRows=1000&pageNo=1&_type=xml"
        content = requests.get(url).content
        data = xmltodict.parse(content)
        items = data['response']['body']['items']['item']
        if not isinstance(items, list):
            items = [items]
        return items
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def fetch_bus_route_info(station_id, station_name):
    try:
        url = f"http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnThrghRouteList?serviceKey={key}&cityCode=22&nodeid={station_id}&numOfRows=1000&pageNo=1&_type=xml"
        content = requests.get(url).content
        data = xmltodict.parse(content)
        items = data['response']['body']['items']['item']
        if not isinstance(items, list):
            items = [items]
        routes = []
        for item in items:
            bus_number = item.get('routeno', '')
            route_id = item.get('routeid')
            route_path = fetch_route_path(route_id)
            for path in route_path:
                if any(station == station_name for station, _, _, _ in path):
                    routes.append((bus_number, route_id, path))
                    break
        return routes
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

def fetch_route_path(route_id):
    try:
        url = f"http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteAcctoThrghSttnList?serviceKey={key}&cityCode=22&routeId={route_id}&numOfRows=1000&pageNo=1&_type=xml"
        content = requests.get(url).content
        data = xmltodict.parse(content)
        items = data['response']['body']['items']['item']
        if not isinstance(items, list):
            items = [items]
        route_paths = []
        current_route = []
        for item in items:
            station_name = item.get('nodenm')
            direction_code = item.get('updowncd')
            latitude = item.get('gpslati')
            longitude = item.get('gpslong')
            if not current_route or current_route[-1][1] != direction_code:
                if current_route:
                    route_paths.append(current_route)
                current_route = [(station_name, direction_code, latitude, longitude)]
            else:
                current_route.append((station_name, direction_code, latitude, longitude))
        if current_route:
            route_paths.append(current_route)
        return route_paths
    except Exception as e:
        print(f"Error occurred: {e}")
        return []

def find_intermediate_stations(start_routes, end_routes):
    common_stations = []
    for start_route in start_routes:
        for start_station, _, _, _ in start_route[2]:
            for end_route in end_routes:
                for end_station, _, _, _ in end_route[2]:
                    if start_station == end_station:
                        common_stations.append((start_station, start_route[0], end_route[0]))
    return common_stations

@app.route('/start_station_info', methods=['POST'])
def start_station_info():
    data = request.json
    print("Request Data (Start Station Info):", data)
    start_station_name = data.get('start_station')
    start_stations = fetch_bus_station_info(start_station_name)

    if start_stations:
        response_data = []
        for station in start_stations:
            station_info = {
                "station_name": station['nodenm'],
                "station_id": station['nodeid'],
            }
            response_data.append(station_info)
        print("Start Station Info (Response):", response_data)
        return jsonify(response_data)
    else:
        error_message = {"error": "Invalid input data"}
        print("Error (Start Station Info):", error_message)
        return jsonify(error_message), 400

@app.route('/end_station_info', methods=['POST'])
def end_station_info():
    data = request.json
    print("Request Data (End Station Info):", data)
    end_station_name = data.get('end_station')
    end_stations = fetch_bus_station_info(end_station_name)

    if end_stations:
        response_data = []
        for station in end_stations:
            station_info = {
                "station_name": station['nodenm'],
                "station_id": station['nodeid'],
            }
            response_data.append(station_info)
        print("End Station Info (Response):", response_data)
        return jsonify(response_data)
    else:
        error_message = {"error": "Invalid input data"}
        print("Error (End Station Info):", error_message)
        return jsonify(error_message), 400

@app.route('/route_info', methods=['POST'])
def route_info():
    data = request.json
    print("Request Data (Route Info):", data)
    start_station_name = data.get('start_station')
    end_station_name = data.get('end_station')

    start_stations = fetch_bus_station_info(start_station_name)
    end_stations = fetch_bus_station_info(end_station_name)

    if start_stations and end_stations:
        start_station = start_stations[0]
        end_station = end_stations[0]

        start_station_id = start_station['nodeid']
        start_station_name = start_station['nodenm']

        end_station_id = end_station['nodeid']
        end_station_name = end_station['nodenm']

        start_routes = fetch_bus_route_info(start_station_id, start_station_name)
        end_routes = fetch_bus_route_info(end_station_id, end_station_name)
        response_data = {}

        direct_routes = []
        seen_route_ids = set()
        for start_route in start_routes:
            for end_route in end_routes:
                if start_route[1] == end_route[1] and start_route[1] not in seen_route_ids:
                    direct_routes.append(start_route)
                    seen_route_ids.add(start_route[1])

        if direct_routes:
            direct_routes_info = []
            for route_id, _, route_path in direct_routes:
                route_info = {
                    "bus_number": route_id,
                    "start_station": start_station_name,
                    "end_station": end_station_name,
                    "total_distance": 0,
                    "total_time": 0
                }
                prev_coords = None
                for station, _, gpsx, gpsy in route_path:
                    if station == start_station_name:
                        prev_coords = (float(gpsx), float(gpsy))
                    if prev_coords:
                        current_coords = (float(gpsx), float(gpsy))
                        distance = haversine(prev_coords, current_coords)
                        route_info["total_distance"] += distance
                        time = distance / bus_speed * 60
                        route_info["total_time"] += time
                        prev_coords = current_coords
                    if station == end_station_name:
                        break
                route_info["total_distance"] = round(route_info["total_distance"], 1)
                total_minutes = int(route_info["total_time"])
                hours, minutes = divmod(total_minutes, 60)
                route_info["total_time"] = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"
                direct_routes_info.append(route_info)
            if direct_routes_info:
                response_data["direct_routes"] = direct_routes_info
        else:
            intermediate_stations = find_intermediate_stations(start_routes, end_routes)
            if intermediate_stations:
                intermediate_stations_info = []
                for station, start_bus, end_bus in intermediate_stations:
                    distance_start_to_intermediate = 0
                    distance_intermediate_to_end = 0
                    for start_route in start_routes:
                        if start_route[0] == start_bus:
                            start_route_path = start_route[2]
                            idx_start_station = next(
                                (idx for idx, (s, _, _, _) in enumerate(start_route_path) if s == start_station_name), None)
                            idx_intermediate_station = next(
                                (idx for idx, (s, _, _, _) in enumerate(start_route_path) if s == station), None)
                            if idx_intermediate_station is not None:
                                for i in range(idx_start_station, idx_intermediate_station):
                                    coord1 = (float(start_route_path[i][2]), float(start_route_path[i][3]))
                                    coord2 = (float(start_route_path[i + 1][2]), float(start_route_path[i + 1][3]))
                                    distance_start_to_intermediate += haversine(coord1, coord2)
                    for end_route in end_routes:
                        if end_route[0] == end_bus:
                            end_route_path = end_route[2]
                            idx_intermediate_station = next(
                                (idx for idx, (s, _, _, _) in enumerate(end_route_path) if s == station), None)
                            idx_end_station = next(
                                (idx for idx, (s, _, _, _) in enumerate(end_route_path) if s == end_station_name), None)
                            if idx_intermediate_station is not None and idx_end_station is not None:
                                for i in range(idx_intermediate_station, idx_end_station):
                                    coord1 = (float(end_route_path[i][2]), float(end_route_path[i][3]))
                                    coord2 = (float(end_route_path[i + 1][2]), float(end_route_path[i + 1][3]))
                                    distance_intermediate_to_end += haversine(coord1, coord2)
                    if distance_start_to_intermediate == 0 or distance_intermediate_to_end == 0:
                        continue
                    time_start_to_intermediate = distance_start_to_intermediate / bus_speed * 60
                    time_intermediate_to_end = distance_intermediate_to_end / bus_speed * 60
                    total_distance = round(distance_start_to_intermediate + distance_intermediate_to_end, 1)
                    total_time = time_start_to_intermediate + time_intermediate_to_end
                    total_minutes = int(total_time)
                    hours, minutes = divmod(total_minutes, 60)
                    total_time_str = f"{hours}시간 {minutes}분" if hours > 0 else f"{minutes}분"
                    intermediate_stations_info.append({
                        "station": station,
                        "start_bus": start_bus,
                        "end_bus": end_bus,
                        "distance_start_to_intermediate": round(distance_start_to_intermediate, 1),
                        "distance_intermediate_to_end": round(distance_intermediate_to_end, 1),
                        "total_distance": total_distance,
                        "total_time": total_time_str
                    })
                if intermediate_stations_info:
                    selected_routes = {}
                    grouped_routes = {}
                    for intermediate_station in intermediate_stations_info:
                        start_bus = intermediate_station["start_bus"]
                        if start_bus not in grouped_routes:
                            grouped_routes[start_bus] = []
                        grouped_routes[start_bus].append(intermediate_station)

                    for start_bus, routes in grouped_routes.items():
                        sorted_routes = sorted(routes, key=lambda x: (x["total_distance"], x["total_time"]))
                        selected_routes[start_bus] = sorted_routes[:3]

                    response_data["intermediate_stations"] = selected_routes

        print("Route Info (Response):", response_data)
        return jsonify(response_data)
    else:
        error_message = {"error": "Invalid input data"}
        print("Error (Route Info):", error_message)
        return jsonify(error_message), 400



if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000)



