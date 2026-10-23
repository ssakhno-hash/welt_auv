# welt_auv
Stingray powered AUV Welt

---

## Vision pipeline (камера + автоматическая запись rosbag2)

### Как запустить

    cd ~/repos/welt_auv-master
    source /opt/ros/jazzy/setup.bash
    colcon build --packages-select welt_launch
    source install/setup.bash
    ros2 launch welt_launch vision.launch.py

Одна команда запускает камеру и автоматически начинает запись в rosbag2.

### Камеры

| Название | Тип         | Устройство  | Namespace        | Image topic          | CameraInfo topic          | Optical frame                    |
|----------|-------------|-------------|------------------|----------------------|---------------------------|----------------------------------|
| laptop   | встроенная  | /dev/video0 | /camera_laptop   | /camera_laptop/image_raw | /camera_laptop/camera_info | camera_laptop_optical_frame  |

Описание камер — в `src/welt_launch/config/cameras.yaml`.

### Стабильное соответствие USB-камер

Для USB-камер используется путь `/dev/v4l/by-id/usb-<vendor>_<model>_<serial>-video-index0`.
Эта ссылка привязана к серийному номеру устройства и не меняется при перезагрузке
или переподключении, в отличие от `/dev/video0`, `/dev/video1` и т.п.

Посмотреть доступные by-id ссылки:

    ls -l /dev/v4l/by-id/

Для встроенной камеры ноутбука (текущий вариант) by-id ссылки может не быть —
используется `/dev/video0`. Для реальных USB-камер в конфиг подставляется by-id.

### Какие топики записываются

- `/camera_laptop/image_raw` — изображения (sensor_msgs/Image)
- `/camera_laptop/camera_info` — параметры камеры (sensor_msgs/CameraInfo)

**Зачем именно эти топики для Computer Vision:**
- `Image` — сами кадры для обработки (детекция, трекинг, сегментация).
- `CameraInfo` — матрица внутренних параметров и коэффициенты дисторсии,
  без них нельзя корректно устранить искажения (undistort) и восстановить
  3D-геометрию (например, положение объекта в пространстве).

При добавлении нескольких камер в `cameras.yaml` запись автоматически
расширяется на все топики вида `/<namespace>/image_raw` и `/<namespace>/camera_info`.

### Куда пишется запись

Каждый запуск создаёт отдельную сессию:

    /tmp/bags/
      2026-10-09_18-13-23/
      2026-10-09_18-21-07/
      2026-10-09_18-30-12/

Имя сессии = дата и время старта, поэтому старая запись не перезаписывается.

Для сохранения на внешний диск достаточно поменять значение `bag_root`
в `vision.launch.py` (по умолчанию `/tmp/bags`).

### Разбиение записи

Используется разбиение **по размеру**:

    --max-bag-size 1073741824    # 1 GiB

Почему по размеру, а не по времени:
- размер файла предсказуем и не зависит от fps/разрешения,
- удобно копировать на флешку или в облако,
- не упираемся в лимит файловой системы (FAT32 = 4 ГБ).

При необходимости размер легко меняется одной цифрой.

### Контроль свободного места

Перед стартом записи launch проверяет свободное место в `bag_root`:
если меньше 2 ГБ — запись не запускается, в терминал выводится явная ошибка

    RuntimeError: Недостаточно места в /tmp/bags: X.XX GB (need >= 2 GB)

Это исключает ситуацию, когда система молча перестаёт писать данные.

### Корректное завершение

При нажатии **Ctrl+C**:
1. launch отправляет SIGINT процессу `ros2 bag record`,
2. rosbag2 закрывает файл `.mcap` и завершает запись,
3. камера (`usb_cam_node_exe`) останавливается,
4. bag остаётся валидным и готовым к `ros2 bag play`.

### QoS

`usb_cam` публикует изображения с QoS `BEST_EFFORT`, что не совпадает
с дефолтным `RELIABLE` для rosbag2. Для надёжной подписки в проекте
предусмотрен файл `src/welt_launch/config/qos_overrides.yaml` с явным
описанием `reliability: best_effort` для каждого топика камеры.
Файл подключается к `ros2 bag record` через `--qos-profile-overrides-path`.

### Проверка записи и воспроизведения

1. Записать:
       ros2 launch welt_launch vision.launch.py
   (остановить — Ctrl+C)

2. Посмотреть, что записалось:
       ros2 bag info /tmp/bags/<имя_сессии>

3. Воспроизвести:
       ros2 bag play /tmp/bags/<имя_сессии>

4. В другом терминале убедиться, что картинки идут:
       source /opt/ros/jazzy/setup.bash
       ros2 topic hz /camera_laptop/image_raw
   Ожидаемая частота — около 30 Гц.

5. Визуально:
       ros2 run rqt_image_view rqt_image_view
   Выбрать топик /camera_laptop/image_raw.

### Известные ограничения

- Проект изначально собран на ROS 2 Humble (Ubuntu 22.04), в текущем
  варианте pipeline адаптирован под ROS 2 Jazzy (Ubuntu 24.04).
- Сабмодуль `src/sauvc` в исходном архиве отсутствует, поэтому запуск
  камер реализован собственным `cam_multi`-launch на базе пакета `usb_cam`,
  без использования `sauvc_launch/cam.launch.py`.
- Калибровочный файл встроенной камеры отсутствует (`default_cam.yaml`),
  `camera_info` публикуется с нулевой матрицей. Для реальных задач
  требуется откалибровать камеру (`ros2 run camera_calibration cameracalibrator ...`).
- Скрипт `stingray_recorder` (запись AVI) не задействован: штатная запись
  ведётся через `rosbag2`.
