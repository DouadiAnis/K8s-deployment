FROM python:3.9-slim
WORKDIR /app
RUN pip install flask mysql-connector-python
COPY app.py .
CMD ["python", "app.py"]