FROM ubuntu:trusty
COPY stackdriver.list /etc/apt/sources.list.d/
COPY RPM-GPG-KEY-stackdriver /
RUN apt-key add /RPM-GPG-KEY-stackdriver
ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update && apt-get install -y curl libhiredis0.10 stackdriver-agent
COPY collectd.conf.tmpl /opt/stackdriver/collectd/etc/
COPY redis.conf /opt/stackdriver/collectd/etc/collectd.d/
COPY run.sh /
CMD ["/run.sh"]
