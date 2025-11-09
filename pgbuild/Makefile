SHELL := /bin/bash
# Parallelism: adjust via `make JOBS=4` locally; CI defaults to 2 for stability
JOBS ?= 2
# Optional: override strip program
STRIP ?= strip
# Keep dev artifacts (headers/static libs/pgxs) if set to 1
KEEP_DEV ?= 0
INSTALL_PREFIX := $(shell pwd)/../src/pgserver/pginstall/
BUILD := $(shell pwd)/pgbuild/

.PHONY: all
all: pgvector postgis postgres prune

### postgres
POSTGRES_VERSION := 16.2
POSTGRES_URL := https://ftp.postgresql.org/pub/source/v$(POSTGRES_VERSION)/postgresql-$(POSTGRES_VERSION).tar.gz
POSTGRES_SRC := postgresql-$(POSTGRES_VERSION)
POSTGRES_BLD := $(POSTGRES_SRC)

$(POSTGRES_SRC).tar.gz:
	curl -L -O $(POSTGRES_URL)

## extract
$(POSTGRES_SRC)/configure: $(POSTGRES_SRC).tar.gz
	tar xzf $(POSTGRES_SRC).tar.gz
	touch $(POSTGRES_SRC)/configure

## configure
$(POSTGRES_BLD)/config.status: $(POSTGRES_SRC)/configure
	mkdir -p $(POSTGRES_BLD)
	cd $(POSTGRES_BLD) && ../$(POSTGRES_SRC)/configure --prefix=$(INSTALL_PREFIX) --without-readline --without-icu

## build
# https://stackoverflow.com/questions/68379786/
# for explanation of unsetting make env variables prior to calling postgres' own make
$(POSTGRES_BLD)/src/bin/initdb/initdb: $(POSTGRES_BLD)/config.status
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS && $(MAKE) -C $(POSTGRES_BLD) -j$(JOBS)

## install to INSTALL_PREFIX
$(INSTALL_PREFIX)/bin/postgres: $(POSTGRES_BLD)/config.status
	mkdir -p $(INSTALL_PREFIX)
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS && $(MAKE) -C $(POSTGRES_BLD) install
	patchelf --set-rpath '$$ORIGIN/../lib' $(INSTALL_PREFIX)/bin/postgres || true

.PHONY: postgres
postgres: $(INSTALL_PREFIX)/bin/postgres

#
# Prune & strip to reduce wheel size without affecting runtime
#   - remove static libs and headers/dev files
#   - remove pgxs build system
#   - strip binaries and shared libs
# Keep all runtime .so and essential executables in place.
.PHONY: prune
prune: postgres postgis pgvector
	@sh -c 'if [ "$(KEEP_DEV)" != "1" ]; then \
	  find $(INSTALL_PREFIX)/lib -type f -name "*.a" -print -delete || true; \
	  rm -rf $(INSTALL_PREFIX)/include $(INSTALL_PREFIX)/lib/postgresql/pgxs || true; \
	else \
	  echo "KEEP_DEV=1 set; preserving headers/static libs/pgxs"; \
	fi'
	@echo "-- Removing non-essential PostgreSQL client tools"
	@sh -c 'for f in $(INSTALL_PREFIX)/bin/*; do \
	  bn=$$(basename "$$f"); \
	  case "$$bn" in \
	    postgres|initdb|pg_ctl|psql|pg_config) \
	      ;; \
	    *) \
	      rm -f "$$f"; \
	      ;; \
	  esac; \
	done'
	@echo "-- Keeping only core PostGIS extension files; removing contrib payload"
	@sh -c 'extdir=$(INSTALL_PREFIX)/share/postgresql/extension; \
	  if [ -d "$$extdir" ]; then \
	    find "$$extdir" -maxdepth 1 -type f -name "postgis*" \
	      ! -name "postgis.control" \
	      ! -name "postgis--$(POSTGIS_VER).sql" -print -delete; \
	  fi; \
	  rm -rf $(INSTALL_PREFIX)/share/postgresql/contrib || true'
	@sh -c 'if command -v $(STRIP) >/dev/null 2>&1; then \
	  find $(INSTALL_PREFIX)/bin -type f -exec $(STRIP) --strip-all {} + 2>/dev/null || true; \
	  find $(INSTALL_PREFIX)/lib -type f -name "*.so*" -exec $(STRIP) --strip-unneeded {} + 2>/dev/null || true; \
	  find $(INSTALL_PREFIX)/lib/postgresql -type f -name "*.so*" -exec $(STRIP) --strip-unneeded {} + 2>/dev/null || true; \
	else \
	  echo "strip not available; skipping binary stripping"; \
	fi'

