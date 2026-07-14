# Stable mount for Media drive (avoid media1 on reboot)

The Media NTFS drive can end up as `/media/mediaserver/media1` after reboot. To always mount it at **/media/mediaserver/media** (so your `.env` paths for TV shows and movies work), use a fixed `/etc/fstab` entry.

## 1. Unmount the current mount (if it’s mounted as media1)

```bash
sudo umount /media/mediaserver/media1
```

(Close any open files/folders on that drive first.)

## 2. Create the mount point

```bash
sudo mkdir -p /media/mediaserver/media
```

## 3. Add this line to `/etc/fstab`

Edit as root:

```bash
sudo nano /etc/fstab
```

Append this line (single line):

```
UUID=407FF70E6FB4077C /media/mediaserver/media ntfs-3g defaults,nofail,uid=1000,gid=1000,umask=022 0 0
```

- **nofail**: boot continues if the drive is unplugged.
- **uid=1000,gid=1000**: makes files owned by user `mediaserver`.

Save and exit (Ctrl+O, Enter, Ctrl+X).

## 4. Mount it

```bash
sudo mount /media/mediaserver/media
```

Check:

```bash
ls /media/mediaserver/media
mount | grep media/mediaserver/media
```

## 5. (Optional) Reduce automount conflicts

If your desktop (e.g. GNOME Disks) still mounts the same drive elsewhere after reboot:

- Open **Disks**, select the Media drive, click the gear → **Mount Options**.
- Turn off **Mount at startup** and/or **Show in user interface** so only `/etc/fstab` controls this mount.

## 6. Reboot test

```bash
sudo reboot
```

After reboot, the drive should be at `/media/mediaserver/media` and your media stack (using `TV_SHOWS_PATH` and `MOVIES_PATH` from `compose_files/.env`) will find it.
