Name: demo
Version: 1.0
Release: 1
Summary: Demo package
BuildRequires: gcc, make
Source0: demo-1.0.tar.gz
Patch0: fix-build.patch

%description
Demo package.

%prep
%setup -q
%patch0 -p1

%build
cmake .
make

%install
make install DESTDIR=%{buildroot}
