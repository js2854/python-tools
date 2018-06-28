include Makefile.POSIX

NAME=Demo

CCFLAGS += -Wall -fPIC

# EACH DIRECTORY WITH HEADERS MUST BE APPENDED IN THIS MANNER TO THE CCFLAGS
CCFLAGS += -I.
CCFLAGS += -I./src
CCFLAGS += -I../lib/include
CCFLAGS += -I../common/include

LIBS += -L../lib/bin -llog4cxx
LIBS += -L../lib/bin -lCommonUtilitiesLib

CFILES = ../common/common.c
CFILES += ../common/md5.c

CPPFILES =	src/main.cpp \
	src/utils.cpp \
	./common/hls.cpp\
	./common/re.cpp
	
SUBDIRS =


all: $(NAME)
	test -f ../Makefile.POSIX || exit 1
	
$(NAME): Make_Subs $(CFILES:.c=.o) $(CPPFILES:.cpp=.o)
	$(LINK) -o $@ $(CFILES:.c=.o) $(CPPFILES:.cpp=.o) $(COMPILER_FLAGS) $(LINKOPTS) $(LIBS) $(CORE_LINK_LIBS)

install: $(NAME)
	cp $(NAME) /usr/local/bin

clean:
	rm -f $(NAME) $(CFILES:.c=.o) $(CPPFILES:.cpp=.o)
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir clean; \
	done

Make_Subs:
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir  $*; \
	done

