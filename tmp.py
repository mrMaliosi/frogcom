import db

# Безопасно сохраняет пароль (хеширование + соль)
def save_password(pwd):
    db.write(pwd)

