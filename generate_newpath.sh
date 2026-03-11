#!/bin/bash

OLD_TAR=$1
NEW_TAR=$2

if [ -z "$OLD_TAR" ] || [ -z "$NEW_TAR" ]; then
    echo "Usage: $0 old_version.tar new_version.tar"
    exit 1
fi

WORKDIR=$(mktemp -d)

OLD_DIR=$WORKDIR/old
NEW_DIR=$WORKDIR/new
PATCH_DIR=$WORKDIR/patch

mkdir $OLD_DIR $NEW_DIR $PATCH_DIR

echo "Extracting tar files..."

tar -xf $OLD_TAR -C $OLD_DIR
tar -xf $NEW_TAR -C $NEW_DIR

echo "Finding changed files..."

rsync -rcn --out-format="%n" $OLD_DIR/ $NEW_DIR/ > $WORKDIR/changed_files.txt

mkdir -p $PATCH_DIR/files

while read file
do
    if [ -f "$NEW_DIR/$file" ]; then
        mkdir -p "$PATCH_DIR/files/$(dirname $file)"
        cp "$NEW_DIR/$file" "$PATCH_DIR/files/$file"
    fi
done < $WORKDIR/changed_files.txt

echo "Finding deleted files..."

cd $OLD_DIR
find . -type f | sed 's|^\./||' | sort > $WORKDIR/old_files.txt
cd - >/dev/null

cd $NEW_DIR
find . -type f | sed 's|^\./||' | sort > $WORKDIR/new_files.txt
cd - >/dev/null

comm -23 $WORKDIR/old_files.txt $WORKDIR/new_files.txt > $PATCH_DIR/delete_list.txt

echo "Creating install script..."

cat <<EOF > $PATCH_DIR/install_patch.sh
#!/bin/bash

INSTALL_DIR=\${1:-.}

echo "Removing deleted files..."

if [ -f delete_list.txt ]; then
    while read file
    do
        rm -f "\$INSTALL_DIR/\$file"
    done < delete_list.txt
fi

echo "Applying patch files..."

tar -xf patch_files.tar -C "\$INSTALL_DIR"

echo "Patch applied successfully"
EOF

chmod +x $PATCH_DIR/install_patch.sh

cho "Packaging patch..."

if [ -d "$PATCH_DIR/files" ] && [ "$(ls -A $PATCH_DIR/files)" ]; then
    tar -cf $PATCH_DIR/patch_files.tar -C $PATCH_DIR/files .
else
    tar -cf $PATCH_DIR/patch_files.tar --files-from /dev/null
fi

rm -rf $PATCH_DIR/files

cd $PATCH_DIR
tar -cf patch.tar patch_files.tar delete_list.txt install_patch.sh
cd - >/dev/null

cp $PATCH_DIR/patch.tar "$OLDPWD"

echo "Patch created: $OLDPWD/patch.tar"

echo "Patch created: patch.tar"

echo "Cleaning temporary files..."
rm -rf $WORKDIR
