FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app
COPY . /app/

# 🔁 Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# 🔧 Install system dependencies (Graphviz)
RUN apt-get update && apt-get install -y graphviz

EXPOSE 8000

CMD ["python", "ontologygen_web/manage.py", "runserver", "0.0.0.0:8000"]
