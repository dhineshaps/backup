#!/bin/bash

OLD_DIR=$1
NEW_DIR=$2
PATCH_DIR=patch

if [ -z "$OLD_DIR" ] || [ -z "$NEW_DIR" ]; then
    echo "Usage: $0 <old_release_dir> <new_release_dir>"
    exit 1
fi

echo "Cleaning old patch directory..."
rm -rf $PATCH_DIR
mkdir -p $PATCH_DIR/files

echo "Finding changed and new files..."

rsync -rcn --out-format="%n" $OLD_DIR/ $NEW_DIR/ > /tmp/changed_files.txt

while read file
do
    if [ -f "$NEW_DIR/$file" ]; then
        mkdir -p "$PATCH_DIR/files/$(dirname $file)"
        cp "$NEW_DIR/$file" "$PATCH_DIR/files/$file"
    fi
done < /tmp/changed_files.txt

echo "Finding deleted files..."

cd $OLD_DIR
find . -type f | sed 's|^\./||' | sort > /tmp/old_files.txt
cd - > /dev/null

cd $NEW_DIR
find . -type f | sed 's|^\./||' | sort > /tmp/new_files.txt
cd - > /dev/null

comm -23 /tmp/old_files.txt /tmp/new_files.txt > $PATCH_DIR/delete_list.txt

echo "Creating install script..."

cat <<EOF > $PATCH_DIR/install_patch.sh
#!/bin/bash

INSTALL_DIR=\${1:-.}

echo "Deleting removed files..."

if [ -f delete_list.txt ]; then
    while read file
    do
        rm -f "\$INSTALL_DIR/\$file"
    done < delete_list.txt
fi

echo "Applying patch..."

tar -xf patch_files.tar -C "\$INSTALL_DIR"

echo "Patch applied successfully"
EOF

chmod +x $PATCH_DIR/install_patch.sh

echo "Packaging patch..."

cd $PATCH_DIR
tar -cf patch_files.tar files
rm -rf files
tar -cf patch.tar patch_files.tar delete_list.txt install_patch.sh
cd ..

echo "Patch created: $PATCH_DIR/patch.tar"
