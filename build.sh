#!/bin/bash
set -e

echo "Building UPK .deb package using setuptools approach (Size Optimized)..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root for installation
if [[ $EUID -eq 0 ]]; then
   print_warning "This script should not be run as root for building"
   print_warning "Use sudo only when installing the final .deb package"
   exit 1
fi

# Read version from VERSION file
VERSION=$(cat VERSION)
print_status "Building UPK version: $VERSION"

# Create temporary directory for packaging
TEMP_DIR=$(mktemp -d)
print_status "Creating temporary directory: $TEMP_DIR"

# Create package structure
mkdir -p "$TEMP_DIR"/{DEBIAN,usr/bin,usr/share/doc/upk,usr/lib/python3/dist-packages/upk}

# Copy source files to package structure
print_status "Copying source files to package structure..."
cp -r backends "$TEMP_DIR/usr/lib/python3/dist-packages/upk/"
cp config.py "$TEMP_DIR/usr/lib/python3/dist-packages/upk/"
cp display.py "$TEMP_DIR/usr/lib/python3/dist-packages/upk/"
cp search.py "$TEMP_DIR/usr/lib/python3/dist-packages/upk/"
cp utils.py "$TEMP_DIR/usr/lib/python3/dist-packages/upk/"
cp upk.py "$TEMP_DIR/usr/lib/python3/dist-packages/upk/"
cp VERSION "$TEMP_DIR/usr/lib/python3/dist-packages/upk/"

# Create wrapper script
print_status "Creating wrapper script..."
cat > "$TEMP_DIR/usr/bin/upk" << 'EOF'
#!/bin/bash
# UPK wrapper script
cd /usr/lib/python3/dist-packages/upk
exec python3 upk.py "$@"
EOF

chmod +x "$TEMP_DIR/usr/bin/upk"
print_success "Source files copied and wrapper script created"

# Create control file from template
print_status "Creating control file from template..."
cp "templates/DEBIAN/control" "$TEMP_DIR/DEBIAN/control"
# Replace VERSION_PLACEHOLDER with actual version
sed -i "s/VERSION_PLACEHOLDER/$VERSION/g" "$TEMP_DIR/DEBIAN/control"

# Create postinst script from template
print_status "Creating post-installation script from template..."
cp "templates/DEBIAN/postinst" "$TEMP_DIR/DEBIAN/postinst"
chmod 755 "$TEMP_DIR/DEBIAN/postinst"

# Create postrm script from template
print_status "Creating post-removal script from template..."
cp "templates/DEBIAN/postrm" "$TEMP_DIR/DEBIAN/postrm"
chmod 755 "$TEMP_DIR/DEBIAN/postrm"

# Create changelog from template
print_status "Creating changelog from template..."
cp "templates/usr/share/doc/upk/changelog.Debian" "$TEMP_DIR/usr/share/doc/upk/changelog.Debian"

# Create copyright file from template
print_status "Creating copyright file from template..."
cp "templates/usr/share/doc/upk/copyright" "$TEMP_DIR/usr/share/doc/upk/copyright"

# Create README from template
print_status "Creating README from template..."
cp "templates/usr/share/doc/upk/README.Debian" "$TEMP_DIR/usr/share/doc/upk/README.Debian"

# Set proper permissions
print_status "Setting proper permissions..."
find "$TEMP_DIR" -type d -exec chmod 755 {} \;
find "$TEMP_DIR" -type f -exec chmod 644 {} \;
chmod 755 "$TEMP_DIR/usr/bin/upk"
chmod 755 "$TEMP_DIR/DEBIAN/postinst"
chmod 755 "$TEMP_DIR/DEBIAN/postrm"

# Build the package
print_status "Building .deb package..."
HERE="$(pwd)"
cd "$TEMP_DIR"
DEB_FILE_NAME="upk-${VERSION}.deb"
dpkg-deb --build . $DEB_FILE_NAME

# Check if build was successful
if [ $? -eq 0 ]; then
    # Return to original directory and copy the built package
    cd $HERE
    DEB_FILE="$TEMP_DIR/$DEB_FILE_NAME"
    if [ -f "$DEB_FILE" ]; then
        cp "$DEB_FILE" "$HERE/"
        print_success "Package built successfully: $DEB_FILE_NAME"
        print_status "Size: $(ls -lh "$DEB_FILE_NAME" | awk '{print $5}')"
        
        # Show package contents
        print_status "Package contents:"
        dpkg-deb --contents "$DEB_FILE_NAME" | head -20
        
        print_success "Build process completed successfully!"
        print_status "To install the package, run: sudo dpkg -i $DEB_FILE_NAME"
    else
        print_error "Error: No .deb file found in $TEMP_DIR"
        print_error "Checking what files exist in temp directory:"
        ls -la "$TEMP_DIR"
        print_error "Checking current directory for .deb files:"
        ls -la *.deb 2>/dev/null || echo "No .deb files found in current directory"
        print_error "Checking if dpkg-deb actually created the file:"
        ls -la "$TEMP_DIR.deb" 2>/dev/null || echo "File not found at expected location"
        print_error "Checking if the file exists but with different permissions:"
        find "$TEMP_DIR" -name "*.deb" -type f 2>/dev/null || echo "No .deb files found in temp directory"
        exit 1
    fi
else
    print_error "Package build failed"
    exit 1
fi

# Clean up
print_status "Cleaning up temporary files..."
rm -rf "$TEMP_DIR"

print_success "UPK .deb package build completed!"