# **All-jellyfin-media-server**

<div style="text-align: center">
    <img src="image/Isyrr.png" style="margin: 15px 10px;">
</div>


Welcome to the All-jellyfin-media-server Repository! This repository contains everything you need to create your own Jellyfin media server with Sonarr, Radarr, Jellyseerr, Prowlarr, Jackett, qBittorrent, and Gluetun (VPN) in a Docker Compose setup. We'll refer to the compilation of all containers as **Isyrr** to keep it simple.

![](https://img.shields.io/github/stars/Morzomb/All-jellyfin-media-server.svg)
![](https://img.shields.io/github/forks/Morzomb/All-jellyfin-media-server.svg)
![](https://img.shields.io/github/release/Morzomb/All-jellyfin-media-server.svg) 
![](https://img.shields.io/github/issues/Morzomb/All-jellyfin-media-server.svg)
[![GitHub last commit](https://img.shields.io/github/last-commit/Morzomb/All-jellyfin-media-server.svg)](https://github.com/Morzomb/All-jellyfin-media-server/commits/master)
![GitHub repo size](https://img.shields.io/github/repo-size/Morzomb/All-jellyfin-media-server)
![visitors](https://visitor-badge.laobi.icu/badge?page_id=Morzomb.All-jellyfin-media-server.id)

## **Table of contents**

- [**All-jellyfin-media-server**](#all-jellyfin-media-server)
  - [**Table of contents**](#table-of-contents)
  - [**What is Isyrr for?**](#what-is-isyrr-for)
  - [**Services Overview**](#services-overview)
- [**Prerequisites**](#prerequisites)
  - [**Docker**](#docker)
    - [**Using Docker Compose :**](#using-docker-compose-)
  - [**VPN**](#vpn)
  - [**Troubleshoot VPN**](#troubleshoot-vpn)
- [**Installation**](#installation)
  - [**1. Storage  Configuration**](#storage-configuration)
  - [**3. Steps**](#steps)
- [**Accessing Applications**](#accessing-applications)
- [**Configuration Guide for Web Interfaces Only**](#configuration-guide-for-web-interfaces-only)
  - [**qBittorrent**](#qbittorrent-1)
    - [**Category Configuration**](#category-configuration)
  - [**Radarr**](#radarr-1)
    - [**Media Management**](#media-management)
    - [**Download Clients**](#download-clients)
  - [**Sonarr**](#sonarr-1)
    - [**Media Management**](#media-management-1)
    - [**Download Clients**](#download-clients-1)
  - [**Prowlarr**](#prowlarr-1)
    - [**Configure Torrent Indexers**](#configure-torrent-indexers)
    - [**Configure FlareSolverr**](#configure-flaresolverr)
    - [**Configure Radarr**](#configure-radarr)
    - [**Configure Sonarr**](#configure-sonarr)
  - [**Jellyfin**](#jellyfin-1)
    - [**Initial Setup**](#initial-setup)
    - [**Adding Users to Jellyfin**](#adding-users-to-jellyfin)
  - [**Jellyseerr**](#jellyseerr-1)
    - [**Sign In / Configuration**](#sign-in--configuration)
    - [**Integrating with Radarr**](#integrating-with-radarr)
    - [**Integrating with Sonarr**](#integrating-with-sonarr)
- [**Updating Applications**](#updating-applications)
- [**Disclaimer**](#disclaimer)

## **What is Isyrr for?**

This repository allows you to create your own Jellyfin media server with all the necessary tools to manage your movies, TV shows, music, and eBooks. It also includes tools to automate the downloading of new content and to protect your privacy using a VPN.

Isyrr uses Docker and Docker Compose to deploy the services. Docker Compose files can be found in the directories with-vpn and without-vpn.

> [!IMPORTANT]  
> To use Docker Compose, make sure Docker is installed on your system.

---

## **Services Overview**

| Service | Description |
|---------|-------------|
| **[Jellyfin](https://jellyfin.org/)** | Open-source media server software that allows you to stream your movies, TV shows, music, and eBooks to all your devices. Compatible with many types of media files and supports streaming to numerous devices. |
| **[Jellyseerr](https://github.com/Fallenbagel/jellyseerr)** | Open-source application that automates the management of your Jellyfin media server. Monitors your Jellyfin library and automatically searches for and downloads new content based on your preferences. Integrates with Sonarr and Radarr for seamless media management. |
| **[Sonarr](https://sonarr.tv/)** | TV show management software that allows you to search, download, and manage your favorite TV shows automatically. Works with many types of trackers and torrent clients and supports automatic subtitle downloading. |
| **[Radarr](https://radarr.video/)** | Movie management software that allows you to search, download, and manage your favorite movies automatically. Works with many types of trackers and torrent clients and supports automatic subtitle downloading. |
| **[Jackett](https://github.com/Jackett/Jackett)** | Proxy software for torrent trackers that allows you to search for torrent files on many trackers from one place. Works with many types of torrent clients and supports authentication and advanced searching. |
| **[Flaresolverr](https://github.com/FlareSolverr/FlareSolverr)** | Open-source software that allows you to bypass streaming restrictions on video-sharing sites. Resolves streaming links and bypasses geographical blocks and playback restrictions. |
| **[Prowlarr](https://github.com/Prowlarr/Prowlarr)** | Download management software that allows you to search for and automatically download files from many types of sources, including torrent trackers, newsgroups, and direct download sites. |
| **[qBittorrent](https://www.qbittorrent.org/)** | Open-source BitTorrent client software that allows you to download torrent files. Lightweight, easy to use, and supports many advanced features such as built-in torrent search, encryption, torrent creation, and support for private trackers. |
| **[Gluetun (VPN)](https://github.com/qdm12/gluetun)** | Open-source VPN client software that allows you to connect to VPN servers. Easy to use and supports many advanced features such as port forwarding, DNS leak protection, and support for multiple VPN protocols. |

---

# **Prerequisites**

> [!NOTE]  
> This service requires a machine with at least 4 CPU cores and 8 GB of RAM. It is also highly recommended to have an NVIDIA GPU for optimal performance.

Première chose à faire mettre à jour votre systèmes :

```bash
sudo apt update && sudo apt upgrade
```

## **Docker**

To install Docker on your system, use the following commands:

Download the script with this command:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
```

Then run the script with this command:
```bash
sh get-docker.sh
```

> [!TIP]
> I recommend giving Docker administrative rights to your user:
> ```bash
> usermod -aG docker <user>
> ```
> After this command, disconnect and reconnect.


### **Using Docker Compose :**

To use Docker Compose with this repository, you first need to choose whether you want to use the version with VPN or without VPN. Then, navigate to the corresponding directory (with-vpn or without-vpn) and run the following command :

```bash
docker-compose up -d
```
To shut down the stack :

```bash
docker-compose down
```

**[`^        back to top        ^`](#table-of-contents)**

# **VPN**

Personally, I use Surfshark VPN, but you can find a number of other VPN providers as well. The instructions for all the providers are [HERE](https://github.com/qdm12/gluetun-wiki/tree/main/setup/providers). Follow those instructions to setup and customize.
If you are using Surfshark you need to follow the isntructions there and look at the env file to see what environment variables you need.

## **Troubleshoot VPN** 

Once the Docker is launched, you can test your VPN with the following command :

```bash
docker exec qbittorrent curl -s https://api.ipify.org/
# Result
94.101.115.63
```

On my side, it shows me an IP address in Belgium :

<div style="text-align: center">
    <img src="image/vpn/vpn4.png" style="margin: 15px 10px;">
</div>

**[`^        back to top        ^`](#table-of-contents)**

---

# **Installation**
## **Storage Configuration**

This setup uses a **separated storage approach** for better performance and organization. You'll need to configure the paths directly in the `docker-compose.yaml` file according to your system setup.

### **Recommended Directory Structure**
```
/home/mediaserver/configs/          # Service configurations
├── qbittorrent/
├── sonarr/
├── radarr/
├── jellyfin/
├── jellyseerr/
└── prowlarr/

/home/mediaserver/downloads/        # qBittorrent downloads (fast local storage)
├── radarr/                         # Movie downloads
├── sonarr/                         # TV show downloads  
└── completed/                      # Completed downloads

/mnt/external-drive/media/          # External drive for media
├── movies/                         # Movie files
└── tv-shows/                      # TV show files

/mnt/external-drive/audio/         # External drive for audio
└── music/                         # Music files

/mnt/external-drive/books/          # External drive for books
└── ebooks/                        # E-book files
```

> [!TIP]
> This setup allows downloads to happen on fast local storage first, then you can move/organize them to external drives later using Sonarr/Radarr's file management features.

## **Steps**


1. **Clone the repository**

```bash
git clone https://github.com/s-ashwinkumar/media-server.git
cd media-server/
```

2. **Configure Environment Variables**
Before proceeding, navigate to the `.env` file located in the `compose_files/` directory and complete it with the required information. This file must always be at the root of the `docker-compose` file you are going to launch.

```bash
cp compose_files/.env.example compose_files/.env
```

> [!WARNING]  
> Make sure you configure your Surfshark VPN credentials in the `.env` file. This step is essential for establishing a proper VPN connection for secure downloads.

3. **Configure Storage Paths**
Edit the `docker-compose.yaml` file to set your storage paths according to your system setup. Update the volume mounts for each service to point to your desired directories.

4. **Start the Media Server**
   ```bash
   cd compose_files/
   docker compose up -d
   ```

5. **Access the Services**
   - **qBittorrent**: http://localhost:8080
   - **Sonarr**: http://localhost:8989
   - **Radarr**: http://localhost:7878
   - **Jellyfin**: http://localhost:8096
   - **Jellyseerr**: http://localhost:5055
   - **Prowlarr**: http://localhost:9696
   - **Jackett**: http://localhost:9117

**[`^        back to top        ^`](#table-of-contents)**

# **Accessing Applications**

Once the applications are deployed, you can access them using the following addresses :

> [!IMPORTANT]  
> Replace `localhost` with the IP address of your machine or remote server if needed.


* Jellyfin : http://localhost:8096
* Jellyseer : http://localhost:5055
* Sonarr : http://localhost:8989
* Radarr : http://localhost:7878
* Jackett : http://localhost:9117
* Prowlarr : http://localhost:9696
* qBittorrent : http://localhost:8080

Gluetun (Surfshark VPN) will be automatically configured to be used with the applications.

# **Configuration Guide for Web Interfaces Only**

> [!IMPORTANT]  
> All links containing the container name can be replaced with either the server IP or `localhost`. Use the paths you configured in your `docker-compose.yaml` file for volume mounts.


## **qBittorrent**

1. Open the WebUI by clicking on the application icon in the **DOCKER** tab and selecting **WebUI**.
2. Log in with the default credentials:
   - **Username**: `admin`
   - **Password**: `adminadmin`
   
<div style="text-align: center">
    <img src="image/qBittorrent/qbit1.png" style="margin: 15px 10px;">
</div>

   *Note: The default credentials may have changed, please check the documentation for updates on this. In most cases, qBittorrent Web UI will generate a temporary password when the container is started. To view this password, check the logs for this container with the command: `docker logs qbittorrent`*

1. Once logged in, click the gear icon to go to **Options**.
2. Under the **Downloads** tab, configure the backup settings as follows:
   - **Default Torrent Management Mode**: `Automatic` (required for category-based save paths to work)
   - **When Torrent Category changed**: `Relocate torrent`
   - **When Default Save Path changed**: `Relocate affected torrents`
   - **When Category Save Path changed**: `Relocate affected torrents`
   - **Default Save Path**: `/downloads` 
3. Click **SAVE**.

<div style="text-align: center">
    <img src="image/qBittorrent/qbit2.png" style="margin: 15px 10px;">
</div>

### **Category Configuration**

1. In the WebUI, expand **CATEGORIES** in the left menu. Right-click on **All** and select **Add category...**.
2. In the **New Category** window, configure as follows:
   - **Category**: `radarr` (this corresponds to the category you will later configure in Radarr)
   - **Save path**: `/downloads/radarr`
3. Click **Add**.
4. Right-click on **All** again, select **Add category...**.
5. Configure as follows:
   - **Category**: `sonarr` (this should match the category configured later in Sonarr, by default `sonarr-tv`, but this guide uses `sonarr`)
   - **Save path**: `/downloads/sonarr`
6. Click **Add**.

<div style="text-align: center">
    <img src="image/qBittorrent/qbit3.png" style="margin: 15px 10px;">
</div>

<div style="text-align: center">
    <img src="image/qBittorrent/qbit4.png" style="margin: 15px 10px;">
    <img src="image/qBittorrent/qbit5.png" style="margin: 15px 10px;">
</div>

**[`^        back to top        ^`](#table-of-contents)**

---

## **Radarr**

### **Media Management**

1. Open the WebUI and go to **Settings** > **Media Management**.
2. Click **Add Root Folder**, add the path `/movies` (or your configured movies path), and click **OK**.
3. Click **Show Advanced** at the top, scroll down to **Importing**, and make sure **Use Hardlinks instead of Copy** is enabled.

<div style="text-align: center">
    <img src="image/radarr/rad3.png" style="margin: 15px 10px;">
</div>

### **Download Clients**

1. In the WebUI, go to **Settings** > **Download Clients**.
2. Click **+** under **Download Clients**, then select **qBittorrent** from the **Add Download Client** window.
3. Fill in the fields as follows:
   - **Name**: `qBittorrent` (or another name of your choice)
   - **Host**: `qbittorrent`
   - **Username**: `admin`
   - **Password**: `adminadmin` (change it if you've modified it in qBittorrent)
   - **Category**: `radarr` (this should match the category set in qBittorrent)
4. Click **Test**. If you see a checkmark, it means the connection is working; if not, there is an error.
5. Click **Save**.

<div style="text-align: center">
    <img src="image/radarr/rad5.png" style="margin: 15px 10px;">
</div>

_Note: if entering `qbittorrent` as the Host does not work, try entering the IP address instead (ex: `192.168.x.x`)_

> [!WARNING]
> On new installations, Radarr may complain that the `/downloads/radarr` directory does not exist inside the container (this is generally flagged as an error by Radarr in  **System** > **Status**). To fix this, simply move into your downloads directory and manually create the `radarr` directory. Then, simply delete qBittorrent from Radarr and re-add it -  you should see the error disappear.

### **Indexer Jackett (Optional)**

1. In the WebUI, go to **Settings** > **Indexers**.
2. Click **+** under **Add Indexer**, then select **Torznab**.
3. Fill in the fields as follows:
   - **Name**: `Torznab` (or another name of your choice)
   - **URL**: `http://Jackett:9117/api/v2.0/indexers/YOUR_INDEXERS/results/torznab/`
   - **ApiKey**: Find the API key in the home menu at the top right.
4. Click **Test**. If you see a checkmark, it means the connection is working; if not, there is an error.
5. Click **Save**.

<div style="text-align: center">
    <img src="image/sonarr/son3.png" style="margin: 15px 10px;">
</div>

**[`^        back to top        ^`](#table-of-contents)**

---

## **Sonarr**

### **Media Management**

1. Open the WebUI and go to **Settings** > **Media Management**.
2. Click **Add Root Folder**, add the path `/tv-shows` (or your configured TV shows path), and click **OK**.
3. Click **Show Advanced**, scroll down to **Importing**, and enable **Use Hardlinks instead of Copy**.

<div style="text-align: center">
    <img src="image/sonarr/son1.png" style="margin: 15px 10px;">
</div>

_Note: if entering `qbittorrent` as the Host does not work, try entering the IP address instead (ex: `192.168.x.x`)_

### **Download Clients**

1. In the WebUI, go to **Settings** > **Download Clients**.
2. Click **+** under **Download Clients**, then select **qBittorrent**.
3. Fill in the fields as follows:
   - **Name**: `qBittorrent` (or another name of your choice)
   - **Host**: `qbittorrent`
   - **Username**: `admin`
   - **Password**: `adminadmin` (change it if you've modified it in qBittorrent)
   - **Category**: `sonarr` (this should match the category set in qBittorrent)
4. Click **Test**. If you see a checkmark, it means the connection is working.
5. Click **Save**.

<div style="text-align: center">
    <img src="image/sonarr/son2.png" style="margin: 15px 10px;">
</div>

### **Indexer Jackett (Optional)**

1. In the WebUI, go to **Settings** > **Indexers**.
2. Click **+** under **Add Indexer**, then select **Torznab**.
3. Fill in the fields as follows:
   - **Name**: `Torznab` (or another name of your choice)
   - **URL**: `http://Jackett:9117/api/v2.0/indexers/YOUR_INDEXERS/results/torznab/`
   - **ApiKey**: Find the API key in the home menu at the top right.
4. Click **Test**. If you see a checkmark, it means the connection is working; if not, there is an error.
5. Click **Save**.

<div style="text-align: center">
    <img src="image/sonarr/son3.png" style="margin: 15px 10px;">
</div>

**[`^        back to top        ^`](#table-of-contents)**

---

## **Prowlarr**

### **Configure Torrent Indexers**

1. Open the WebUI and go to **Indexers** > **Add New Indexer**.
2. Select **1337x** (or another tracker of your choice).
   - You can modify the settings as per your preference, but the default values generally work well.
   - Sorting by **Seeders** can be useful for faster downloads.
3. Click **Test**. If you see a checkmark, the connection is functional; otherwise, there's an error.
4. Click **Save**.

### **Configure FlareSolverr**

1. Go to **Settings** and click **+** under **Indexer**.
2. Select **FlareSolverr** and fill in the information as follows:
   - **Name**: `FlareSolverr`
   - **Tags**: `flaresolverr`
   - **Host**: `http://flaresolverr:8191/`
3. Click **Test** to check the connection.
4. Click **Save**.

<div style="text-align: center">
    <img src="image/prowlarr/pro1.png" style="margin: 15px 10px;">
</div>

### **Configure Radarr**

1. Go to **Settings** and click **Apps**.
2. Select **Radarr** and fill in the information as follows:
   - **Sync Level**: `Full Sync`
   - **Prowlarr Server**: `http://prowlarr:9696`
   - **Radarr Server**: `http://radarr:7878`
   - **ApiKey**: Find the API key in the Radarr interface under **Settings** > **General** > **API Key**.
3. Click **Test** to check the connection.
4. Click **Save**.

<div style="text-align: center">
    <img src="image/prowlarr/pro2.png" style="margin: 15px 10px;">
</div>

### **Configure Sonarr**

1. Go to **Settings** and click **Apps**.
2. Select **Sonarr** and fill in the information as follows:
   - **Sync Level**: `Full Sync`
   - **Prowlarr Server**: `http://prowlarr:9696`
   - **Sonarr Server**: `http://sonarr:8989`
   - **ApiKey**: Find the API key in the Sonarr interface under **Settings** > **General** > **API Key**.
3. Click **Test** to check the connection.
4. Click **Save**.

<div style="text-align: center">
    <img src="image/prowlarr/pro3.png" style="margin: 15px 10px;">
</div>

**[`^        back to top        ^`](#table-of-contents)**

---

## **Jellyfin**

### **Initial Setup**

1. Open the Web UI by going to the **DOCKER** tab, click the app logo for Jellyfin, and select **WebUI**.
2. Select a preferred display language (or use the default English). Click **Next** ➝.
3. Create an administrator account, fill out the credentials as desired, and click **Next** ➝.
4. Click **Add Media Library** and fill in the following:
   - **Content type**: Movies
   - **Folders**: `/movies` (or your configured movies path)
   - Configure the rest as you see fit; the default settings are typically fine.
5. Click **OK**.
6. Click **Add Media Library** again and fill in the following:
   - **Content type**: Shows
   - **Folders**: `/tv-shows` (or your configured TV shows path)
   - Configure the rest as you see fit; the default settings are typically fine.
7. Click **OK**.
8. Click **Next** ➝.
9. Configure the **Preferred Metadata Language** (or use the default), and click **Next** ➝.
10. In **Configure Remote Access**, leave **Allow Remote Connections to this Server** checked and **Enable Automatic Port Mapping** unchecked.
11. Click **Next** ➝, then click **Finish**.
12. Sign in with your administrator account.

Once you sign in, if you already have media in your configured media folders (/movies, /tv-shows, etc.), it should start appearing in Jellyfin. If not, the content will populate as the folders are filled.

### **Adding Users to Jellyfin**

If you want other users to access your Jellyfin server, you can create additional user accounts. This step is optional if you're the only user.

1. Open the left menu by clicking on the three horizontal lines (hamburger menu) in the upper left corner.
2. Select **Users** and click the **+** button on the left to add a new user.
3. Fill in the following details for the new user:
   - **Name**: `<username>`
   - **Password**: `<password>`
   - Under **Library Access**, check the boxes for the libraries (Movies, TV shows, etc.) that you want the user to have access to.
4. Click **Save** to create the user.
5. Repeat this process for all users you wish to add to the server.

**[`^        back to top        ^`](#table-of-contents)**

---

## **Jellyseerr**

### **Sign In / Configuration**

1. Open the WebUI and in the **Welcome to Jellyseerr** screen, select **Use your Jellyfin account**.
2. Fill in the information as follows:
   - **Jellyfin URL**: `http://jellyfin:8096/`
   - **Email Address**: `<your email address>`
   - **Username**: `<your Jellyfin username>`
   - **Password**: `<your Jellyfin password>`
3. Select **Sign In**.
4. Go to **Sync Libraries** under **Jellyfin Libraries**, select your Jellyfin libraries, then click **Continue**.

### **Integrating with Radarr**

1. Go to **Radarr Settings**, then click **Add Radarr Server**.
2. Fill in the information as follows:
   - **Default Server**: Check this box
   - **Server Name**: `Radarr`
   - **Name or IP Address**: `http://radarr`
   - **Port**: `7878`
   - **API Key**: Find the API key in the Radarr interface under **Settings** > **General** > **API Key**.
3. Click **Test** to check the connection.
4. Click **Save Changes**.

### **Integrating with Sonarr**

1. Go to **Sonarr Settings**, then click **Add Sonarr Server**.
2. Fill in the information as follows:
   - **Default Server**: Check this box
   - **Server Name**: `Sonarr`
   - **Name or IP Address**: `http://sonarr`
   - **Port**: `8989`
   - **API Key**: Find the API key in the Sonarr interface under **Settings** > **General** > **API Key**.
3. Click **Test** to check the connection.
4. Click **Save Changes**.

**[`^        back to top        ^`](#table-of-contents)**

---

# **Updating Applications**

To update the applications, you need to stop the running containers and remove the existing Docker images. You can use the following commands to perform these operations:

```bash
docker-compose down
docker image prune -a
```

Then, you can run `docker-compose up -d` to restart the containers with the latest versions of the applications.

**[`^        back to top        ^`](#table-of-contents)**

# **Disclaimer**

This code is provided for informational purposes only and should not be used for illegal activities. I am not responsible for the actions performed by users of this code. This code is for informational purposes, and if people wish to use it, they should consult the laws of their countries.
