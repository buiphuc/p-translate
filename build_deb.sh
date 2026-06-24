#!/bin/bash
# Script to build Debian package (.deb) for QTranslate Linux

set -e

APP_NAME="qtranslate-linux"
VERSION="1.0.0"
BUILD_DIR="build_deb_tmp"

echo "Building Debian package for $APP_NAME v$VERSION..."

# 1. Clean up old build files
rm -rf "$BUILD_DIR"
rm -f "${APP_NAME}.deb"

# 2. Create directory structure
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/share/$APP_NAME"
mkdir -p "$BUILD_DIR/usr/share/applications"

# 3. Create control file
cat << EOF > "$BUILD_DIR/DEBIAN/control"
Package: $APP_NAME
Version: $VERSION
Section: utils
Priority: optional
Architecture: all
Maintainer: Phuc Bui Minh <bui.phuc.vt@gmail.com>
Depends: python3, python3-pyqt6, xdotool, xclip
Description: A quick translation tool using global hotkey for Linux.
EOF

# 4. Create executable wrapper in /usr/bin
cat << 'EOF' > "$BUILD_DIR/usr/bin/$APP_NAME"
#!/bin/bash
exec /usr/share/qtranslate-linux/run.sh "$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/$APP_NAME"

# 5. Copy application source files
cp main.py "$BUILD_DIR/usr/share/$APP_NAME/"
cp ui.py "$BUILD_DIR/usr/share/$APP_NAME/"
cp settings_manager.py "$BUILD_DIR/usr/share/$APP_NAME/"
cp translator.py "$BUILD_DIR/usr/share/$APP_NAME/"
cp run.sh "$BUILD_DIR/usr/share/$APP_NAME/"
chmod 755 "$BUILD_DIR/usr/share/$APP_NAME/run.sh"

# 6. Create .desktop file
cat << EOF > "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=QTranslate Linux
Comment=Quick translation tool using hotkey
Exec=$APP_NAME
Icon=accessories-dictionary
Terminal=false
Categories=Utility;Translation;
EOF
chmod 644 "$BUILD_DIR/usr/share/applications/$APP_NAME.desktop"

# 7. Build package
dpkg-deb --build "$BUILD_DIR" "${APP_NAME}.deb"

# 8. Clean up
rm -rf "$BUILD_DIR"

echo "Debian package successfully built: ${APP_NAME}.deb"