### pgvector
PGVECTOR_TAG := v0.8.1
PGVECTOR_URL := https://github.com/pgvector/pgvector/archive/refs/tags/$(PGVECTOR_TAG).tar.gz
PGVECTOR_DIR := pgvector-$(PGVECTOR_TAG)

$(PGVECTOR_DIR).tar.gz:
	curl -L -o $(PGVECTOR_DIR).tar.gz $(PGVECTOR_URL)

$(PGVECTOR_DIR)/Makefile: $(PGVECTOR_DIR).tar.gz
	# tar extract into pgvector-$(PGVECTOR_TAG)
	mkdir -p $(PGVECTOR_DIR)
	tar xzf $(PGVECTOR_DIR).tar.gz -C $(PGVECTOR_DIR) --strip-components=1
	touch $(PGVECTOR_DIR)/Makefile

$(INSTALL_PREFIX)/lib/vector.so: $(PGVECTOR_DIR)/Makefile $(INSTALL_PREFIX)/bin/postgres
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS \
		&& export PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config \
		&& $(MAKE) -C $(PGVECTOR_DIR) -j$(JOBS) \
		&& $(MAKE) -C $(PGVECTOR_DIR) install

.PHONY: pgvector
pgvector: postgres $(INSTALL_PREFIX)/lib/vector.so

### PostGIS dependencies and extension
# Shared CMake defaults
CMAKE_FLAGS := -DCMAKE_INSTALL_PREFIX=$(INSTALL_PREFIX) -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_SHARED_LIBS=ON -DBUILD_TESTING=OFF

# JSON-C 0.18
JSONC_VER := 0.18
JSONC_TAG := json-c-$(JSONC_VER)-20240915
$(JSONC_TAG).tar.gz:
	curl -L -o $@ https://github.com/json-c/json-c/archive/refs/tags/$(JSONC_TAG).tar.gz
$(JSONC_TAG)/CMakeLists.txt: $(JSONC_TAG).tar.gz
	mkdir -p $(JSONC_TAG) && tar xzf $< -C $(JSONC_TAG) --strip-components=1 && touch $@
$(INSTALL_PREFIX)/lib/libjson-c.so: $(JSONC_TAG)/CMakeLists.txt
	@echo "======== Building JSON-C $(JSONC_VER) ========"
	mkdir -p $(JSONC_TAG)/build && cd $(JSONC_TAG)/build && cmake .. $(CMAKE_FLAGS) -DCMAKE_INSTALL_LIBDIR=lib -DBUILD_APPS=OFF && $(MAKE) -j$(JOBS) && $(MAKE) install
	@echo "======== JSON-C build complete ========"

# libxml2 2.9.14
LIBXML2_VER := 2.9.14
libxml2-$(LIBXML2_VER).tar.xz:
	curl -L -o $@ https://download.gnome.org/sources/libxml2/2.9/libxml2-$(LIBXML2_VER).tar.xz
libxml2-$(LIBXML2_VER)/configure: libxml2-$(LIBXML2_VER).tar.xz
	mkdir -p libxml2-$(LIBXML2_VER) && tar xJf $< -C libxml2-$(LIBXML2_VER) --strip-components=1 && touch $@
