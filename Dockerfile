FROM python:3.11-slim
RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir --upgrade \
	asyncclick==8.3.0.7 \
	aiomqtt==2.5.1 \
	paho-mqtt==2.1.0 \
	python-dateutil==2.9.0.post0 \
	pytz==2026.2 \
	pymongo==4.17.0
