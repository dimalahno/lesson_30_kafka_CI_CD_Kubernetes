# Kafka CI/CD Kubernetes Demo - Расширенная документация

Демонстрационный проект, показывающий интеграцию Apache Kafka с CI/CD пайплайном и развертыванием в Kubernetes.

## 📋 Описание проекта

Этот проект представляет собой полный цикл разработки и развертывания приложения на Python, которое работает с Apache Kafka. Проект включает:

- **Python приложение** для отправки и получения сообщений через Kafka
- **Docker контейнеризацию** приложения
- **Docker Compose** для локального развертывания Kafka и Zookeeper
- **GitLab CI/CD пайплайн** для автоматической сборки, тестирования и развертывания
- **Kubernetes манифесты** для развертывания в кластере

## 🏗️ Архитектура

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Python App    │--->│     Kafka       │<---│   Zookeeper     │
│  (Producer/     │    │   (Message      │    │  (Coordination) │
│   Consumer)     │    │    Broker)      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                        ┌─────────────────┐
                        │   Kubernetes    │
                        │    Cluster      │
                        └─────────────────┘
```

## 📁 Структура проекта

```
.
├── app/
│   └── main.py              # Основное приложение (producer/consumer)
├── .gitlab-ci.yml           # CI/CD пайплайн для GitLab
├── docker-compose.yml       # Конфигурация для локального развертывания
├── Dockerfile              # Образ Docker для приложения
├── kafka-demo-deployment.yml # Kubernetes deployment манифест
├── requirements.txt        # Python зависимости
└── README.md              # Документация проекта
```

## 💻 Код проекта с комментариями

### 1. Основное Python приложение (`app/main.py`)

```python
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import time

def produce_messages():
    """
    Функция для отправки сообщений в Kafka топик.
    Создает producer, отправляет сообщение и подтверждает доставку.
    """
    # Создаем producer с подключением к Kafka брокеру на localhost:9092
    producer = KafkaProducer(bootstrap_servers='localhost:9092')
    
    # Подготавливаем сообщение в байтовом формате
    message = b'Hello, Kafka!'
    
    # Отправляем сообщение в топик 'test_topic'
    producer.send('test_topic', value=message)
    
    # Ждем подтверждения доставки всех сообщений
    producer.flush()
    
    print("Message sent successfully: " + message.decode('utf-8'))
    
def consume_messages():
    """
    Функция для чтения сообщений из Kafka топика.
    Создает consumer и читает сообщения с таймаутом.
    """
    # Создаем consumer для чтения из топика 'test_topic'
    consumer = KafkaConsumer(
        'test_topic',                    # Имя топика для чтения
        bootstrap_servers='localhost:9092',  # Адрес Kafka брокера
        auto_offset_reset='earliest',    # Читать с самого начала топика
        consumer_timeout_ms=5000         # Таймаут ожидания новых сообщений (5 сек)
    )
    
    # Читаем сообщения из топика
    for message in consumer:
        print(f"Received message: {message.value.decode('utf-8')}")
        time.sleep(1)  # Имитируем время обработки сообщения

