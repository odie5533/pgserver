.DEFAULT_GOAL := build

build:
	PGSERVER_VERSION=17 $(MAKE) -C ../../pgbuild all
	rm -rf src/pgserver_binaries/pg17
	mkdir -p src/pgserver_binaries/pg17
	cp -r ../../src/pgserver/pginstall/* src/pgserver_binaries/pg17/

clean:
	rm -rf src/pgserver_binaries/pg17
	PGSERVER_VERSION=17 $(MAKE) -C ../../pgbuild clean
