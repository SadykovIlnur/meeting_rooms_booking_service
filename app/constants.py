from pathlib import Path

# Максимальная длина имени пользователя
MAX_USERNAME_LENGTH = 100

# Максимальная длина пароля
MAX_LENGTH_PASSWORD = 255

# Максимальная длина названия комнаты
MAX_ROOMNAME_LENGTH = 30

# Образ PostgreSQL (integration-test)
POSTGRES_IMAGE = "postgres:16"

# Путь до csv-файлов
DATA_DIR = Path(__file__).parent.parent / "app" / "data"

# URL тестов
BASE_URL = "http://test/api/v1"

# Ожидаемое количество записей (unit-test)
COUNT_BOOKINGS_UNIT_TEST = 1

# Ожидаемое количество временных слотов (unit-test)
COUNT_SLOTS_UNIT_TEST = 2

# Ожидаемое количество временных слотов (integration-test)
COUNT_SLOTS_INT_TEST = 5

# Ожидаемое количество комнат (unit-test)
COUNT_ROOMS_UNIT_TEST = 2

# Ожидаемое количество комнат (integration-test)
COUNT_ROOMS_INT_TEST = 3

# Ожидаемое id room_id (unit-test)
ROOM_ID_UNIT_TEST = 1

# Ожидаемое id timeslot_id (unit-test)
TIMESLOT_ID_UNIT_TEST = 1

# Ожидаемое id timeslot_id (integration-test)
TIMESLOT_ID_INT_TEST = 1

# Ожидаемое id user_id
USER_ID_TEST = 1

# Ожидаемые пары временных слотов (integration-test)
EXPECTED_TIME_PAIRS = {('09:00:00', '11:00:00'), ('11:00:00', '13:00:00'), ('13:00:00', '15:00:00'), ('15:00:00', '17:00:00'), ('17:00:00', '19:00:00')}
