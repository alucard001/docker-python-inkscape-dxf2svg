FROM ubuntu:latest

WORKDIR /root

EXPOSE 80 443

RUN apt-get update \
    && apt-get install -y python3 \
        pip \
    && apt-get clean \
    && apt-get autoclean

RUN pip install boto3
RUN pip install flask
RUN pip install waitress

COPY Inkscape-3bf5ae0-x86_64.AppImage /root/
RUN chmod +x Inkscape-3bf5ae0-x86_64.AppImage

# Output dir is squashfs-root/
RUN ./Inkscape-3bf5ae0-x86_64.AppImage --appimage-extract

# https://stackoverflow.com/a/26504961/1802483
COPY app.py /root/
ADD inkscape/ /root/inkscape

CMD ["waitress-serve", "--listen=*:80", "--listen=*:443", "--ident=inkscape", "--max-request-header-size=1048576", "app:app"]