if __name__ == "__main__":
    try:
        # Сначала отправляем сообщение
        produce_messages()
        
        # Небольшая пауза для гарантии доставки
        time.sleep(2)
        
        # Затем читаем сообщения
        consume_messages()
        
    except KafkaError as e:
        print(f"An error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
```

### 2. Docker конфигурация (`Dockerfile`)

```dockerfile
# Используем официальный образ Python 3.10.2
FROM python:3.10.2

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей в контейнер
COPY requirements.txt /app/

# Устанавливаем Python зависимости без кеширования
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app

# Устанавливаем переменную окружения для адреса Kafka брокера
ENV KAFKA_BROKER=localhost:9092

# Команда запуска приложения при старте контейнера
CMD ["python", "app/main.py"]
```

### 3. Docker Compose конфигурация (`docker-compose.yml`)

```yaml
version: '3'
services:
    # Сервис Zookeeper - координатор для Kafka кластера
    zookeeper:
        image: confluentinc/cp-zookeeper:latest
        container_name: zookeeper
        environment:
            # Порт для клиентских подключений
            ZOOKEEPER_CLIENT_PORT: 2181
            # Интервал между heartbeat сообщениями (мс)
            ZOOKEEPER_TICK_TIME: 2000
        ports:
            - "2181:2181"  # Проброс порта на хост машину
            
    # Сервис Kafka - брокер сообщений
    kafka:
        image: confluentinc/cp-kafka:7.2.1
        container_name: kafka
        depends_on:
            - zookeeper  # Kafka запускается после Zookeeper
        ports:
            - "9092:9092"  # Проброс порта Kafka на хост машину
        environment:
            # Уникальный ID брокера в кластере
            KAFKA_BROKER_ID: 1
            # Адрес Zookeeper для координации
            KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
            # Адреса для прослушивания подключений
            KAFKA_LISTENERS: PLAINTEXT://0.0.0.0:9092
            # Адреса, которые Kafka сообщает клиентам для подключения
            KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092
            # Фактор репликации для служебного топика offsets
            KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
```

### 4. GitLab CI/CD пайплайн (`.gitlab-ci.yml`)

```yaml
# Определяем этапы пайплайна
stages:
  - build    # Сборка Docker образа
  - test     # Тестирование приложения
  - deploy   # Развертывание в целевую среду

# Глобальные переменные для пайплайна
variables:
  DOCKER_IMAGE: my-kafka-app
  DOCKER_TAG: $CI_COMMIT_SHORT_SHA  # Используем короткий хеш коммита как тег

# Этап сборки Docker образа
build:
  stage: build
  image: docker:latest
  services:
    - docker:dind  # Docker-in-Docker для сборки образов
  script:
    - echo "Сборка Docker-образа..."
    # Собираем образ с тегом из переменных
    - docker build -t $DOCKER_IMAGE:$DOCKER_TAG .
    # Авторизуемся в Docker registry
    - docker login -u "$CI_REGISTRY_USER" -p "$CI_REGISTRY_PASSWORD" $CI_REGISTRY
    # Загружаем образ в registry
    - docker push $DOCKER_IMAGE:$DOCKER_TAG
  only:
    - master   # Запускаем только для веток master
    - develop  # и develop

# Этап unit тестирования
unit_tests:
  stage: test
  image: python:3.10.2
  script:
    # Устанавливаем зависимости
    - pip install --no-cache-dir -r requirements.txt
    # Запускаем unit тесты
    - pytest tests/unit
  only:
    - master
    - develop

# Этап интеграционного тестирования
integration_tests:
  stage: test
  image: docker:latest
  services:
    - docker:dind
  before_script:
    # Устанавливаем docker-compose в контейнере
    - apk add --no-cache docker-compose
    # Поднимаем Kafka и ZooKeeper для тестов
    - docker-compose up -d
    # Ждем инициализации сервисов
    - sleep 15
  script:
    - echo "Запуск интеграционных тестов..."
    - pip install --no-cache-dir -r requirements.txt
    # Запускаем интеграционные тесты
    - pytest tests/integration
  only:
    - master
    - develop

# Этап развертывания
deploy:
  stage: deploy
  image: docker:latest
  script:
    - echo "Деплой в тестовую/продакшн среду..."
    # Запускаем скрипт развертывания с образом
    - ./deploy_script.sh $DOCKER_IMAGE:$DOCKER_TAG
  only:
    - master  # Деплой только с master ветки
```

### 5. Kubernetes deployment (`kafka-demo-deployment.yml`)

```yaml
# Версия API Kubernetes
apiVersion: apps/v1
# Тип ресурса - Deployment (управляет репликами подов)
kind: Deployment
metadata:
  name: kafka-demo-app  # Имя deployment'а
spec:
  replicas: 1  # Количество реплик приложения
  # Селектор для определения подов, которыми управляет deployment
  selector:
    matchLabels:
      app: kafka-demo-app
  # Шаблон для создания подов
  template:
    metadata:
      labels:
        app: kafka-demo-app  # Метки для подов
    spec:
      containers:
        - name: kafka-demo-app        # Имя контейнера
          image: kafka-demo-app:latest # Docker образ для запуска
          ports:
            - containerPort: 80       # Порт, который слушает приложение
```

### 6. Python зависимости (`requirements.txt`)

```text
# Библиотека для работы с Apache Kafka
# Версия 2.0.2 - стабильная версия с поддержкой всех основных функций
kafka-python==2.0.2
```

## 🚀 Быстрый старт

### Предварительные требования

- Docker Desktop с включенным Kubernetes
- Python 3.10+
- kubectl (для работы с Kubernetes)
- Git

### 1. Локальное развертывание с Docker Compose

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd lesson_30_kafka_CI_CD_Kubernetes
   ```

2. **Запустите Kafka и Zookeeper:**
   ```bash
   docker-compose up -d
   ```

3. **Создайте Kafka топик:**
   ```bash
   docker exec -it kafka kafka-topics --create --topic test-topic --bootstrap-server localhost:9092 --replication-factor 1 --partitions 1
   ```

4. **Соберите Docker образ приложения:**
   ```bash
   docker build -t kafka-demo-app .
   ```

5. **Запустите приложение:**
   ```bash
   docker run --rm --network host kafka-demo-app
   ```

### 2. Развертывание в Kubernetes

1. **Убедитесь, что Kubernetes включен в Docker Desktop**

2. **Примените Kubernetes манифест:**
   ```bash
   kubectl apply -f kafka-demo-deployment.yml
   ```

3. **Проверьте статус развертывания:**
   ```bash
   kubectl get pods
   kubectl get deployments
   ```

## 🔧 Конфигурация

### Docker Compose

Файл `docker-compose.yml` настраивает:
- **Zookeeper** на порту 2181 - координирует работу Kafka кластера
- **Kafka** на порту 9092 - основной брокер сообщений

### Приложение

Приложение `app/main.py` включает:
- **Producer**: отправляет сообщение "Hello, Kafka!" в топик `test_topic`
- **Consumer**: читает сообщения из топика `test_topic` с таймаутом 5 секунд

### CI/CD Pipeline

Пайплайн `.gitlab-ci.yml` включает этапы:
1. **Build**: сборка Docker образа с тегом из хеша коммита
2. **Test**: unit и integration тесты с поднятием тестового окружения
3. **Deploy**: развертывание в целевую среду только с master ветки

## 📊 Ожидаемый результат

При успешном запуске приложения вы увидите:
```
Message sent successfully: Hello, Kafka!
Received message: Hello, Kafka!
```

## 🐛 Устранение неполадок

### Проблема: ImagePullBackOff в Kubernetes

Если вы видите статус `ImagePullBackOff`:

```bash
NAME                              READY   STATUS             RESTARTS   AGE
kafka-demo-app-57c44df46f-lwglt   0/1     ImagePullBackOff   0          20s
```

**Решение:**
1. Убедитесь, что образ собран локально:
   ```bash
   docker images | grep kafka-demo-app
   ```

2. Для локального Kubernetes добавьте в deployment манифест:
   ```yaml
   spec:
     containers:
       - name: kafka-demo-app
         image: kafka-demo-app:latest
         imagePullPolicy: Never  # Не пытаться скачать образ из registry
   ```

3. Или загрузите образ в Docker registry и обновите манифест

### Проблема: Kafka недоступен

Если приложение не может подключиться к Kafka:

1. **Проверьте статус контейнеров:**
   ```bash
   docker-compose ps
   ```

2. **Проверьте логи Kafka:**
   ```bash
   docker-compose logs kafka
   ```

3. **Убедитесь, что топик создан:**
   ```bash
   docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
   ```

4. **Проверьте сетевое подключение:**
   ```bash
   # Проверка доступности Kafka порта
   telnet localhost 9092
   ```

## 🛠️ Разработка

### Локальная разработка

1. **Установите зависимости:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Запустите Kafka через Docker Compose:**
   ```bash
   docker-compose up -d
   ```

3. **Создайте топик для разработки:**
   ```bash
   docker exec -it kafka kafka-topics --create --topic dev-topic --bootstrap-server localhost:9092 --replication-factor 1 --partitions 3
   ```

4. **Запустите приложение локально:**
   ```bash
   python app/main.py
   ```

### Добавление новых функций

1. **Модифицируйте `app/main.py`** - добавьте новую логику
2. **Обновите `requirements.txt`** при добавлении новых зависимостей
3. **Пересоберите Docker образ:**
   ```bash
   docker build -t kafka-demo-app:dev .
   ```
4. **Протестируйте изменения:**
   ```bash
   docker run --rm --network host kafka-demo-app:dev
   ```

### Полезные команды для разработки

```bash
# Просмотр всех топиков
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# Просмотр сообщений в топике
docker exec -it kafka kafka-console-consumer --topic test_topic --from-beginning --bootstrap-server localhost:9092

# Отправка сообщения через консоль
docker exec -it kafka kafka-console-producer --topic test_topic --bootstrap-server localhost:9092

# Просмотр информации о топике
docker exec -it kafka kafka-topics --describe --topic test_topic --bootstrap-server localhost:9092

# Удаление топика
docker exec -it kafka kafka-topics --delete --topic test_topic --bootstrap-server localhost:9092
```

## 📚 Дополнительные ресурсы

- [Apache Kafka Documentation](https://kafka.apache.org/documentation/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [kafka-python Library Documentation](https://kafka-python.readthedocs.io/)

## 🔍 Архитектурные решения

### Выбор технологий

1. **Python + kafka-python**: Простая и надежная библиотека для работы с Kafka
2. **Docker Compose**: Удобное решение для локальной разработки и тестирования
3. **GitLab CI/CD**: Полнофункциональный пайплайн с поддержкой Docker
4. **Kubernetes**: Стандарт для оркестрации контейнеров в продакшене

### Паттерны проектирования

- **Producer-Consumer**: Классический паттерн для асинхронной обработки сообщений
- **Container-First**: Приложение изначально проектируется для работы в контейнерах
- **Infrastructure as Code**: Вся инфраструктура описана в конфигурационных файлах

## 📝 Лицензия

Этот проект создан в учебных целях.
