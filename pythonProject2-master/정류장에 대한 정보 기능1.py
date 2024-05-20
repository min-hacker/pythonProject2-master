import random
import requests
import xmltodict
import time
import os
key = "a8o62hkYTQfh7mh2/1fYcwrkCY9nAkRHVl0tQEbIStbXP4VcsOSB7Sh4WqEFTTV6IRewyXe4Xhl729LG4c4OCg=="

# def clear_console():
#     # 콘솔 클리어
#     os.system('cls' if os.name == 'nt' else 'clear')

def get_node_id(node_nm):
    # OpenAPI URL 템플릿
    url_template = "http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnNoList?serviceKey={}&cityCode=22&nodeNm={}"

    # API 요청을 위한 URL 생성
    url = url_template.format(key, node_nm)

    # API에 요청하여 XML 데이터 가져오기
    response = requests.get(url)
    content = response.content

    # XML 데이터 파싱
    data_dict = xmltodict.parse(content)

    # 파싱된 데이터에서 필요한 정보 추출
    try:
        items = data_dict['response']['body']['items']['item']
    except KeyError:
        print("해당 정류소명에 대한 정보가 없습니다.")
        return None

    # items가 리스트가 아닐 경우 리스트로 변환
    if not isinstance(items, list):
        items = [items]

    # 중복된 정류소명이 있을 때 선택할 수 있는 옵션 제공
    print("중복된 정류소명이 있습니다. 아래에서 선택해주세요:")
    for num, item in enumerate(items, start=1):
        print(f"{num}. 정류장명: {item['nodenm']}")

    # 사용자에게 선택 받기
    selected_index = int(input("원하는 정류장의 번호를 선택하세요: ")) - 1
    selected_item = items[selected_index]

    # 선택한 정류장의 NodeID 반환
    return selected_item['nodeid']

# def seconds_to_minutes_and_seconds(seconds):
#     minutes = seconds // 60
#     remaining_seconds = seconds % 60
#     return minutes, remaining_seconds

def get_bus_route_info(node_nm):
    while True:
        # 콘솔 클리어
        # clear_console()

        # 정류소명에 대한 NodeID 가져오기
        node_id = get_node_id(node_nm)

        if node_id is None:
            return

        # OpenAPI URL 템플릿
        url_template = "http://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList?serviceKey={}&cityCode=22&nodeId={}&numOfRows=10&pageNo=1&_type=xml"

        # API 요청을 위한 URL 생성
        url = url_template.format(key, node_id)

        # API에 요청하여 XML 데이터 가져오기
        response = requests.get(url)
        content = response.content

        # XML 데이터 파싱
        data_dict = xmltodict.parse(content)

        # 파싱된 데이터에서 필요한 정보 추출
        try:
            items = data_dict['response']['body']['items']['item']
        except KeyError:
            print("해당 정류소에 대한 정보가 없습니다.")
            return

        # items가 리스트가 아닐 경우 리스트로 변환
        if not isinstance(items, list):
            items = [items]

        # 도착 예정 시간을 기준으로 오름차순으로 정렬
        sorted_items = sorted(items, key=lambda x: int(x.get('arrtime', 0)))

        # 노선 정보 출력
        for item in sorted_items:
            # 도착 예정 시간을 분과 초로 변환
            arrival_seconds = int(item.get('arrtime', 0))
            arrival_minutes, arrival_seconds = divmod(arrival_seconds, 60)

            # 혼잡도 랜덤으로 선택
            congestion_level = random.choice(["쾌적", "보통", "혼잡", "매우혼잡"])

            # 해당 노선에 대한 정보 출력
            print(
                f"노선번호: {item['routeno']}, 남은 정류장 수: {item.get('arrprevstationcnt', '정보 없음')}, 도착 예정 시간: {arrival_minutes}분 {arrival_seconds}초, 혼잡도: {congestion_level}")

            # 10초마다 리프레시
        time.sleep(10)

        # 10초마다 리프레시
        time.sleep(10)

# 정류장 정보 가져오기
bus_stop_name = input("정류장명을 입력하세요: ")
get_bus_route_info(bus_stop_name)

# def get_bus_station_info(node_nm):#정률장명
#     url_template = "http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnNoList?serviceKey={}&cityCode=22&nodeNm={}&nodeNo=&numOfRows=100&pageNo=1&_type=xml"
#     key = "a8o62hkYTQfh7mh2/1fYcwrkCY9nAkRHVl0tQEbIStbXP4VcsOSB7Sh4WqEFTTV6IRewyXe4Xhl729LG4c4OCg=="
#     url = url_template.format(key, node_nm)
#     content = requests.get(url).content
#     data_dict = xmltodict.parse(content)
#
#     items = data_dict['response']['body']['items']['item']
#
#     if not isinstance(items, list):
#         items = [items]
#
#     print("정류소 정보:")
#     for i, item in enumerate(items, start=1):
#         print(f"{i}. 정류소명: {item['nodenm']}")
#
#     return items
#
# def get_bus_station_info(node_nm):
#     url_template = "http://apis.data.go.kr/1613000/BusSttnInfoInqireService/getSttnNoList?serviceKey={}&cityCode=22&nodeNm={}&nodeNo=&numOfRows=100&pageNo=1&_type=xml"
#
#     url = url_template.format(key, node_nm)
#     content = requests.get(url).content
#     data_dict = xmltodict.parse(content)
#
#     items = data_dict['response']['body']['items']['item']
#
#     if not isinstance(items, list):
#         items = [items]
#
#     print("정류소 정보:")
#     for i, item in enumerate(items, start=1):
#         print(f"{i}. 정류소명: {item['nodenm']}")
#
#     return items
#
# def get_bus_station_gas_info(node_id):
#     url_template = "http://apis.data.go.kr/1613000/ArvlInfoInqireService/getSttnAcctoArvlPrearngeInfoList?serviceKey={}&cityCode=22&nodeId={}&numOfRows=100&pageNo=1&_type=xml"
#
#     url = url_template.format(key, node_id)
#     content = requests.get(url).content
#     data_dict = xmltodict.parse(content)
#
#     items = data_dict['response']['body']['items']['item']
#
#     if not isinstance(items, list):
#         items = [items]
#
#     print("\n노선 정보:")
#     for i, item in enumerate(items, start=1):
#         print(f"{i}. 노선번호: {item['routeno']}, Route ID: {item['routeid']}")
#
# def select_station(items):
#     print("\n여러 개의 정류소가 검색되었습니다.")
#     for i, item in enumerate(items, start=1):
#         print(f"{i}. 정류소명: {item['nodenm']}")
#
#     while True:
#         try:
#             choice = int(input("선택할 정류소의 번호를 입력하세요: "))
#             if 1 <= choice <= len(items):
#                 return items[choice - 1]['nodeid']
#             else:
#                 print("올바르지 않은 번호입니다. 다시 입력하세요.")
#         except ValueError:
#             print("숫자를 입력하세요.")
#
# def main():
#     bus_station_name = input("버스 정류소명을 입력하세요: ")
#
#     # 첫 번째 함수 호출하여 nodeid를 얻기
#     station_info = get_bus_station_info(bus_station_name)
#
#     # 결과가 여러 개인 경우 선택
#     if len(station_info) > 1:
#         selected_node_id = select_station(station_info)
#     else:
#         selected_node_id = station_info[0]['nodeid']
#
#     # 선택한 nodeid로 두 번째 함수 호출
#     get_bus_station_gas_info(selected_node_id)
#
# if __name__ == "__main__":
#     main()
