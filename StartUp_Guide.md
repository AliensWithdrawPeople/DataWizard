# Step by step guide on how to work with DataWizard App

Проверка лога сайта (см. <https://blog.miguelgrinberg.com/post/running-a-flask-application-as-a-service-with-systemd>)
journalctl -u microblog

Запуск сервиса:
$ sudo systemctl daemon-reload
$ sudo systemctl start wizard
