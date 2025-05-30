import logging

import requests
import cloudscraper  # 导入 cloudscraper

from dotenv import dotenv_values

env = dotenv_values(".env")
TELEGRAM_API_KEY = env.get("TELEGRAM_API_KEY")
DEBUGGING_CHAT_ID = env.get("DEBUGGING_CHAT_ID")


def generate_payload(cities, page_size):
    payload = {
        "operationName": "GetCategories",
        "variables": {
            "currentPage": 1,
            "id": "Nw==",
            "filters": {
                "available_to_book": {"in": ["179", "336"]},
                "city": {"in": cities},
                "category_uid": {"eq": "Nw=="},
            },
            "pageSize": page_size,
            "sort": {"available_startdate": "ASC"},
        },
        "query": """
            query GetCategories($id: String!, $pageSize: Int!, $currentPage: Int!, $filters: ProductAttributeFilterInput!, $sort: ProductAttributeSortInput) {
              categories(filters: {category_uid: {in: [$id]}}) {
                items {
                  uid
                  ...CategoryFragment
                  __typename
                }
                __typename
              }
              products(
                pageSize: $pageSize
                currentPage: $currentPage
                filter: $filters
                sort: $sort
              ) {
                ...ProductsFragment
                __typename
              }
            }

            fragment CategoryFragment on CategoryTree {
              uid
              meta_title
              meta_keywords
              meta_description
              __typename
            }

            fragment ProductsFragment on Products {
              items {
                name
                sku
                city
                url_key
                available_to_book
                available_startdate
                building_name
                finishing
                living_area
                no_of_rooms
                resident_type
                offer_text_two
                offer_text
                maximum_number_of_persons
                type_of_contract
                price_analysis_text
                allowance_price
                floor
                basic_rent
                lumpsum_service_charge
                inventory
                caretaker_costs
                cleaning_common_areas
                energy_common_areas
                allowance_price
                small_image {
                  url
                  label
                  position
                  disabled
                  __typename
                }
                thumbnail {
                  url
                  label
                  position
                  disabled
                  __typename
                }
                image {
                  url
                  label
                  position
                  disabled
                  __typename
                }
                media_gallery {
                  url
                  label
                  position
                  disabled
                  __typename
                }
                price_range {
                  minimum_price {
                    regular_price {
                      value
                      currency
                      __typename
                    }
                    final_price {
                      value
                      currency
                      __typename
                    }
                    discount {
                      amount_off
                      percent_off
                      __typename
                    }
                    __typename
                  }
                  maximum_price {
                    regular_price {
                      value
                      currency
                      __typename
                    }
                    final_price {
                      value
                      currency
                      __typename
                    }
                    discount {
                      amount_off
                      percent_off
                      __typename
                    }
                    __typename
                  }
                  __typename
                }
                __typename
              }
              page_info {
                total_pages
                __typename
              }
              total_count
              __typename
            }
        """,
    }
    return payload


CITY_IDS = {
    "24": "Amsterdam",
    "320": "Arnhem",
    "619": "Capelle aan den IJssel",
    "26": "Delft",
    "28": "Den Bosch",
    "90": "Den Haag",
    "110": "Diemen",
    "620": "Dordrecht",
    "29": "Eindhoven",
    "545": "Groningen",
    "616": "Haarlem",
    "6099": "Helmond",
    "6209": "Maarssen",
    "6090": "Maastricht",
    "6051": "Nieuwegein",
    "6217": "Nijmegen",
    "25": "Rotterdam",
    "6224": "Rijswijk",
    "6211": "Sittard",
    "6093": "Tilburg",
    "27": "Utrecht",
    "6145": "Zeist",
    "6088": "Zoetermeer",
}

CONTRACT_TYPES = {
    "21": "Indefinite",
    "6125": "2 years",
    "20": "1 year max",
    "318": "6 months max",
    "606": "4 months max",
}

ROOM_TYPES = {
    "104": "Studio",
    "6137": "Loft (open bedroom area)",
    "105": "1",
    "106": "2",
    "108": "3",
    "382": "4",
}

MAX_REGISTER_TYPES = {
    "22": "One",
    "23": "Two (only couples)",
    "500": "Two",
    "380": "Family (parents with children)",
    "501": "Three",
    "502": "Four",
}

# 定义房源预订方式类型
BOOKING_TYPES = {
    "179": "DIRECT_BOOKING",  # 可直接预定
    "336": "LOTTERY",         # 需要抽签
}


def city_id_to_city(city_id):
    # Use CITY_IDS dictionary for city lookup
    return CITY_IDS.get(city_id)


def contract_type_id_to_str(contract_type_id):
    # Use CONTRACT_TYPES dictionary for contract type lookup
    return CONTRACT_TYPES.get(contract_type_id, "Unknown")


def room_id_to_room(room_id):
    # Use ROOM_TYPES dictionary for room type lookup
    return ROOM_TYPES.get(room_id, "Unknown")


def max_register_id_to_str(maxregister_id):
    # Use MAX_REGISTER_TYPES dictionary for max occupancy lookup
    return MAX_REGISTER_TYPES.get(maxregister_id, "Unknown")


def booking_type_id_to_str(booking_type_id):
    # 获取预订方式的描述
    return BOOKING_TYPES.get(str(booking_type_id), "Unknown")


def is_direct_booking(booking_type_id):
    # 判断是否为可直接预定的房源
    return str(booking_type_id) == "179"


