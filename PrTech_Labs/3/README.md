Лабораторная работа 3: "Схемы форматов передачи данных"
Задание на лабораторную работу: Добавить в свой предыдущий проект возможность сохранения состояния в виде периодического сохранения, 
либо в виде функций импорта и экспорта. 
Выбранный формат для сериализации должен иметь схему. 
В проекте обязателен код валидирующий данные. 
Валидация должна производиться либо в программе при импорте данных, либо в юнит-тестах, проверяющих корректность сохранения состояния.

Описание: Были добравлены новые функции в сервер, такие как возможность сохранить состояние, и загрузка программы из последнего сохраненного состояния.
Для этого в server.py были реализованны следующие элементы:

json-схема сервера для вадидации файла сохранения;
метод load_session(), загружающий сессию из файла и производящий валидацию json;
метод save_session(), сохранающий текущее состояние сервера в виде json.
