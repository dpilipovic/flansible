FROM python:alpine
# Dockerfile to run both nginx as well as gunicorn UWSGI server which connects to Flask app
# Could be easily split into two containers with docker-compose file
# For latest build deps, see https://github.com/nginxinc/docker-nginx/blob/master/mainline/alpine/Dockerfile
# Install OS dependencies for Alpine via apk
RUN apk add --no-cache --virtual .build-deps \
    gcc \
    libc-dev \
    make \
    openssl-dev \
    pcre-dev \
    zlib-dev \
    linux-headers \
    curl \
    gnupg \
    libxslt-dev \
    gd-dev \
    geoip-dev \
    # Upwards from here are tools needed to compile nginx and bellow are tools needed to support Python modules from requirements file
    openssh \
    gcc \
    g++ \
    cmake \
    libffi-dev \
    bash \
    openrc \
    git \
    openssl \
    tzdata

# Download nginx and sticky module sources
RUN  mkdir -p /usr/src && \
     curl -fSL https://nginx.org/download/nginx-1.15.8.tar.gz -o /usr/src/nginx.tar.gz && \
     curl -fSL https://bitbucket.org/nginx-goodies/nginx-sticky-module-ng/get/08a395c66e42.zip -o /usr/src/sticky_module.zip

# Unpack nginx sources and a fix for sticky module compile error: ngx_http_sticky_misc.c:176:15: error: 'SHA_DIGEST_LENGTH' undeclared (first use in this function)
RUN cd /usr/src/ && \
    tar -zxvf nginx.tar.gz && \
    rm -rf nginx.tar.gz && \
    unzip sticky_module.zip && \
    rm -rf sticky_module.zip && \
    sed -i '12s/^/#ifndef MD5_DIGEST_LENGTH \n/' /usr/src/nginx-goodies-nginx-sticky-module-ng-08a395c66e42/ngx_http_sticky_misc.c && \
    sed -i '13s/^/#include <openssl\/sha.h> \n/' /usr/src/nginx-goodies-nginx-sticky-module-ng-08a395c66e42/ngx_http_sticky_misc.c && \
    sed -i '14s/^/#endif \n/' /usr/src/nginx-goodies-nginx-sticky-module-ng-08a395c66e42/ngx_http_sticky_misc.c && \
    sed -i '15s/^/#ifndef SHA_DIGEST_LENGTH \n/' /usr/src/nginx-goodies-nginx-sticky-module-ng-08a395c66e42/ngx_http_sticky_misc.c && \
    sed -i '16s/^/#include <openssl\/md5.h> \n/' /usr/src/nginx-goodies-nginx-sticky-module-ng-08a395c66e42/ngx_http_sticky_misc.c && \
    sed -i '17s/^/#endif \n/' /usr/src/nginx-goodies-nginx-sticky-module-ng-08a395c66e42/ngx_http_sticky_misc.c

# Compile nginx source and add sticky module
RUN  bash && \
     CONFIG="\
--prefix=/etc/nginx \
--sbin-path=/usr/sbin/nginx \
--modules-path=/usr/lib/nginx/modules \
--conf-path=/etc/nginx/nginx.conf \
--error-log-path=/var/log/nginx/error.log \
--http-log-path=/var/log/nginx/access.log \
--pid-path=/var/run/nginx.pid \
--lock-path=/var/run/nginx.lock \
--http-client-body-temp-path=/var/cache/nginx/client_temp \
--http-proxy-temp-path=/var/cache/nginx/proxy_temp \
--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp \
--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp \
--http-scgi-temp-path=/var/cache/nginx/scgi_temp \
--user=nginx \
--group=nginx \
--with-http_ssl_module \
--with-http_realip_module \
--with-http_addition_module \
--with-http_sub_module \
--with-http_dav_module \
--with-http_flv_module \
--with-http_mp4_module \
--with-http_gunzip_module \
--with-http_gzip_static_module \
--with-http_random_index_module \
--with-http_secure_link_module \
--with-http_stub_status_module \
--with-http_auth_request_module \
--with-http_xslt_module=dynamic \
--with-http_image_filter_module=dynamic \
--with-http_geoip_module=dynamic \
--with-threads \
--with-stream \
--with-stream_ssl_module \
--with-stream_ssl_preread_module \
--with-stream_realip_module \
--with-stream_geoip_module=dynamic \
--with-http_slice_module \
--with-mail \
--with-mail_ssl_module \
--with-compat \
--with-file-aio \
--with-http_v2_module \
" \
        && addgroup -S nginx && \
        adduser -D -S -h /var/cache/nginx -s /sbin/nologin -G nginx nginx &&\
        cd /usr/src/nginx-1.15.8/ && \
        ./configure $CONFIG --add-module=/usr/src/nginx-goodies-nginx-sticky-module-ng-08a395c66e42 && \
         make && make install

# Obtain Application code
RUN cd /opt/ && \
    git clone https://github.com/dpilipovic/flansible.git

# Setup Python3 and it's pip as default and create venv
RUN python -m ensurepip --default-pip && \
    alias pip='python -m pip'

# Install requirements
RUN cd /opt/flansible/ && \
     python -m venv venv && \
     venv/bin/pip install -r requirements.txt

# Create self-signed certs so that nginx can start OK - If you want to use it permanently, you want to replace the CN with your own here
RUN mkdir -p /etc/nginx/certs && \
    cd /etc/nginx/certs && \
    # Generating signing SSL private key
    openssl genrsa -des3 -passout pass:example -out key.pem 2048 && \
    # Removing passphrase from private key
    cp key.pem key.pem.orig && \
    openssl rsa -passin pass:example -in key.pem.orig -out key.pem && \
    # Generating certificate signing request
    openssl req -new -key key.pem -out cert.csr -subj "/C=US/ST=California/L=San Francisco/O=Example/OU=Example/CN=default" && \
    # Generating self-signed certificate
    openssl x509 -req -days 3650 -in cert.csr -signkey key.pem -out cert.pem && \
    cp /opt/flansible/misc/nginx.conf-alpine /etc/nginx/nginx.conf

# Few more small changes for Docker Alpine release to function a ok. tzlocal python library requires /etc/localtime and we want alpine version of startup script which solves docker network routing
RUN cp -r -f /usr/share/zoneinfo/UTC /etc/localtime && \
    cp -r -f /opt/flansible/bin/start-flansible-alpine.sh /opt/flansible/bin/start-flansible.sh &&\
    chmod u+x /opt/flansible/bin/start-flansible.sh && chmod 600 /opt/flansible/app/id_rsa && \
    chmod u+x /opt/flansible/bin/start-docker-services.sh

# Make /opt a volume to persist data
VOLUME /opt

# Run nginx as well as app
EXPOSE 80 443
STOPSIGNAL SIGTERM
CMD /opt/flansible/bin/start-docker-services.sh