$(INSTALL_PREFIX)/lib/libxml2.so: libxml2-$(LIBXML2_VER)/configure
	@echo "======== Building libxml2 $(LIBXML2_VER) ========"
	cd libxml2-$(LIBXML2_VER) && ./configure --prefix=$(INSTALL_PREFIX) --without-python --without-lzma && $(MAKE) -j$(JOBS) && $(MAKE) install
	@echo "======== libxml2 build complete ========"

# SQLite 3.49.1
SQLITE_VER := 3490100
SQLITE_YEAR := 2025
sqlite-autoconf-$(SQLITE_VER).tar.gz:
	curl -L -o $@ https://www.sqlite.org/$(SQLITE_YEAR)/sqlite-autoconf-$(SQLITE_VER).tar.gz
sqlite-autoconf-$(SQLITE_VER)/configure: sqlite-autoconf-$(SQLITE_VER).tar.gz
	mkdir -p sqlite-autoconf-$(SQLITE_VER) && tar xzf $< -C sqlite-autoconf-$(SQLITE_VER) --strip-components=1 && touch $@
$(INSTALL_PREFIX)/lib/libsqlite3.so: sqlite-autoconf-$(SQLITE_VER)/configure
	cd sqlite-autoconf-$(SQLITE_VER) && ./configure --prefix=$(INSTALL_PREFIX) && $(MAKE) -j$(JOBS) && $(MAKE) install

# PROJ 9.3.1
PROJ_VER := 9.3.1
proj-$(PROJ_VER).tar.gz:
	curl -L -o $@ https://github.com/OSGeo/PROJ/releases/download/$(PROJ_VER)/proj-$(PROJ_VER).tar.gz
proj-$(PROJ_VER)/CMakeLists.txt: proj-$(PROJ_VER).tar.gz
	mkdir -p proj-$(PROJ_VER) && tar xzf $< -C proj-$(PROJ_VER) --strip-components=1 && touch $@
