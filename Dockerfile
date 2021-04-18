FROM python:3.8.9-slim
RUN mkdir /app
COPY requirements.txt /app
WORKDIR /app
RUN pip install -r requirements.txt
COPY data/ /app/data/
COPY tests/ /app/tests/
COPY src/ /app/src/
WORKDIR /app/src
CMD bokeh serve --show dashboard.py
EXPOSE 5006