safe_umount() {
  umount -f smb_tmp
  rm -rf smb_tmp
}
trap "safe_umount" ERR
mkdir -p smb_tmp
mount_smbfs //datasci@prod-techcom-web01/websites/www2.microstrategy.com/producthelp smb_tmp/
echo 'Remote disk mounted. Uploading data'
git rev-parse HEAD > build/git_hash.txt
cp -r build/* smb_tmp/Current/mstrio-py/
cp -r build/* smb_tmp/2020/mstrio-py/
echo 'Upload finished. Unmounting disk'
safe_umount