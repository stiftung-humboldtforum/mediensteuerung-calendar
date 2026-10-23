FROM python:3.11-slim
RUN pip install --no-cache-dir --upgrade pip

RUN pip install --no-cache-dir --upgrade \
	asyncclick==8.1.3.4 \
	anyio==3.6.2 \
	aiomqtt==1.1.0 \
	python-dateutil==2.8.2 \
	pytz==2023.3.post1 \
	motor==3.7.0
