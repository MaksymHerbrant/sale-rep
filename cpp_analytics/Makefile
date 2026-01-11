CXX = g++
CXXFLAGS = -std=c++11 -Wall -O2

TARGET = analytics
SRC = analytics.cpp

all: $(TARGET)

$(TARGET): $(SRC)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SRC)

clean:
	rm -f $(TARGET)
