Name: installfail
Version: 1.0
Release: 1
BuildRequires: make
Source0: installfail.tar.gz
Patch2: install-dir.patch

%description
Install failure package.

%build
make

%install
mkdir -p %{buildroot}/usr/bin
install -m 0755 missing %{buildroot}/usr/bin/missing
