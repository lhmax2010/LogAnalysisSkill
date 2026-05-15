%define pname demo-macro
Name: %{pname}
Version: 1.0
Release: 1
BuildRequires: pkgconfig(foo) >= 1.0
Source0: %{pname}-%{version}.tar.gz

%description
Macro package.

%build
%configure
make %{?_smp_mflags}
