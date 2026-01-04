CXX = g++
CXXFLAGS = -std=c++11 -Wall -O2
TARGET = analytics
SOURCE = analytics.cpp
SOURCE_OOP = analytics_oop.cpp
TARGET_OOP = analytics_oop

all: $(TARGET) $(TARGET_OOP)

$(TARGET): $(SOURCE)
	$(CXX) $(CXXFLAGS) -o $(TARGET) $(SOURCE)

$(TARGET_OOP): $(SOURCE_OOP)
	$(CXX) $(CXXFLAGS) -o $(TARGET_OOP) $(SOURCE_OOP)

clean:
	rm -f $(TARGET) $(TARGET_OOP)

.PHONY: all clean

