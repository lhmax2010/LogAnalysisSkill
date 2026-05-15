Name: subdemo
Version: 1.0
Release: 1
BuildRequires: gcc
Source0: subdemo.tar.gz

%description
Main package.

%package devel
Summary: Development files

%description devel
Development package.

%build
make all
