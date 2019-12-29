FROM python:3.8-slim

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 80
CMD ["python"]
