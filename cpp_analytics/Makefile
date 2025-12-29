CXX = g++
CXXFLAGS = -std=c++11 -Wall -O2
TARGET = analytics
SOURCE = analytics.cpp

all: $(TARGET)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE)

clean:
	rm -f $(TARGET)

.PHONY: all clean

