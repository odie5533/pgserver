SHELL := /bin/bash
INSTALL_PREFIX := $(shell pwd)/../src/pgserver/pginstall/
BUILD := $(shell pwd)/pgbuild/

# PostgreSQL version to build (can be overridden via environment variable)
# Default to 18 if not specified
PGSERVER_VERSION ?= 18

# Detect OS for setting correct RPATH
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Linux)
    RPATH_FLAG := -Wl,-rpath,'\$$\$$ORIGIN/../lib'
else ifeq ($(UNAME_S),Darwin)
    RPATH_FLAG := -Wl,-rpath,@loader_path/../lib
endif

### PostgreSQL version definitions
PG16_VERSION := 16.10
PG17_VERSION := 17.6
PG18_VERSION := 18.0

# Set the version-specific variables based on PGSERVER_VERSION
ifeq ($(PGSERVER_VERSION),16)
    POSTGRES_VERSION := $(PG16_VERSION)
else ifeq ($(PGSERVER_VERSION),17)
    POSTGRES_VERSION := $(PG17_VERSION)
else ifeq ($(PGSERVER_VERSION),18)
    POSTGRES_VERSION := $(PG18_VERSION)
else
    $(error Invalid PGSERVER_VERSION: $(PGSERVER_VERSION). Must be 16, 17, or 18)
endif

.PHONY: all
all: postgres pgvector

### PostgreSQL build
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
	cd $(POSTGRES_BLD) && LDFLAGS="$(RPATH_FLAG)" ../$(POSTGRES_SRC)/configure --prefix=$(INSTALL_PREFIX) --without-readline --without-icu

## build
# https://stackoverflow.com/questions/68379786/
# for explanation of unsetting make env variables prior to calling postgres' own make
$(POSTGRES_BLD)/src/bin/initdb/initdb: $(POSTGRES_BLD)/config.status
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS && $(MAKE) -C $(POSTGRES_BLD) -j

## install to INSTALL_PREFIX
$(INSTALL_PREFIX)/bin/postgres: $(POSTGRES_BLD)/config.status
	mkdir -p $(INSTALL_PREFIX)
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS && $(MAKE) -C $(POSTGRES_BLD) install
	# Set RPATH on all binaries to find bundled libraries
	@echo "Setting RPATH on PostgreSQL binaries..."
ifeq ($(UNAME_S),Linux)
	@if command -v patchelf >/dev/null 2>&1; then \
		for binary in $(INSTALL_PREFIX)/bin/*; do \
			if file "$$binary" | grep -q ELF; then \
				echo "Setting RPATH for $$binary"; \
				patchelf --force-rpath --set-rpath '$$ORIGIN/../lib' "$$binary" || true; \
			fi \
		done; \
	else \
		echo "Warning: patchelf not found, binaries may not find bundled libraries"; \
	fi
else ifeq ($(UNAME_S),Darwin)
	@for binary in $(INSTALL_PREFIX)/bin/*; do \
		if file "$$binary" | grep -q "Mach-O"; then \
			echo "Setting RPATH for $$binary"; \
			install_name_tool -add_rpath @loader_path/../lib "$$binary" 2>/dev/null || true; \
		fi \
	done
endif

.PHONY: postgres
postgres: $(INSTALL_PREFIX)/bin/postgres

### pgvector
PGVECTOR_TAG := v0.8.1
PGVECTOR_URL := https://github.com/pgvector/pgvector/archive/refs/tags/$(PGVECTOR_TAG).tar.gz
PGVECTOR_DIR := pgvector-$(PGVECTOR_TAG)

$(PGVECTOR_DIR).tar.gz:
	curl -L -o $(PGVECTOR_DIR).tar.gz $(PGVECTOR_URL)

$(PGVECTOR_DIR)/Makefile: $(PGVECTOR_DIR).tar.gz
	mkdir -p $(PGVECTOR_DIR)
	tar xzf $(PGVECTOR_DIR).tar.gz -C $(PGVECTOR_DIR) --strip-components=1
	touch $(PGVECTOR_DIR)/Makefile

$(INSTALL_PREFIX)/lib/vector.so: $(PGVECTOR_DIR)/Makefile $(INSTALL_PREFIX)/bin/postgres
	unset MAKELEVEL && unset MAKEFLAGS && unset MFLAGS \
		&& export PG_CONFIG=$(INSTALL_PREFIX)/bin/pg_config \
		&& $(MAKE) -C $(PGVECTOR_DIR) -j \
		&& $(MAKE) -C $(PGVECTOR_DIR) install

.PHONY: pgvector
pgvector: postgres $(INSTALL_PREFIX)/lib/vector.so

### other
.PHONY: clean clean-all
clean:
	rm -rf $(INSTALL_PREFIX)
	rm -rf $(POSTGRES_SRC)
	rm -rf $(POSTGRES_BLD)
	rm -rf $(PGVECTOR_DIR)

clean-all: clean
	rm -rf *.tar.gz