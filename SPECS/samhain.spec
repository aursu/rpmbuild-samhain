# Support systemd presets from Fedora 18, RHEL 7
%if 0%{?fedora} >= 18 || 0%{?rhel} >= 7
%global preset_support 1
%endif

%if 0%{?rhel} < 7
%global _rundir /var/run
%endif

%define debug_package %{nil}

Summary:		The SAMHAIN file integrity/intrusion detection system
Name:			samhain
Version:		4.4.3
Release:		2%{?dist}
License:		GPLv2
URL:			https://www.la-samhna.de/samhain/

Source0:		samhain-%{version}.tar.gz
Source1:		samhain.service
Source2:        samhain.logrotate
Source3:        samhainrc
Source4:        samhain-init.service
Source5:        samhain.tmpfiles
Source6:        samhain.init

BuildRoot:		%{_tmppath}/%{name}-%{version}-%{release}-root

%if 0%{?rhel} >= 7
Requires(post):		systemd-units
Requires(preun):	systemd-units
Requires(postun):	systemd-units
%endif

BuildRequires: gnutls-devel
BuildRequires: libacl-devel
BuildRequires: libattr-devel
%if 0%{?rhel} >= 7
BuildRequires: libprelude-devel >= 5.0.0
%endif
BuildRequires: pcre-devel

# Do not provide private Perl modules
%global __provides_exclude %{?__provides_exclude:%{__provides_exclude}|}^perl\\(utils\\)
%global reqfilt sh -c "%{__perl_requires} | sed -e 's!perl(utils)!nagios-plugins-perl!'"
%global __perl_requires %{reqfilt}

%description
The Samhain host-based intrusion detection system (HIDS) provides file integrity
checking and log file monitoring/analysis, as well as rootkit detection, port
monitoring, detection of rogue SUID executables, and hidden processes.

%package -n nagios-plugins-samhain
Summary: Nagios Plugin - check_samhain
Requires: nagios-plugins-perl
Requires: %{_sbindir}/samhain

%description -n nagios-plugins-samhain
Provides check_samhain support for Nagios.

%prep
%setup -q

%build
%{_configure} --host=%{_host} --build=%{_build} \
    --prefix=%{_prefix} \
    --exec-prefix=%{_exec_prefix} \
    --sbindir=%{_sbindir} \
    --sysconfdir=%{_sysconfdir} \
    --localstatedir=%{_localstatedir} \
    --mandir=%{_mandir} \
    --enable-login-watch \
    --enable-logfile-monitor \
    --enable-mounts-check \
    --enable-network=client \
    --enable-port-check \
    --enable-posix-acl \
    --enable-process-check \
    --enable-selinux \
    --enable-suidcheck \
    --with-config-file=%{_sysconfdir}/samhain/samhainrc \
    --with-data-file=%{_localstatedir}/lib/samhain/samhain_file \
    --with-log-file=%{_localstatedir}/log/samhain/samhain.log \
    --with-pid-file=%{_rundir}/samhain/samhain.pid \
%if 0%{?rhel} >= 7
    --with-prelude \
%endif
    --with-state-dir=%{_localstatedir}/lib/samhain

make %{?_smp_mflags}

sed -i 's,/usr/local/nagios/libexec,%{_libdir}/nagios/plugins,' scripts/check_samhain.pl

%install
rm -rf %{buildroot}
make install DESTDIR=%{buildroot}

# SNMPd script
mkdir -p %{buildroot}%{_libdir}/nagios/plugins
install -p -m 744 scripts/check_samhain.pl %{buildroot}%{_libdir}/nagios/plugins/check_samhain

# install log rotation stuff
install -D -p -m 644 %{SOURCE2} %{buildroot}%{_sysconfdir}/logrotate.d/samhain
# default config
install -D -p -m 600 %{SOURCE3} %{buildroot}%{_sysconfdir}/samhain/samhainrc
mkdir -p %{buildroot}%{_localstatedir}/lib/samhain %{buildroot}%{_localstatedir}/log/samhain

%if 0%{?rhel} >= 7
install -D -p -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/samhain.service
install -D -p -m 644 %{SOURCE4} %{buildroot}%{_unitdir}/samhain-init.service
# tmpfiles.d configuration (CentOS 7)
mkdir -p %{buildroot}%{_prefix}/lib/tmpfiles.d
install -m 644 -p $RPM_SOURCE_DIR/samhain.tmpfiles \
    %{buildroot}%{_prefix}/lib/tmpfiles.d/samhain.conf
%else
# install SYSV init stuff
mkdir -p %{buildroot}/etc/rc.d/init.d
install -m 755 %{SOURCE6} \
    %{buildroot}/etc/rc.d/init.d/samhain
%endif

%check
exit 0

%clean
rm -rf %{buildroot}

%post
%if 0%{?rhel} >= 7
/bin/systemctl daemon-reload &>/dev/null || :
if [ $1 -eq 1 ]; then
    # Initial installation
%if 0%{?preset_support:1}
    /bin/systemctl preset samhain.service &>/dev/null || :
%endif
fi
%else
/sbin/chkconfig --add samhain
%endif

%preun
%if 0%{?rhel} >= 7
if [ $1 -eq 0 ]; then
    # Package removal, not upgrade
    /bin/systemctl --no-reload disable samhain-init.service samhain.service &>/dev/null || :
    /bin/systemctl stop samhain.service samhain-init.service &>/dev/null || :
fi
%else
if [ $1 -eq 0 ]; then
    /sbin/service samhain stop >/dev/null 2>&1
    /sbin/chkconfig --del samhain
fi
%endif

%postun
%if 0%{?rhel} >= 7
/bin/systemctl daemon-reload &>/dev/null || :
if [ $1 -ge 1 ]; then
    # Package upgrade, not uninstall
    /bin/systemctl try-restart samhain.service &>/dev/null || :
fi
%endif

%files
%{_sbindir}/samhain
%{_sbindir}/samhain_setpwd
%attr(600,root,root) %config(noreplace) %{_sysconfdir}/samhain/samhainrc
%config(noreplace) %{_sysconfdir}/logrotate.d/samhain
%if 0%{?rhel} >= 7
%{_unitdir}/samhain.service
%{_unitdir}/samhain-init.service
%{_prefix}/lib/tmpfiles.d/samhain.conf
%else
%{_sysconfdir}/rc.d/init.d/samhain
%endif
%{_mandir}/man8/samhain.8.gz
%{_mandir}/man5/samhainrc.5.gz
%dir %{_localstatedir}/lib/samhain
%dir %{_localstatedir}/log/samhain

%files -n nagios-plugins-samhain
%{_libdir}/nagios/plugins/check_samhain

%changelog
* Fri Nov 27 2020 Alexander Ursu <alexander.ursu@gmail.com> - 4.4.3-2
- Added support for CentOS 6

* Wed Nov 25 2020 Alexander Ursu <alexander.ursu@gmail.com> - 4.4.3-1
- upgrade to 4.4.3
- added check_samhain script

* Thu Mar 26 2020 Alexander Ursu <aursu@hostopia.com> - 4.4.1-1
- upgrade to 4.4.1

* Wed Nov 28 2018 Alexander Ursu <aursu@hostopia.com> - 4.3.1-1
- initial build