$(INSTALL_PREFIX)/lib/libproj.so: proj-$(PROJ_VER)/CMakeLists.txt $(INSTALL_PREFIX)/lib/libsqlite3.so
	# Build only the library to avoid 'make install' generating proj.db via sqlite3
	mkdir -p proj-$(PROJ_VER)/build && cd proj-$(PROJ_VER)/build \
		&& cmake .. $(CMAKE_FLAGS) -DBUILD_APPS=OFF -DENABLE_TIFF=OFF -DENABLE_CURL=OFF -DBUILD_PROJSYNC=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
		&& $(MAKE) -j$(JOBS) proj
	# Manually install library and headers
	mkdir -p $(INSTALL_PREFIX)/lib $(INSTALL_PREFIX)/include
	cp -a proj-$(PROJ_VER)/build/lib/libproj.* $(INSTALL_PREFIX)/lib/
	find proj-$(PROJ_VER)/src -name "*.h" -exec cp {} $(INSTALL_PREFIX)/include/ \;
	find proj-$(PROJ_VER)/include -name "*.h" -exec cp {} $(INSTALL_PREFIX)/include/ \; 2>/dev/null || true
	cp proj-$(PROJ_VER)/build/include/*.h $(INSTALL_PREFIX)/include/ 2>/dev/null || true

# GEOS
GEOS_VER := 3.14.1
geos-$(GEOS_VER).tar.bz2:
	curl -L -o $@ https://github.com/libgeos/geos/releases/download/$(GEOS_VER)/geos-$(GEOS_VER).tar.bz2
geos-$(GEOS_VER)/CMakeLists.txt: geos-$(GEOS_VER).tar.bz2
	mkdir -p geos-$(GEOS_VER) && tar xjf $< -C geos-$(GEOS_VER) --strip-components=1 && touch $@

$(INSTALL_PREFIX)/lib/libgeos.so: geos-$(GEOS_VER)/CMakeLists.txt
	mkdir -p geos-$(GEOS_VER)/build && cd geos-$(GEOS_VER)/build && cmake .. $(CMAKE_FLAGS) -DCMAKE_POLICY_VERSION_MINIMUM=3.5 && $(MAKE) -j$(JOBS) && $(MAKE) install
	# Ensure libgeos_c can resolve libgeos via $ORIGIN (use soname symlink)
	@if [ -e $(INSTALL_PREFIX)/lib/libgeos_c.so.1 ]; then \
		patchelf --set-rpath '$$ORIGIN' $(INSTALL_PREFIX)/lib/libgeos_c.so.1 || true; \
	fi

# PostGIS (works with PostgreSQL 16, GEOS 3.14.x, PROJ 9.3.x)
POSTGIS_VER := 3.6.0
postgis-$(POSTGIS_VER).tar.gz:
	curl -L -o $@ https://github.com/postgis/postgis/archive/refs/tags/$(POSTGIS_VER).tar.gz
postgis-$(POSTGIS_VER)/configure.ac: postgis-$(POSTGIS_VER).tar.gz
	mkdir -p postgis-$(POSTGIS_VER) && tar xzf $< -C postgis-$(POSTGIS_VER) --strip-components=1 && touch $@
postgis-$(POSTGIS_VER)/configure: postgis-$(POSTGIS_VER)/configure.ac
	cd postgis-$(POSTGIS_VER) && ./autogen.sh
$(INSTALL_PREFIX)/lib/postgis-3.so: postgis-$(POSTGIS_VER)/configure $(INSTALL_PREFIX)/bin/postgres $(INSTALL_PREFIX)/lib/libjson-c.so $(INSTALL_PREFIX)/lib/libxml2.so $(INSTALL_PREFIX)/lib/libproj.so $(INSTALL_PREFIX)/lib/libgeos.so
	cd postgis-$(POSTGIS_VER) && PATH=$(INSTALL_PREFIX)/bin:$$PATH LD_LIBRARY_PATH=$(INSTALL_PREFIX)/lib PKG_CONFIG_PATH=$(INSTALL_PREFIX)/lib/pkgconfig \
		LDFLAGS="-L$(INSTALL_PREFIX)/lib -Wl,-rpath,$(INSTALL_PREFIX)/lib" \
		./configure --prefix=$(INSTALL_PREFIX) --with-pgconfig=$(INSTALL_PREFIX)/bin/pg_config \
		--with-projdir=$(INSTALL_PREFIX) --with-geosconfig=$(INSTALL_PREFIX)/bin/geos-config \
		--without-raster --without-topology --without-protobuf
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS && PATH=$(INSTALL_PREFIX)/bin:$$PATH LD_LIBRARY_PATH=$(INSTALL_PREFIX)/lib $(MAKE) -C postgis-$(POSTGIS_VER) -j$(JOBS) && $(MAKE) -C postgis-$(POSTGIS_VER) install
	# Ensure postgis-3.so resolves local libs at runtime
	patchelf --set-rpath '$$ORIGIN/../../lib' $(INSTALL_PREFIX)/lib/postgresql/postgis-3.so || true
	# Explicitly install official extension SQL/control (3.6.0 may not place by default)
	@export PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config; \
	PATH=$(INSTALL_PREFIX)/bin:$$PATH $(MAKE) -C postgis-$(POSTGIS_VER)/extensions/postgis install

.PHONY: postgis
postgis: $(INSTALL_PREFIX)/lib/postgis-3.so

### other
.PHONY: clean clean-all
clean:
	rm -rf $(INSTALL_PREFIX) $(POSTGRES_SRC) $(POSTGRES_BLD) $(PGVECTOR_DIR)
	rm -rf $(JSONC_TAG) libxml2-$(LIBXML2_VER) sqlite-autoconf-$(SQLITE_VER) proj-$(PROJ_VER) geos-$(GEOS_VER) postgis-$(POSTGIS_VER)

clean-all: clean
	rm -rf *.tar.gz *.tar.bz2 *.tar.xz
