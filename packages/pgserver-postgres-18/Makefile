.DEFAULT_GOAL := build

build:
	PGSERVER_VERSION=18 $(MAKE) -C ../../pgbuild all
	rm -rf src/pgserver_binaries/pg18
	mkdir -p src/pgserver_binaries/pg18
	cp -r ../../src/pgserver/pginstall/* src/pgserver_binaries/pg18/

clean:
	rm -rf src/pgserver_binaries/pg18
	PGSERVER_VERSION=18 $(MAKE) -C ../../pgbuild clean
