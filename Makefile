.PHONY: package clean

# The target zip file
TARGET = kasa_manager.zip

# The files that need to be in the zip file
SOURCES = kasa_manager.py requirements.txt kasa.sh Dockerfile

package: clean
	@echo "Creating portable zip package..."
	zip $(TARGET) $(SOURCES)
	@echo "Created $(TARGET) successfully!"

clean:
	@echo "Cleaning up..."
	rm -f $(TARGET)
