.DEFAULT_GOAL := build

build:
	PGSERVER_VERSION=16 $(MAKE) -C ../../pgbuild all
	rm -rf src/pgserver_binaries/pg16
	mkdir -p src/pgserver_binaries/pg16
	cp -r ../../src/pgserver/pginstall/* src/pgserver_binaries/pg16/

clean:
	rm -rf src/pgserver_binaries/pg16
	PGSERVER_VERSION=16 $(MAKE) -C ../../pgbuild clean
