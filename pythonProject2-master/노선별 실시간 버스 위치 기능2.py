import requests
import xmltodict
import time

def get_bus_no(routeno):
    url_template = "http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteNoList?serviceKey={}&cityCode=22&routeNo={}&numOfRows=300&pageNo=1&_type=xml"
    key = "a8o62hkYTQfh7mh2/1fYcwrkCY9nAkRHVl0tQEbIStbXP4VcsOSB7Sh4WqEFTTV6IRewyXe4Xhl729LG4c4OCg=="

    url = url_template.format(key, routeno)
    content = requests.get(url).content
    data_dict = xmltodict.parse(content)

    items = data_dict.get('response', {}).get('body', {}).get('items', {}).get('item', [])

    if not items:
        print(f"{routeno} 버스 번호에 대한 노선이 없습니다.")
    elif isinstance(items, list):
        print(f"{routeno} 버스 번호에 대해 여러 노선이 있습니다. 노선을 선택하세요:")
        for i, item in enumerate(items):
            print(f"{i + 1}. 노선 번호: {item['routeno']}")

        selected_index = int(input("원하는 노선에 해당하는 번호를 입력하세요: ")) - 1
        selected_route_id = items[selected_index]['routeid']
        get_bus_route_info(selected_route_id)
    else:
        route_id = items['routeid']
        get_bus_route_info(route_id)

def get_bus_route_info(route_id):
    url_stops = "http://apis.data.go.kr/1613000/BusRouteInfoInqireService/getRouteAcctoThrghSttnList?serviceKey={}&cityCode=22&routeId={}&numOfRows=300&pageNo=1&_type=xml"
    url_vehicle = "http://apis.data.go.kr/1613000/BusLcInfoInqireService/getRouteAcctoBusLcList?serviceKey={}&cityCode=22&routeId={}&numOfRows=100&pageNo=1&_type=xml"
    key = "a8o62hkYTQfh7mh2/1fYcwrkCY9nAkRHVl0tQEbIStbXP4VcsOSB7Sh4WqEFTTV6IRewyXe4Xhl729LG4c4OCg=="

    while True:
        content_stops = requests.get(url_stops.format(key, route_id)).content
        data_dict_stops = xmltodict.parse(content_stops)

        bus_stops = data_dict_stops.get('response', {}).get('body', {}).get('items', {}).get('item', [])

        if not bus_stops:
            print("해당 노선에 대한 정류장 정보가 없습니다.")
        else:
            bus_stops.sort(key=lambda x: int(x['nodeord']))
            # print(f"\n{route_id} 버스 노선의 실시간 차량 정보:")
            content_vehicle = requests.get(url_vehicle.format(key, route_id)).content
            data_dict_vehicle = xmltodict.parse(content_vehicle)
            vehicle_info = data_dict_vehicle.get('response', {}).get('body', {}).get('items', {}).get('item', [])

            if not vehicle_info:
                print("해당 노선에 대한 차량 정보가 없습니다.")
            else:
                for i, stop in enumerate(bus_stops):
                    vehicle_number = next((info.get('vehicleno', '') for info in vehicle_info if info.get('nodeid') == stop.get('nodeid')), '')
                    print( stop['nodenm'],vehicle_number)

        time.sleep(15)  # 15초 대기하기

if __name__ == "__main__":
    bus_no = input("버스 번호를 입력하세요: ")
    get_bus_no(bus_no)

