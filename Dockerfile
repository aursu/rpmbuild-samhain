FROM aursu/rpmbuild:7.7.1908-build

USER root
RUN yum -y install \
        gnutls-devel \
        libacl-devel \
        libattr-devel \
        libprelude-devel \
        pcre-devel \
    && yum clean all && rm -rf /var/cache/yum

COPY SOURCES ${BUILD_TOPDIR}/SOURCES
COPY SPECS ${BUILD_TOPDIR}/SPECS

RUN chown -R $BUILD_USER ${BUILD_TOPDIR}/{SOURCES,SPECS}

USER $BUILD_USER
ENTRYPOINT ["/usr/bin/rpmbuild", "samhain.spec"]
CMD ["-ba"]
