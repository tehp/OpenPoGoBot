CC ?= cc
CFLAGS ?= -g -fPIC
LDFLAGS ?=

LIBENCRYPT_OBJS = encrypt.o
TEST_OBJS = main.o
OBJS = $(LIBENCRYPT_OBJS) $(TEST_OBJS)
TARGETS = libencrypt.so

all: $(TARGETS)

libencrypt.so: $(LIBENCRYPT_OBJS)
	$(CC) $(CFLAGS) $(LDFLAGS) -shared -o $@ $(LIBENCRYPT_OBJS) -lm

lib: libencrypt.so

clean:
	$(RM) $(OBJS) $(TARGETS)
