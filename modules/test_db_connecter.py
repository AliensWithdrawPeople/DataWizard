import Models
import User
import db_connecter

Models.Base.metadata.create_all(db_connecter.engine)
user = Models.User(
    id = 2, 
    password = "qwerty",
    name = "test",
    role = 'admin', 
    phone_number = "+79324375590",
    email = "test2@test.com"
    # birthdate = None,
    # position = None,
    # certificate_number = None,
    # certificated_till = None,
    # reports = None
    ) 
session = db_connecter.get_session()
session.add(user)
session.commit()

# a = User.User_info.check_and_load("test@test.com", "qwerty")
a = User.User_info.check_and_load("test2@test.com", "qwerty")
print(a.get_id() if not a is None else "None!!!")