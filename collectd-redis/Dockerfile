FROM ubuntu:trusty
RUN apt-get install -y curl
RUN apt-get update && apt-get install -y collectd libhiredis0.10
COPY collectd.conf.tmpl /etc/collectd/
COPY redis.conf /etc/collectd/collectd.conf.d/
COPY run.sh /
CMD ["/run.sh"]
