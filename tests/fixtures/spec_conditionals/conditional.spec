Name: conditional
Version: 1.0
Release: 1
%if 0%{?tizen}
BuildRequires: pkgconfig(tizen)
%endif
BuildRequires: gcc
Source0: conditional.tar.gz

%description
Conditional package.

%prep
%setup -q

%build
make conditional
