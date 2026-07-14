# Stable mount for Samsung drive (avoid SAMSUNG1 on reboot)

The Samsung NTFS drive can end up as `/media/mediaserver/SAMSUNG1` after reboot. To always mount it at **/media/mediaserver/SAMSUNG** (so your `.env` paths work), use a fixed `/etc/fstab` entry.

## 1. Unmount the current mount (if it’s mounted as SAMSUNG1)

```bash
sudo umount /media/mediaserver/SAMSUNG1
```

(Close any open files/folders on that drive first.)

## 2. Create the mount point

```bash
sudo mkdir -p /media/mediaserver/SAMSUNG
```

## 3. Add this line to `/etc/fstab`

Edit as root:

```bash
sudo nano /etc/fstab
```

Append this line (single line):

```
UUID=6666605B66602DCD /media/mediaserver/SAMSUNG ntfs-3g defaults,nofail,uid=1000,gid=1000,umask=022 0 0
```

- **nofail**: boot continues if the drive is unplugged.
- **uid=1000,gid=1000**: makes files owned by user `mediaserver`.

Save and exit (Ctrl+O, Enter, Ctrl+X).

## 4. Mount it

```bash
sudo mount /media/mediaserver/SAMSUNG
```

Check:

```bash
ls /media/mediaserver/SAMSUNG
mount | grep SAMSUNG
```

## 5. (Optional) Reduce automount conflicts

If your desktop (e.g. GNOME Disks) still mounts the same drive elsewhere after reboot:

- Open **Disks**, select the Samsung drive, click the gear → **Mount Options**.
- Turn off **Mount at startup** and/or **Show in user interface** so only `/etc/fstab` controls this mount.

## 6. Reboot test

```bash
sudo reboot
```

After reboot, the drive should be at `/media/mediaserver/SAMSUNG` and your media stack (using paths from `compose_files/.env`) will find it.
