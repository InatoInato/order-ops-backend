FROM ubuntu:latest
LABEL authors="inato"

ENTRYPOINT ["top", "-b"]