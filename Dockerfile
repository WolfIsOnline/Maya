FROM python:3.12.1-bullseye

WORKDIR /maya

COPY . /maya

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-OO", "__main__.py"]