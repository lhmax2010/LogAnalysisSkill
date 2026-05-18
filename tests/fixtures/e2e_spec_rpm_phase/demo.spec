Name: demo
Version: 1
Release: 1
BuildRequires: gcc

%description
demo

%install
install -m 0755 missing %{buildroot}/usr/bin/demo
