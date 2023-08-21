import modules.Models as Models
import modules.User_info as User_info
import modules.db_connecter as db_connecter
from passlib.hash import pbkdf2_sha256

from datetime import date

Models.Base.metadata.create_all(db_connecter.engine)
user = Models.User(
    # id = 7, 
    password = pbkdf2_sha256.hash("test_inspector"),
    name = "test_inspector3",
    role = 'inspector', 
    phone_number = "+78005553535",
    email = "test_inspector3@test_inspector3.com",
    birthdate = date.fromisoformat('1970-01-01'),
    position = "Средний инспектор по тестам",
    certificate_number = "A2",
    certificated_till = date.fromisoformat('2024-01-01')
) 
session = db_connecter.get_session()
session.add(user)
session.commit()

# a = User.User_info.check_and_load("test@test.com", "qwerty")
# a = User_info.User_info.check_and_load("test4@test.com", "qwerty")
# print(a.get_id() if not a is None else "None!!!")