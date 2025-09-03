FROM debian:12.11-slim

WORKDIR /app

RUN apt update

RUN apt install git vim emacs -y

RUN git clone https://github.com/ezyway/demo_file.git

WORKDIR demo_file

CMD ["cat", "random_file.txt"]