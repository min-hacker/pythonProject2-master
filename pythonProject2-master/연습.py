def check_travel_itinerary(keyword):
    keywords = {"Gwanghwamun", "Seoul", "Jeonju Hanok Village", "Odongdo island in Yeosu", "Jeonju"}

    if keyword.capitalize() in keywords:
        if keyword in {"Seoul", "Yeosu"}:
            print(f"Yes, {keyword} is in your travel itinerary!")
        else:
            print(f"Yes, {keyword.capitalize()} is in your travel itinerary!")
    else:
        print(f"Sorry, {keyword} is not in your travel itinerary.")

user_input = input("Enter a city you mant to check in the itinerary: ")

if user_input in {"Gwanghwamun in Seoul", "Gwanghwamun", "gwanghwamun", "Seoul", "seoul", "Jeonju Hanok Village", "jeonju hanok village", "Odongdo island in Yeosu", "odongdo island in yeosu", "Jeonju", "jeonju"}:
    if user_input in {"Gwanghwamun in Seoul", "Seoul", "seoul"}:
        print("Yes, Gwanghwamun in Seoul is in your travel itinerary!")
    elif user_input in {"Jeonju Hanok Village", "jeonju hanok village", "Jeonju", "jeonju"}:
        check_travel_itinerary(user_input)
    elif user_input in {"Odongdo island in Yeosu", "odongdo island in yeosu", "Yeosu"}:
        check_travel_itinerary(user_input)
    else:
        check_travel_itinerary(user_input)
else:
    check_travel_itinerary(user_input)
