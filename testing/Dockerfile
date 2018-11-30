FROM aursu/rpmbuild:7-build-systemd

RUN yum -y --enablerepo custom install \
        samhain \
    && yum clean all && rm -rf /var/cache/yum

RUN systemctl enable samhain-init.service \
                     samhain.service
