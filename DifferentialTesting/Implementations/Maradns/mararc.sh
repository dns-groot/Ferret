ipaddr=\"$(hostname -i)\"
echo "ipv4_bind_addresses = $ipaddr"
echo 'chroot_dir = "/etc/maradns"'
echo 'csv2 = {}'
echo 'csv2["campus.edu."] = "db.campus.edu.csv2"'