from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import requests # Для отправки HTTP запросов на ESP32
import json     # Для работы с JSON

app = Flask(__name__)
app.secret_key = 'your_very_secret_key' # Нужно для flash сообщений

# --- КОНФИГУРАЦИЯ ---
# !!! ЗАМЕНИТЕ НА АДРЕС ВАШЕГО ESP32 !!!
ESP32_IP_ADDRESS_OR_HOSTNAME = "music-leds.local" # или "192.168.X.X"
ESP32_SETTINGS_URL = f"http://{ESP32_IP_ADDRESS_OR_HOSTNAME}/settings"
REQUEST_TIMEOUT = 5 # Секунд на ожидание ответа от ESP32
# --------------------

# Храним текущие настройки (чтобы отображать их в форме)
# Инициализируем значениями по умолчанию, похожими на ESP32
current_settings = {
    "mode": 0,
    "vu_green_red": {
        "sensitivity": 70,
        "brightness": 80,
        "bgColor": "#000000",
        "bgBrightness": 10,
        "smoothing": 30
    },
    "vu_rainbow": {
        "sensitivity": 70,
        "brightness": 80,
        "bgColor": "#000000",
        "bgBrightness": 10,
        "smoothing": 30
    },
    "flash": {
        "sensitivity": 80,
        "color": "#FFFFFF",
        "brightness": 100,
        "smoothing": 10
    }
}

@app.route('/')
def index():
    """Отображает главную страницу с формой управления."""
    # Передаем текущие настройки в шаблон
    return render_template('index.html', settings=current_settings)

@app.route('/update', methods=['POST'])
def update_settings():
    """Принимает данные из формы, формирует JSON и отправляет на ESP32."""
    global current_settings
    try:
        # Получаем выбранный режим
        mode = int(request.form.get('mode', 0))
        payload = {"mode": mode}

        # Собираем настройки для выбранного режима
        if mode == 0: # VU Green-Red
            settings = {
                "sensitivity": int(request.form.get('vu_gr_sensitivity', 70)),
                "brightness": int(request.form.get('vu_gr_brightness', 80)),
                "bgColor": request.form.get('vu_gr_bgColor', '#000000'),
                "bgBrightness": int(request.form.get('vu_gr_bgBrightness', 10)),
                "smoothing": int(request.form.get('vu_gr_smoothing', 30)),
            }
            payload["vu_green_red"] = settings
            # Обновляем локальные настройки для отображения
            current_settings["vu_green_red"] = settings

        elif mode == 1: # VU Rainbow
            settings = {
                "sensitivity": int(request.form.get('vu_rb_sensitivity', 70)),
                "brightness": int(request.form.get('vu_rb_brightness', 80)),
                "bgColor": request.form.get('vu_rb_bgColor', '#000000'),
                "bgBrightness": int(request.form.get('vu_rb_bgBrightness', 10)),
                "smoothing": int(request.form.get('vu_rb_smoothing', 30)),
            }
            payload["vu_rainbow"] = settings
            current_settings["vu_rainbow"] = settings

        elif mode == 2: # Flash
            settings = {
                "sensitivity": int(request.form.get('fl_sensitivity', 80)),
                "color": request.form.get('fl_color', '#FFFFFF'),
                "brightness": int(request.form.get('fl_brightness', 100)),
                "smoothing": int(request.form.get('fl_smoothing', 10)), # Сглаживание для затухания
            }
            payload["flash"] = settings
            current_settings["flash"] = settings

        # Обновляем режим в локальных настройках
        current_settings["mode"] = mode

        print(f"Отправка на {ESP32_SETTINGS_URL}: {json.dumps(payload)}") # Отладка

        # Отправляем POST запрос на ESP32
        headers = {'Content-Type': 'application/json'}
        response = requests.post(
            ESP32_SETTINGS_URL,
            headers=headers,
            data=json.dumps(payload),
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status() # Вызовет исключение для кодов ошибок HTTP (4xx, 5xx)

        # Проверяем ответ от ESP32 (опционально, но полезно)
        try:
            response_json = response.json()
            print(f"Ответ от ESP32: {response_json}")
            if response_json.get("status") == "ok":
                flash('Настройки успешно отправлены!', 'success')
            elif response_json.get("status") == "no_change":
                 flash('Настройки отправлены, но изменений не было.', 'info')
            else:
                flash(f"ESP32 вернул статус: {response_json.get('status', 'неизвестно')}", 'warning')
        except json.JSONDecodeError:
            print("Не удалось декодировать JSON ответ от ESP32.")
            flash('Настройки отправлены, но ответ от ESP32 не в формате JSON.', 'warning')


    except requests.exceptions.ConnectionError:
        flash(f'Ошибка: Не удалось подключиться к ESP32 по адресу {ESP32_SETTINGS_URL}. Убедитесь, что он включен и находится в той же сети.', 'danger')
        print(f"Ошибка подключения к {ESP32_SETTINGS_URL}")
    except requests.exceptions.Timeout:
        flash(f'Ошибка: ESP32 не ответил в течение {REQUEST_TIMEOUT} секунд.', 'danger')
        print(f"Таймаут при подключении к {ESP32_SETTINGS_URL}")
    except requests.exceptions.RequestException as e:
        flash(f'Произошла ошибка при отправке запроса: {e}', 'danger')
        print(f"Ошибка запроса: {e}")
    except Exception as e:
        flash(f'Произошла внутренняя ошибка сервера: {e}', 'danger')
        print(f"Непредвиденная ошибка: {e}")

    # Перенаправляем пользователя обратно на главную страницу
    return redirect(url_for('index'))

if __name__ == '__main__':
    # host='0.0.0.0' делает сервер доступным в локальной сети
    # port=5000 стандартный порт для Flask
    # debug=True удобно для разработки (автоперезагрузка при изменениях),
    # но НЕ ИСПОЛЬЗУЙТЕ в продакшене!
    app.run(host='0.0.0.0', port=5000, debug=True)