def url_key_to_link(url_key):
    return f"https://holland2stay.com/residences/{url_key}.html"


def clean_img(url):
    try:
        if 'cache' not in url:
            return url
        parts = url.split('/')
        ci = parts.index('cache')
        return '/'.join(parts[:ci] + parts[ci + 2:])
    except Exception as error:
        logging.error("Error in cleaning image URL")
        logging.error(url)
        logging.error(str(error))


def house_to_msg(house):
    booking_type = "可直接预定" if house.get('direct_booking') else "需要抽签"
    return f"""
New house in #{city_id_to_city(house['city'])}!
{url_key_to_link(house['url_key'])}

Living area: {house['area']}m²
Price: {float(house['price_inc'].replace(',', '.')):,}€ (excl. {float(house['price_exc'].replace(',', '.')):,}€ basic rent)
Price per meter: {float(float(house['price_inc']) / float(house['area'])):.2f} €\\m²

Available from: {house['available_from']}
Bedrooms: {house['rooms']}
Max occupancy: {house['max_register']}
Contract type: {house['contract_type']}
预订方式: {booking_type}

# See details and apply on Holland2Stay website."""


# Define the GraphQL query payload
def scrape(cities=[], page_size=30, only_direct_booking=True):
    logging.info(f"开始爬取网页，城市IDs: {cities}, 每页数量: {page_size}, 仅显示可直接预定: {only_direct_booking}")

    payload = generate_payload(cities, page_size)
    try:
        # 添加请求头以模拟真实浏览器
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Origin': 'https://holland2stay.com',
            'Referer': 'https://holland2stay.com/residences.html',
            'sec-ch-ua': '"Google Chrome";v="121", "Not A(Brand";v="99", "Chromium";v="121"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'Connection': 'keep-alive'
        }

        logging.info("创建 cloudscraper 实例...")
        scraper = cloudscraper.create_scraper()  # 使用 cloudscraper 创建 scraper

        logging.info("开始发送 POST 请求到 Holland2Stay API...")
        response = scraper.post(
            "https://api.holland2stay.com/graphql/",
            json=payload,
            headers=headers,
            timeout=30  # 增加超时时间
        )

        # 检查响应状态码
        if response.status_code != 200:
            logging.error(f"API请求失败，状态码: {response.status_code}")
            logging.error(f"响应内容: {response.text[:500]}")  # 只打印前500个字符
            return {}

        logging.info("成功获取API响应，开始解析数据...")

        # 尝试解析JSON并添加错误处理
        try:
            json_data = response.json()
            if "data" not in json_data:
                logging.error(f"API响应中没有'data'字段: {json_data}")
                return {}

            data = json_data["data"]
            cities_dict = {}
            for c in cities:
                cities_dict[c] = []

            # 检查products是否存在
            if "products" not in data or "items" not in data["products"]:
                logging.error(f"API响应格式不符合预期: {data}")
                return cities_dict

            total_houses = len(data["products"]["items"])
            logging.info(f"获取到 {total_houses} 个房源")

            direct_booking_count = 0
            lottery_count = 0

            for house in data["products"]["items"]:
                city_id = str(house["city"])
                try:
                    # 判断房源是否可以直接预定
                    booking_type_id = house.get("available_to_book")
                    direct_booking = is_direct_booking(booking_type_id)

                    # 记录统计信息
                    if direct_booking:
                        direct_booking_count += 1
                    else:
                        lottery_count += 1

                    # 如果设置了only_direct_booking且不是直接预定的房源，则跳过
                    if only_direct_booking and not direct_booking:
                        continue

                    cleaned_images = [clean_img(img['url']) for img in house.get('media_gallery', [])]

                    # For now, this image is making an issue. Maybe we need to add similar images later
                    cleaned_images = list(filter(lambda x: x is not None and "logo-blue-1.jpg" not in x, cleaned_images))

                    cities_dict[city_id].append(
                        {
                            "url_key": house["url_key"],
                            "city": str(house["city"]),
                            "area": str(house["living_area"]).replace(",", "."),
                            "price_exc": str(house["basic_rent"]),
                            "price_inc": str(
                                house["price_range"]["maximum_price"]["final_price"]["value"]
                            ),
                            "available_from": house["available_startdate"],
                            "max_register": str(
                                max_register_id_to_str(str(house["maximum_number_of_persons"])),
                            ),
                            "contract_type": contract_type_id_to_str(
                                str(house["type_of_contract"])
                            ),
                            "rooms": room_id_to_room(str(house["no_of_rooms"])),
                            "images": cleaned_images,
                            "booking_type": booking_type_id_to_str(booking_type_id),
                            "direct_booking": direct_booking
                        }
                    )
                except Exception as err:
                    logging.error("Error in parsing house")
                    logging.error(str(err))
                    logging.error(str(house))

            # 记录每个城市的房源数量和预订类型统计
            logging.info(f"预订方式统计：可直接预定: {direct_booking_count}，需要抽签: {lottery_count}")

            for city_id, houses in cities_dict.items():
                city_name = city_id_to_city(city_id) or city_id
                logging.info(f"城市 {city_name}({city_id}) 找到 {len(houses)} 个满足条件的房源")

            return cities_dict

        except ValueError as json_err:
            logging.error(f"JSON解析错误: {json_err}")
            logging.error(f"响应内容: {response.text[:500]}")  # 只打印前500个字符
            return {}

    except Exception as request_err:
        logging.error(f"请求异常: {request_err}")
        return {}
