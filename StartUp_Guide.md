# Step by step guide on how to work with DataWizard App

Проверка лога сайта (см. <https://blog.miguelgrinberg.com/post/running-a-flask-application-as-a-service-with-systemd>)
journalctl -u microblog

Запуск сервиса:
sudo systemctl stop wizard
sudo systemctl daemon-reload
sudo systemctl start wizard

Проверка:
ps -x | grep waitress
Должно быть что-то типа:
$ 1053692 ?        Ssl    0:01 /usr/bin/python3 /usr/bin/waitress-serve --host 127.0.0.1 --port 8000 app:app
$ 1053726 pts/0    R+     0:00 grep --color=auto waitress
