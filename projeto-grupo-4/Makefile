# Variables for architecture
ARCH ?= x86_64
CXX_x86_64 = g++
CXX_arm = aarch64-linux-gnu-g++
CXXFLAGS = -std=c++17 -Wall -Wextra -Iinclude
LDFLAGS = -lpthread

# Select compiler based on architecture
ifeq ($(ARCH), x86_64)
    CXX = $(CXX_x86_64)
else ifeq ($(ARCH), arm)
    CXX = $(CXX_arm)
else
    $(error Invalid ARCH value: $(ARCH). Use ARCH=x86_64 or ARCH=arm)
endif

# Directories
SRC_DIR = src
INC_DIR = include
BUILD_DIR = build
BIN_DIR = bin

# Source, Object, and Executable files
SRC_FILES = $(wildcard $(SRC_DIR)/*.cpp)
OBJ_FILES = $(SRC_FILES:$(SRC_DIR)/%.cpp=$(BUILD_DIR)/%.o)
EXEC = $(BIN_DIR)/program_$(ARCH)

.PHONY: all run clean

# Default target: Build and link everything
all: $(EXEC)

# Linking the final executable
$(EXEC): $(OBJ_FILES)
	mkdir -p $(BIN_DIR)
	$(CXX) $(OBJ_FILES) -o $(EXEC) $(LDFLAGS)

# Compile source files to object files
$(BUILD_DIR)/%.o: $(SRC_DIR)/%.cpp
	mkdir -p $(BUILD_DIR)
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Run the program
run: all
	@echo "Running the program for architecture: $(ARCH)"
	./$(EXEC)

# Clean up build artifacts
clean:
	rm -rf $(BUILD_DIR) $(BIN_DIR)
	mkdir -p $(BIN_DIR)
